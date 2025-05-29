# C2C BOTNET - Phiên Bản Nâng Cao Thread-Safe

## Tổng Quan

Đây là hệ thống C&C (Command & Control) Server Botnet nâng cao được thiết kế với cải tiến toàn diện về thread safety. Hệ thống cung cấp một nền tảng mạnh mẽ để nghiên cứu cách thức hoạt động của botnet với các đặc điểm nổi bật:

- Kiến trúc thread-safe đảm bảo tính ổn định và an toàn khi xử lý đồng thời nhiều kết nối
- Hệ thống mã hóa end-to-end bảo vệ toàn bộ giao tiếp giữa server và client
- Cơ chế quản lý tài nguyên thông minh với connection pooling và rate limiting
- Khả năng mở rộng linh hoạt thông qua kiến trúc plugin
- Giám sát thời gian thực với dashboard trực quan
- Tự động phát hiện và phòng chống các cuộc tấn công DDoS


**QUAN TRỌNG**: Hệ thống này được thiết kế cho nghiên cứu an ninh mạng và phát triển kỹ năng phòng thủ. Dự án cung cấp một nền tảng hoàn chỉnh để hiểu cách malware hoạt động và cách ngăn chặn chúng.

## 🚀 Cài Đặt và Khởi Chạy Nhanh

### Bước 1: Cài Đặt Dependencies
```bash
# Chạy script setup 
pip install -r requirements.txt
```

### Bước 2: Kiểm Tra Hệ Thống
```bash
# Kiểm tra tất cả dependencies
python check_dependencies.py
```

### Bước 3: Khởi Chạy GUI
```bash
# Cách 1: Sử dụng menu tự động
start.bat

# Cách 2: Khởi chạy trực tiếp
python main_gui.py             # GUI chính duy nhất
```

## 🔒 Thread Safety & Cải Tiến Bảo Mật

### 📊 Tối Ưu Hóa Hiệu Năng
- Thao tác I/O không chặn
- Giám sát và dọn dẹp nền
- Emergency shutdown với timeout 10 giây
- Chứng chỉ SSL tự động sinh cho giao tiếp bảo mật

## ✨ Tính Năng

### 🖥️ Server (ThreadSafeServer)
- **Quản Lý Đa Bot**: Điều khiển nhiều bot đồng thời qua console
- **Kết Nối Mã Hóa**: Hỗ trợ SSL/TLS với chứng chỉ tự động sinh
- **Giám Sát Thời Gian Thực**: Theo dõi trạng thái bot và thống kê trực tiếp
- **Thu Thập Dữ Liệu**: Phân tích dữ liệu toàn diện từ các bot
- **Quét Mạng**: Quét mạng tự động và lan truyền
- **Phân Tích Mục Tiêu**: Phối hợp mục tiêu thông minh và điều phối tấn công
- **Thread Safety**: Bảo vệ hoàn toàn chống lại race conditions
- **Connection Pooling**: Quản lý tài nguyên hiệu quả với thread pools có giới hạn
- **Rate Limiting**: Bảo vệ chống flooding kết nối
- **Background Tasks**: Tự động dọn dẹp và giám sát

### 🤖 Client/Bot (ThreadSafeClient)

#### 1. Giám Sát Nâng Cao:
- **Enhanced Keylogger**: Ghi lại phím bấm nâng cao với thread safety
- **Remote Screenshots**: Chụp màn hình bảo mật từ mục tiêu
- **System Information**: Profiling hệ thống chi tiết và trinh sát
- **Process Monitoring**: Theo dõi tiến trình và dịch vụ thời gian thực

#### 2. Điều Khiển Hệ Thống:
- **Shell Command Execution**: Thực thi lệnh từ xa với bảo vệ timeout
- **Shellcode/DLL Injection**: Kỹ thuật tiêm code nâng cao
- **Process Control**: Thao tác tiến trình thread-safe
- **File System Access**: Thao tác file từ xa bảo mật

