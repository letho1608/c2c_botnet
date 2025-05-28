#!/usr/bin/env python3
"""
Thread-Safe C2C Server Implementation
Comprehensive server implementation with thread safety, connection pooling, and security enhancements.
"""

import socket
import ssl
import json
import threading
import concurrent.futures
import logging
import os
import sys
import time
import signal
import atexit
import weakref
from datetime import datetime, timedelta
from contextlib import contextmanager
from typing import Dict, Any, Optional, List, Set
import queue
import hashlib
import secrets
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class ThreadSafeServer:
    """
    Thread-safe C2C server with comprehensive security and reliability features.
    
    Key Features:
    - Thread-safe client management
    - Connection pooling and resource management
    - SSL/TLS with auto-generated certificates
    - Background monitoring and cleanup
    - Graceful shutdown handling
    - Rate limiting and DOS protection
    - Comprehensive logging and statistics
    """
    
    def __init__(self, host='localhost', port=4444, max_clients=100):
        self.host = host
        self.port = port
        self.max_clients = max_clients
        self.running = False
        self.server_socket: Optional[socket.socket] = None
        
        # Thread safety infrastructure
        self._server_lock = threading.RLock()
        self._clients_lock = threading.RLock()
        self._shutdown_event = threading.Event()
        self._stats_lock = threading.Lock()
        
        # Client management
        self.clients: Dict[str, Dict] = {}  # client_id -> client_info
        self.active_operations = weakref.WeakSet()
        
        # Thread pools for different operations
        self.thread_pool = concurrent.futures.ThreadPoolExecutor(
            max_workers=32,
            thread_name_prefix="ClientHandler"
        )
        self.io_pool = concurrent.futures.ThreadPoolExecutor(
            max_workers=16,
            thread_name_prefix="IOHandler"
        )
        
        # SSL context
        self.ssl_context = None
        self.cert_file = "server_cert.pem"
        self.key_file = "server_key.pem"
        
        # Rate limiting
        self.connection_rates: Dict[str, List[float]] = {}
        self.rate_limit_window = 60  # seconds
        self.max_connections_per_minute = 30
        
        # Statistics
        self.stats = {
            'start_time': datetime.now(),
            'total_connections': 0,
            'active_connections': 0,
            'total_commands': 0,
            'failed_connections': 0,
            'rate_limited_ips': set()
        }
        
        # Background tasks
        self.cleanup_thread: Optional[threading.Thread] = None
        self.monitor_thread: Optional[threading.Thread] = None
        
        # Logger
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Initialize server
        self._initialize_server()
    
    def _initialize_server(self):
        """Initialize server with proper error handling"""
        try:
            # Setup SSL
            self._setup_ssl()
            
            # Setup emergency handlers
            self._setup_signal_handlers()
            
            # Start background tasks
            self._start_background_tasks()
            
            self.logger.info("Server initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Server initialization failed: {e}")
            self._safe_shutdown()
            raise
    
    def _setup_ssl(self):
        """Setup SSL context with auto-generated certificates"""
        try:
            # Create certificates if they don't exist
            if not os.path.exists(self.cert_file) or not os.path.exists(self.key_file):
                self._create_self_signed_cert()
            
            # Create SSL context
            self.ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            self.ssl_context.load_cert_chain(self.cert_file, self.key_file)
            
            # Security settings
            self.ssl_context.minimum_version = ssl.TLSVersion.TLSv1_2
            self.ssl_context.set_ciphers('ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20:!aNULL:!MD5:!DSS')
            
            self.logger.info("SSL context configured")
            
        except Exception as e:
            self.logger.error(f"SSL setup failed: {e}")
            raise
    
    def _create_self_signed_cert(self):
        """Create self-signed SSL certificate"""
        try:
            from cryptography import x509
            from cryptography.x509.oid import NameOID
            from cryptography.hazmat.primitives import hashes
            from cryptography.hazmat.primitives.asymmetric import rsa
            from cryptography.hazmat.primitives import serialization
            import ipaddress
            
            # Generate private key
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048,
            )
            
            # Create certificate
            subject = issuer = x509.Name([
                x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
                x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "CA"),
                x509.NameAttribute(NameOID.LOCALITY_NAME, "San Francisco"),
                x509.NameAttribute(NameOID.ORGANIZATION_NAME, "C2C Server"),
                x509.NameAttribute(NameOID.COMMON_NAME, "localhost"),
            ])
            
            cert = x509.CertificateBuilder().subject_name(
                subject
            ).issuer_name(
                issuer
            ).public_key(
                private_key.public_key()
            ).serial_number(
                x509.random_serial_number()
            ).not_valid_before(
                datetime.utcnow()
            ).not_valid_after(
                datetime.utcnow() + timedelta(days=365)
            ).add_extension(
                x509.SubjectAlternativeName([
                    x509.DNSName("localhost"),
                    x509.DNSName("127.0.0.1"),
                    x509.IPAddress(ipaddress.IPv4Address("127.0.0.1")),
                ]),
                critical=False,
            ).sign(private_key, hashes.SHA256())
            
            # Write certificate and key
            with open(self.cert_file, "wb") as f:
                f.write(cert.public_bytes(serialization.Encoding.PEM))
            
            with open(self.key_file, "wb") as f:
                f.write(private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption()
                ))
            
            self.logger.info("Self-signed certificate created")
            
        except ImportError:
            self.logger.warning("cryptography library not available, creating dummy cert")
            self._create_dummy_cert()
        except Exception as e:
            self.logger.error(f"Certificate creation failed: {e}")
            self._create_dummy_cert()
    
    def _create_dummy_cert(self):
        """Create dummy certificate files for testing"""
        # This is just for testing - in production, use proper certificates
        cert_content = """-----BEGIN CERTIFICATE-----
MIICpDCCAYwCAQAwDQYJKoZIhvcNAQELBQAwEjEQMA4GA1UEAwwHdGVzdC1jYTAe
Fw0yMzAxMDEwMDAwMDBaFw0yNDAxMDEwMDAwMDBaMBIxEDAOBgNVBAMMB3Rlc3Qt
Y2EwggEiMA0GCSqGSIb3DQEBAQUAA4IBDwAwggEKAoIBAQC7VJTUt9Us8cKBwko6
Example certificate content - DO NOT USE IN PRODUCTION
-----END CERTIFICATE-----"""
        
        key_content = """-----BEGIN PRIVATE KEY-----
MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC7VJTUt9Us8cKB
Example private key content - DO NOT USE IN PRODUCTION
-----END PRIVATE KEY-----"""
        
        with open(self.cert_file, "w") as f:
            f.write(cert_content)
        
        with open(self.key_file, "w") as f:
            f.write(key_content)
    
    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        try:
            signal.signal(signal.SIGTERM, self._signal_handler)
            signal.signal(signal.SIGINT, self._signal_handler)
            atexit.register(self._cleanup_on_exit)
            
            self.logger.info("Signal handlers registered")
            
        except Exception as e:
            self.logger.error(f"Signal handler setup failed: {e}")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.logger.info(f"Received signal {signum}, initiating shutdown")
        self._shutdown_event.set()
        self._safe_shutdown()
    
    def _cleanup_on_exit(self):
        """Cleanup on exit"""
        self._safe_shutdown()
    
    def _start_background_tasks(self):
        """Start background monitoring and cleanup tasks"""
        self.cleanup_thread = threading.Thread(
            target=self._cleanup_task,
            name="CleanupThread",
            daemon=True
        )
        self.cleanup_thread.start()
        
        self.monitor_thread = threading.Thread(
            target=self._monitor_task,
            name="MonitorThread",
            daemon=True
        )
        self.monitor_thread.start()
        
        self.logger.info("Background tasks started")
    
    def _cleanup_task(self):
        """Background cleanup task"""
        while not self._shutdown_event.is_set():
            try:
                self._cleanup_dead_clients()
                self._cleanup_rate_limiting()
                time.sleep(30)  # Run every 30 seconds
            except Exception as e:
                self.logger.error(f"Cleanup task error: {e}")
    
    def _monitor_task(self):
        """Background monitoring task"""
        while not self._shutdown_event.is_set():
            try:
                self._log_statistics()
                self._check_client_timeouts()
                time.sleep(60)  # Run every minute
            except Exception as e:
                self.logger.error(f"Monitor task error: {e}")
    
    def _cleanup_dead_clients(self):
        """Remove dead/disconnected clients"""
        with self._clients_lock:
            dead_clients = []
            
            for client_id, client_info in self.clients.items():
                if client_info.get('socket'):
                    try:
                        # Send keepalive
                        client_info['socket'].send(b'\x00')
                    except:
                        dead_clients.append(client_id)
                else:
                    dead_clients.append(client_id)
            
            for client_id in dead_clients:
                self._remove_client(client_id)
    
    def _cleanup_rate_limiting(self):
        """Clean up old rate limiting entries"""
        current_time = time.time()
        cutoff_time = current_time - self.rate_limit_window
        
        for ip in list(self.connection_rates.keys()):
            # Remove old timestamps
            self.connection_rates[ip] = [
                timestamp for timestamp in self.connection_rates[ip]
                if timestamp > cutoff_time
            ]
            
            # Remove empty entries
            if not self.connection_rates[ip]:
                del self.connection_rates[ip]
    
    def _log_statistics(self):
        """Log server statistics"""
        with self._stats_lock:
            uptime = datetime.now() - self.stats['start_time']
            self.logger.info(
                f"Stats - Uptime: {uptime}, "
                f"Total connections: {self.stats['total_connections']}, "
                f"Active: {self.stats['active_connections']}, "
                f"Commands: {self.stats['total_commands']}, "
                f"Failed: {self.stats['failed_connections']}"
            )
    
    def _check_client_timeouts(self):
        """Check for client timeouts"""
        current_time = time.time()
        timeout_threshold = 300  # 5 minutes
        
        with self._clients_lock:
            timeout_clients = []
            
            for client_id, client_info in self.clients.items():
                last_activity = client_info.get('last_activity', current_time)
                if current_time - last_activity > timeout_threshold:
                    timeout_clients.append(client_id)
            
            for client_id in timeout_clients:
                self.logger.info(f"Client {client_id} timed out")
                self._remove_client(client_id)
    
    def start(self):
        """Start the server"""
        with self._server_lock:
            if self.running:
                self.logger.warning("Server is already running")
                return
            
            try:
                # Create and bind socket
                self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                self.server_socket.bind((self.host, self.port))
                self.server_socket.listen(self.max_clients)
                
                self.running = True
                self.logger.info(f"Server started on {self.host}:{self.port}")
                
                # Accept connections
                self._accept_connections()
                
            except Exception as e:
                self.logger.error(f"Server start failed: {e}")
                self._safe_shutdown()
                raise
    
    def _accept_connections(self):
        """Accept incoming connections"""
        while self.running and not self._shutdown_event.is_set():
            try:
                # Accept connection with timeout
                self.server_socket.settimeout(1.0)
                client_socket, client_address = self.server_socket.accept()
                
                # Check rate limiting
                if not self._check_rate_limit(client_address[0]):
                    self.logger.warning(f"Rate limited connection from {client_address[0]}")
                    client_socket.close()
                    continue
                
                # Check max clients
                if len(self.clients) >= self.max_clients:
                    self.logger.warning(f"Max clients reached, rejecting {client_address}")
                    client_socket.close()
                    continue
                
                # Handle connection in thread pool
                self.thread_pool.submit(
                    self._handle_client_connection,
                    client_socket,
                    client_address
                )
                
                with self._stats_lock:
                    self.stats['total_connections'] += 1
                
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    self.logger.error(f"Accept connection error: {e}")
    
    def _check_rate_limit(self, ip_address: str) -> bool:
        """Check if IP address is rate limited"""
        current_time = time.time()
        
        if ip_address not in self.connection_rates:
            self.connection_rates[ip_address] = []
        
        # Remove old timestamps
        cutoff_time = current_time - self.rate_limit_window
        self.connection_rates[ip_address] = [
            timestamp for timestamp in self.connection_rates[ip_address]
            if timestamp > cutoff_time
        ]
        
        # Check rate limit
        if len(self.connection_rates[ip_address]) >= self.max_connections_per_minute:
            with self._stats_lock:
                self.stats['rate_limited_ips'].add(ip_address)
            return False
        
        # Add current timestamp
        self.connection_rates[ip_address].append(current_time)
        return True
    
    def _handle_client_connection(self, client_socket: socket.socket, client_address: tuple):
        """Handle individual client connection"""
        client_id = None
        ssl_socket = None
        
        try:
            # Wrap with SSL
            ssl_socket = self.ssl_context.wrap_socket(
                client_socket,
                server_side=True
            )
            ssl_socket.settimeout(30.0)
            
            # Generate client ID
            client_id = self._generate_client_id(client_address)
            
            # Register client
            self._register_client(client_id, ssl_socket, client_address)
            
            # Perform handshake
            if not self._perform_handshake(client_id, ssl_socket):
                self.logger.warning(f"Handshake failed for {client_id}")
                return
            
            # Handle client commands
            self._handle_client_commands(client_id, ssl_socket)
            
        except Exception as e:
            self.logger.error(f"Client handling error for {client_address}: {e}")
            with self._stats_lock:
                self.stats['failed_connections'] += 1
        
        finally:
            if client_id:
                self._remove_client(client_id)
            if ssl_socket:
                try:
                    ssl_socket.close()
                except:
                    pass
    
    def _generate_client_id(self, client_address: tuple) -> str:
        """Generate unique client ID"""
        timestamp = str(time.time())
        address_str = f"{client_address[0]}:{client_address[1]}"
        random_part = secrets.token_hex(8)
        
        combined = f"{timestamp}_{address_str}_{random_part}"
        return hashlib.sha256(combined.encode()).hexdigest()[:16]
    
    def _register_client(self, client_id: str, client_socket: socket.socket, client_address: tuple):
        """Register new client"""
        with self._clients_lock:
            self.clients[client_id] = {
                'socket': client_socket,
                'address': client_address,
                'connected_at': time.time(),
                'last_activity': time.time(),
                'commands_executed': 0,
                'session_key': secrets.token_hex(32)
            }
            
            with self._stats_lock:
                self.stats['active_connections'] = len(self.clients)
            
            self.logger.info(f"Client {client_id} registered from {client_address}")
    
    def _remove_client(self, client_id: str):
        """Remove client from registry"""
        with self._clients_lock:
            if client_id in self.clients:
                del self.clients[client_id]
                
                with self._stats_lock:
                    self.stats['active_connections'] = len(self.clients)
                
                self.logger.info(f"Client {client_id} removed")
    
    def _perform_handshake(self, client_id: str, client_socket: socket.socket) -> bool:
        """Perform handshake with client"""
        try:
            # Receive client hello
            client_hello = self._receive_message(client_socket)
            if not client_hello or client_hello.get('type') != 'client_hello':
                return False
            
            # Send server hello
            server_hello = {
                'type': 'server_hello',
                'session_key': self.clients[client_id]['session_key'],
                'server_capabilities': ['file_transfer', 'shell', 'system_info'],
                'timestamp': time.time()
            }
            
            self._send_message(client_socket, server_hello)
            return True
            
        except Exception as e:
            self.logger.error(f"Handshake error for {client_id}: {e}")
            return False
    
    def _handle_client_commands(self, client_id: str, client_socket: socket.socket):
        """Handle commands from client"""
        while not self._shutdown_event.is_set():
            try:
                # Update last activity
                with self._clients_lock:
                    if client_id in self.clients:
                        self.clients[client_id]['last_activity'] = time.time()
                
                # For demonstration, we'll just echo back
                # In real implementation, this would process actual commands
                time.sleep(1)
                
            except Exception as e:
                self.logger.error(f"Command handling error for {client_id}: {e}")
                break
    
    def _send_message(self, client_socket: socket.socket, message: Dict[str, Any]):
        """Send message to client"""
        try:
            data = json.dumps(message).encode('utf-8')
            length = len(data)
            
            # Send length header
            client_socket.sendall(length.to_bytes(4, byteorder='big'))
            
            # Send data
            client_socket.sendall(data)
            
        except Exception as e:
            self.logger.error(f"Send message error: {e}")
            raise
    
    def _receive_message(self, client_socket: socket.socket) -> Optional[Dict[str, Any]]:
        """Receive message from client"""
        try:
            # Receive length header
            length_data = self._receive_exact(client_socket, 4)
            if not length_data:
                return None
            
            length = int.from_bytes(length_data, byteorder='big')
            
            # Receive data
            data = self._receive_exact(client_socket, length)
            if not data:
                return None
            
            return json.loads(data.decode('utf-8'))
            
        except Exception as e:
            self.logger.error(f"Receive message error: {e}")
            return None
    
    def _receive_exact(self, client_socket: socket.socket, count: int) -> Optional[bytes]:
        """Receive exact number of bytes"""
        data = b''
        while len(data) < count:
            chunk = client_socket.recv(count - len(data))
            if not chunk:
                return None
            data += chunk
        return data
    
    def _safe_shutdown(self):
        """Safely shutdown the server"""
        with self._server_lock:
            if not self.running:
                return
            
            self.logger.info("Initiating server shutdown")
            self.running = False
            self._shutdown_event.set()
            
            # Close server socket
            if self.server_socket:
                try:
                    self.server_socket.close()
                except:
                    pass
            
            # Disconnect all clients
            with self._clients_lock:
                for client_id in list(self.clients.keys()):
                    self._remove_client(client_id)
            
            # Shutdown thread pools
            self.thread_pool.shutdown(wait=True, timeout=10)
            self.io_pool.shutdown(wait=True, timeout=10)
            
            # Wait for background threads
            if self.cleanup_thread and self.cleanup_thread.is_alive():
                self.cleanup_thread.join(timeout=5)
            
            if self.monitor_thread and self.monitor_thread.is_alive():
                self.monitor_thread.join(timeout=5)
            
            self.logger.info("Server shutdown complete")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get server statistics"""
        with self._stats_lock:
            uptime = datetime.now() - self.stats['start_time']
            return {
                **self.stats.copy(),
                'uptime_seconds': uptime.total_seconds(),
                'rate_limited_ips': list(self.stats['rate_limited_ips'])
            }
    
    def list_clients(self) -> List[Dict[str, Any]]:
        """List connected clients"""
        with self._clients_lock:
            clients = []
            for client_id, client_info in self.clients.items():
                clients.append({
                    'id': client_id,
                    'address': client_info['address'],
                    'connected_at': client_info['connected_at'],
                    'last_activity': client_info['last_activity'],
                    'commands_executed': client_info['commands_executed']
                })
            return clients

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Thread-Safe C2C Server')
    parser.add_argument('--host', default='localhost', help='Server host')
    parser.add_argument('--port', type=int, default=4444, help='Server port')
    parser.add_argument('--max-clients', type=int, default=100, help='Maximum clients')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    server = ThreadSafeServer(
        host=args.host,
        port=args.port,
        max_clients=args.max_clients
    )
    
    try:
        server.start()
    except KeyboardInterrupt:
        print("\nShutting down server...")
    except Exception as e:
        print(f"Server error: {e}")
    finally:
        server._safe_shutdown()

if __name__ == '__main__':
    main()
