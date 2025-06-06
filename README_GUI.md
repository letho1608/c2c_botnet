# 🤖 C2C Botnet Management System - GUI Module

## 📋 Tổng quan

Hệ thống GUI modular cho C2C Botnet Management, được thiết kế theo kiến trúc module để dễ dàng bảo trì và mở rộng.

## 🏗️ Cấu trúc thư mục

```
gui/
├── __init__.py                 # Package initialization
├── main_window.py             # Main window class
├── components/                # UI components
│   ├── __init__.py
│   ├── sidebar.py            # Modern sidebar navigation
│   ├── dashboard.py          # Dashboard overview
│   ├── bot_management.py     # Bot control interface
│   ├── monitoring.py         # System monitoring
│   ├── payload_builder.py    # Payload creation tool
│   ├── network_scanner.py    # Network scanning
│   ├── logs.py              # Log viewer
│   └── settings.py          # Configuration settings
└── widgets/                  # Reusable widgets
    ├── __init__.py
    ├── base_widget.py        # Base widget class
    ├── charts.py            # Chart components
    ├── tables.py            # Table widgets
    ├── dialogs.py           # Dialog windows
    ├── progress.py          # Progress indicators
    └── console.py           # Console widget
```

## 🚀 Cách sử dụng

### Khởi chạy ứng dụng

```bash
# Cài đặt dependencies
pip install -r requirements.txt

# Chạy GUI
python main.py
```

### Import và sử dụng trong code

```python
# main.py
from gui import MainWindow
from PyQt5.QtWidgets import QApplication

app = QApplication(sys.argv)
window = MainWindow()
window.show()
app.exec_()
```

## 🎯 Tính năng chính

### 📊 Dashboard
- **Real-time statistics**: Thống kê server và bot
- **System monitoring**: CPU, Memory, Network charts
- **Activity feed**: Log hoạt động real-time
- **Status indicators**: Trạng thái hệ thống

### 🤖 Bot Management
- **Bot listing**: Danh sách bot kết nối
- **Bot control**: Điều khiển từng bot
- **Command execution**: Shell, screenshot, keylogger
- **File operations**: Upload/download files
- **Mass commands**: Điều khiển nhiều bot cùng lúc

### 📈 Monitoring
- **System metrics**: CPU, Memory, Disk, Network usage
- **Network traffic**: Real-time traffic charts
- **Connection logs**: Lịch sử kết nối
- **Performance monitoring**: Hiệu suất hệ thống

### ⚙️ Payload Builder
- **Multi-platform**: Windows, Linux, macOS, Android
- **Template system**: Nhiều template có sẵn
- **Code preview**: Xem trước code được generate
- **Security options**: Encryption, obfuscation, anti-debug
- **Build automation**: Tự động build và test

### 🔍 Network Scanner
- **Host discovery**: Tìm kiếm host trong mạng
- **Port scanning**: Quét port services
- **Vulnerability detection**: Phát hiện lỗ hổng
- **Auto exploitation**: Tự động khai thác
- **Target management**: Quản lý target

### 📝 Logs
- **Multi-level logging**: DEBUG, INFO, WARNING, ERROR
- **Real-time display**: Hiển thị log real-time
- **Filtering**: Lọc theo level, category, keyword
- **Export**: Xuất log ra file
- **Search**: Tìm kiếm trong log

### 🔧 Settings
- **Server configuration**: Cấu hình server
- **Security settings**: Bảo mật và mã hóa
- **Network options**: Proxy, rate limiting
- **UI customization**: Theme, font, language
- **Advanced options**: Debug, custom config

## 🎨 Thiết kế UI/UX

### Modern Design
- **Material Design**: Thiết kế hiện đại
- **Responsive**: Tự động resize
- **Dark/Light theme**: Hỗ trợ nhiều theme
- **Icon integration**: Icons emoji tích hợp

### Navigation
- **Sidebar**: Navigation dạng sidebar có thể thu gọn
- **Tabbed interface**: Tabs cho các tính năng
- **Breadcrumb**: Điều hướng rõ ràng
- **Quick access**: Shortcuts và hotkeys

### Interactive Elements
- **Real-time updates**: Cập nhật real-time
- **Progress indicators**: Thanh tiến trình
- **Notifications**: Thông báo người dùng
- **Tooltips**: Gợi ý sử dụng

## 🔧 Kiến trúc Module

### Component Pattern
```python
# Mỗi component là một widget độc lập
class DashboardWidget(QWidget):
    def __init__(self, server=None, botnet_manager=None):
        super().__init__()
        self.server = server
        self.botnet_manager = botnet_manager
        self.init_ui()
        
    def init_ui(self):
        # Khởi tạo giao diện
        pass
        
    def update_data(self):
        # Cập nhật dữ liệu
        pass
```