#### 3. Lan Truyền Tự Động:
- **Network Scanning**: Khám phá mục tiêu thông minh
- **Exploit Integration**: Khai thác lỗ hổng phổ biến
- **USB Spreading**: Lan truyền tự động qua USB
- **Target Infection**: Khám phá và lây nhiễm mục tiêu mới tự động

#### 4. Cơ Chế Duy Trì:
- **Multiple Auto-start Methods**: Registry, Task Scheduler, WMI persistence
- **Access Maintenance**: Duy trì truy cập liên tục
- **Trace Removal**: Khả năng anti-forensics nâng cao
- **Anti-detection**: Tránh phát hiện toàn diện

#### 5. Bảo Mật & Bảo Vệ:
- **End-to-end Encryption**: Tất cả giao tiếp được mã hóa
- **VM Detection**: Phát hiện môi trường ảo hóa nâng cao
- **Multi-layer Authentication**: Cơ chế xác thực mạnh mẽ
- **Auto-reconnection**: Khôi phục kết nối thông minh
- **Thread Safety**: Bảo vệ hoàn toàn chống race condition

## 🚀 Cài Đặt

### Yêu Cầu
- **Python 3.8+** (khuyến nghị Python 3.10+)
- **Windows 10/11** (cho một số module client)
- **Linux** (cho server hoặc module đa nền tảng)
- **Quyền Administrator** (cho một số tính năng nâng cao)

### Hướng Dẫn Cài Đặt

1. **Clone Repository**:
```powershell
git clone https://github.com/letho1608/c2c_botnet
cd c2c_botnet
```

2. **Cài Đặt Dependencies**:
```powershell
pip install -r requirements.txt
```

3. **Tạo Chứng Chỉ SSL** (Tùy chọn - tự động sinh nếu thiếu):
```powershell
# Server sẽ tự động sinh chứng chỉ self-signed
# Chứng chỉ tùy chỉnh có thể đặt là server_cert.pem và server_key.pem
```

## 🎮 Sử Dụng
python gui_launcher.py


### 🎨 Tính Năng GUI PyQt5:
- **Modern Sidebar**: Animation mượt mà, collapse/expand
- **Dashboard**: Real-time charts, system metrics, thống kê bot
- **Bot Management**: Table view với selection, control panel
- **System Monitoring**: CPU/Memory/Network charts, connection logs
- **Dark Theme**: Giao diện chuyên nghiệp, dễ nhìn
- **Responsive**: Tự động resize, optimal layout

### 📟 Command Line (Advanced):
```powershell
# Khởi động server
cd core
python server.py

# Tạo và chạy client
python client.py [server_host] [server_port]
```

**Kết Nối Mặc Định**: `localhost:4444`

## 💻 Lệnh Console

### 🤖 Quản Lý Bot
- `list` - Hiển thị danh sách bot đã kết nối
- `scan [subnet]` - Quét mạng tìm kiếm mục tiêu mới
- `spread <target>` - Lây lan đến mục tiêu cụ thể
- `info <bot_id>` - Hiển thị thông tin chi tiết bot
- `stats` - Hiển thị thống kê server và chỉ số hiệu suất

### 👁️ Giám Sát & Thu Thập Dữ Liệu
- `keylogger <bot_id> <start|stop|dump>` - Điều khiển keylogger
- `advanced_keylog <bot_id> <options>` - Keylogger nâng cao với tùy chọn mở rộng
- `screenshot <bot_id>` - Chụp màn hình từ xa
- `webcam <bot_id> <capture|stream>` - Thu thập hoặc stream webcam
- `sysinfo <bot_id>` - Lấy thông tin hệ thống
- `ps <bot_id>` - Liệt kê các tiến trình đang chạy
- `browser <bot_id> <browser>` - Thu thập dữ liệu trình duyệt
- `wifi <bot_id>` - Thu thập thông tin mạng WiFi
- `credentials <bot_id> <type>` - Thu thập thông tin đăng nhập

### 🔧 Điều Khiển Hệ Thống
- `shell <bot_id> <command>` - Thực thi lệnh shell
- `inject shellcode <bot_id> <base64_shellcode> [pid]` - Tiêm shellcode
- `inject dll <bot_id> <pid> <dll_path>` - Tiêm DLL
- `kill <bot_id> <pid>` - Kết thúc tiến trình
- `migrate <bot_id> <pid>` - Di chuyển tiến trình
- `schedule <bot_id> <time> <command>` - Lập lịch thực thi lệnh

### 🔄 Quản Lý Persistence
- `persist <bot_id> install` - Cài đặt cơ chế duy trì quyền truy cập
- `persist <bot_id> cleanup` - Xóa dấu vết và dọn dẹp
- `persist <bot_id> check` - Kiểm tra trạng thái persistence
- `persist <bot_id> method <method_name>` - Cài đặt phương thức persistence cụ thể

### 📁 Thao Tác File
- `upload <bot_id> <local_path> <remote_path>` - Tải file lên
- `download <bot_id> <remote_path> <local_path>` - Tải file xuống
- `ls <bot_id> <path>` - Liệt kê nội dung thư mục
- `rm <bot_id> <path>` - Xóa file
- `search <bot_id> <pattern>` - Tìm kiếm file

### 🌐 Mạng & Di Chuyển Ngang
- `network_map <subnet>` - Tạo bản đồ topology mạng
- `lateral <bot_id> <method> <target>` - Di chuyển ngang
- `exploit <target> <exploit_name>` - Khai thác mục tiêu
- `pivot <bot_id>` - Sử dụng bot làm điểm xoay mạng

### 🛡️ Bảo Mật & Bảo Vệ
- `obfuscate <payload>` - Làm rối mã binary
- `encrypt <file> <key>` - Mã hóa file
- `anti_vm <bot_id> <enable|disable>` - Bật/tắt phát hiện VM
- `security <level>` - Thiết lập mức độ bảo mật
- `emergency_shutdown` - Tắt khẩn cấp server

## Cấu trúc Project
```
d:\Code\c&c server\
│
├── gui_launcher.py     # GUI Launcher - chọn loại GUI
├── setup_gui.py        # Setup dependencies cho GUI
├── server.py           # Server chính
├── client.py           # Client/Bot chính
├── remote_control.py   # Điều khiển từ xa
├── requirements.txt    # Dependencies (bao gồm PyQt5)
├── FEATURES.md         # Mô tả tính năng chi tiết
├── UPGRADE_PLAN.md     # Kế hoạch nâng cấp
│
├── core/               # Core server
│   ├── server.py       # Xử lý kết nối
│   ├── console.py      # Console UI
│   ├── exploit_builder.py  # Tạo exploit
│   ├── host_manager.py     # Quản lý host
│   ├── multiple_servers.py # Điều phối nhiều server
│   ├── plugin_system.py    # Hệ thống plugin
│   └── reporting.py        # Báo cáo và phân tích
│
├── gui/                # Giao diện người dùng
│   └── pyqt_interface.py   # 🎨 PyQt5 GUI hiện đại (DUY NHẤT)
│
├── botnet/             # Quản lý botnet
│   └── manager.py      # Bot Manager
│
│
├── network/            # Network & Spreading
│   ├── scanner.py      # Network Scanner
│   ├── lateral_movement.py # Di chuyển ngang
│   ├── network_discovery.py # Khám phá mạng
│   ├── signatures.yaml # Chữ ký nhận dạng
│   └── spreading.py    # Phương thức lây lan
│
├── payload/            # Client modules
│   └── modules/
│       ├── anti_analysis.py      # Chống phân tích
│       ├── browser_harvester.py  # Thu thập dữ liệu trình duyệt
│       ├── credential_harvester.py # Thu thập thông tin đăng nhập
│       ├── data_harvester.py     # Thu thập dữ liệu
│       ├── ddos.py               # Tấn công DDoS
│       ├── keylogger.py          # Ghi lại phím bấm
│       ├── media_capture.py      # Thu thập media
│       ├── persistence.py        # Duy trì quyền truy cập
│       ├── process_migration.py  # Di chuyển giữa các tiến trình
│       ├── scheduler.py          # Lập lịch tác vụ
│       ├── screenshot.py         # Chụp màn hình
│       ├── shellcode.py          # Thực thi shellcode
│       ├── sysinfo.py            # Thông tin hệ thống
│       ├── webcam.py             # Truy cập webcam
│       └── wifi_harvester.py     # Thu thập thông tin WiFi
│
└── utils/              # Utilities
    ├── advanced_protection.py    # Bảo vệ nâng cao
    ├── anti_vm.py                # Phát hiện môi trường ảo hóa
    ├── cert_pinning.py           # Gắn chứng chỉ
    ├── code_obfuscation.py       # Làm rối mã nguồn
    ├── crypto.py                 # Mã hóa cơ bản
    ├── integrity.py              # Kiểm tra tính toàn vẹn
    ├── logger.py                 # Ghi log
    ├── memory_protection.py      # Bảo vệ bộ nhớ
    ├── network_protection.py     # Bảo vệ kết nối mạng
    └── security_manager.py       # Quản lý bảo mật
```