### Signal/Slot Communication
```python
# Communication giữa components
class ModernSidebar(QWidget):
    page_changed = pyqtSignal(str)  # Signal
    
    def on_menu_clicked(self, action):
        self.page_changed.emit(action)  # Emit signal

class MainWindow(QMainWindow):
    def __init__(self):
        self.sidebar.page_changed.connect(self.change_page)  # Connect slot
```

### Data Sharing
```python
# Chia sẻ data giữa components
class MainWindow(QMainWindow):
    def __init__(self):
        # Core components
        self.server = ThreadSafeServer()
        self.botnet_manager = BotnetManager()
        
        # Truyền vào components
        self.dashboard = DashboardWidget(
            server=self.server,
            botnet_manager=self.botnet_manager
        )
```

## 🎯 Customization

### Thêm Component mới
```python
# 1. Tạo file mới trong gui/components/
# gui/components/my_component.py
class MyComponentWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        # UI code here
        pass

# 2. Import trong __init__.py
# gui/components/__init__.py
from .my_component import MyComponentWidget

# 3. Thêm vào main window
# gui/main_window.py
def init_pages(self):
    self.pages['my_component'] = MyComponentWidget()
```

### Custom Styling
```python
# Sử dụng StyleSheet
def get_custom_style(self):
    return """
        QWidget {
            background: #2c3e50;
            color: white;
            font-family: 'Arial';
        }
        QPushButton {
            background: #3498db;
            border-radius: 8px;
            padding: 10px;
        }
    """
```

### Theme System
```python
# Theme configuration
themes = {
    'dark': {
        'background': '#2c3e50',
        'text': '#ecf0f1',
        'primary': '#3498db'
    },
    'light': {
        'background': '#ecf0f1',
        'text': '#2c3e50',
        'primary': '#3498db'
    }
}
```

## 🔒 Security Features

### Input Validation
- **SQL Injection protection**: Validate inputs
- **XSS prevention**: Escape user input
- **File upload security**: Validate file types
- **Command injection**: Sanitize commands

### Access Control
- **Authentication**: User login system
- **Authorization**: Role-based access
- **Session management**: Secure sessions
- **Audit logging**: Track user actions

## 📊 Performance

### Optimization
- **Lazy loading**: Load components khi cần
- **Data caching**: Cache dữ liệu thường dùng
- **Threading**: Background operations
- **Memory management**: Cleanup resources

### Scalability
- **Modular design**: Dễ dàng thêm features
- **Plugin system**: Hỗ trợ plugins
- **Configuration**: Flexible settings
- **Internationalization**: Multi-language support

## 🐛 Testing & Debug

### Testing
```bash
# Unit tests
python -m pytest tests/gui/

# Integration tests
python -m pytest tests/integration/

# UI tests
python -m pytest tests/ui/
```

### Debug Mode
```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Debug UI updates
def update_data(self):
    print(f"Updating {self.__class__.__name__}")
    # Update logic here
```

## 📚 Documentation

### Code Documentation
- **Docstrings**: Mọi function có docstring
- **Type hints**: Type annotations
- **Comments**: Giải thích logic phức tạp
- **Examples**: Ví dụ sử dụng

### User Guide
- **Screenshots**: Hình ảnh minh họa
- **Tutorials**: Hướng dẫn step-by-step
- **FAQ**: Câu hỏi thường gặp
- **Troubleshooting**: Xử lý lỗi

## 🚀 Development

### Prerequisites
```bash
# Required tools
pip install PyQt5-tools
pip install pyqt5-dev-tools

# Optional development tools
pip install black  # Code formatter
pip install flake8  # Linting
pip install mypy   # Type checking
```

### Build và Package
```bash
# Create standalone executable
pip install pyinstaller
pyinstaller --onefile --windowed main.py

# Create installer
pip install cx_Freeze
python setup.py build
```

## 🎉 Kết luận

GUI module này cung cấp:

✅ **Modular Architecture**: Dễ bảo trì và mở rộng
✅ **Professional UI**: Giao diện chuyên nghiệp
✅ **Full Features**: Đầy đủ tính năng C2 management
✅ **Customizable**: Dễ dàng tùy chỉnh
✅ **Scalable**: Có thể mở rộng
✅ **Cross-platform**: Chạy trên Windows/Linux/macOS

**Usage**: Chỉ cần `python main.py` là có GUI hoàn chỉnh!