## Cảnh báo và Mục đích Sử dụng

Dự án này được phát triển và chia sẻ **CHỈ** nhằm mục đích:
- Nghiên cứu về an ninh mạng
- Phát triển kỹ năng phòng thủ
- Hiểu rõ cách thức hoạt động của malware
- Học tập và giáo dục về bảo mật

Tuyệt đối **KHÔNG** sử dụng cho các mục đích:
- Xâm nhập trái phép vào hệ thống máy tính
- Đánh cắp thông tin cá nhân
- Gây hại cho người dùng hoặc hệ thống
- Bất kỳ hoạt động bất hợp pháp nào

Việc sử dụng mã nguồn này phải tuân thủ tất cả luật pháp và quy định liên quan đến an ninh mạng trong khu vực của bạn.

## Tính năng nâng cao

Dự án này triển khai một số tính năng nâng cao để mô phỏng các kỹ thuật được sử dụng bởi malware thực tế:

1. **Đa dạng phương thức persistence**: Triển khai nhiều cơ chế để duy trì quyền truy cập, giúp hiểu rõ cách malware duy trì sự hiện diện trên hệ thống.

2. **Kỹ thuật chống phân tích**: Phát hiện môi trường ảo hóa, chống debug và phân tích tĩnh.

3. **Phòng tránh phát hiện**: Sử dụng mã hóa, đóng gói và kỹ thuật làm rối mã để tránh bị phát hiện.

4. **Hệ thống C2 đa dạng**: Hỗ trợ nhiều kênh liên lạc và cơ chế dự phòng.

Những tính năng này giúp các chuyên gia bảo mật hiểu rõ hơn về cách thức hoạt động của malware và phát triển biện pháp phòng thủ hiệu quả.

## Phát triển

Dự án có cấu trúc mô-đun hóa, cho phép dễ dàng mở rộng và thêm tính năng mới:

1. **Tạo module mới**:
   - Thêm tệp mới vào thư mục `payload/modules/`
   - Tuân thủ API module đã được định nghĩa

2. **Cập nhật server**:
   - Mở rộng logic xử lý trong `core/`
   - Thêm lệnh mới vào console trong `core/console.py`

3. **Cải thiện chức năng**:
   - Thêm các phương thức tấn công mới
   - Tối ưu hiệu năng và bảo mật
   - Nâng cao khả năng tự động hóa

## Giấy phép
Dự án được phân phối dưới giấy phép MIT.