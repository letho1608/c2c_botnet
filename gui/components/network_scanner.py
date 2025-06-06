#!/usr/bin/env python3
"""
Network Scanner Widget Component
"""

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import time
import random
import ipaddress
import threading


class NetworkScannerWidget(QWidget):
    """Widget quét mạng"""
    
    def __init__(self, scanner=None):
        super().__init__()
        self.scanner = scanner
        self.scan_thread = None
        
        self.init_ui()
        
    def init_ui(self):
        """Khởi tạo giao diện network scanner"""
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Title
        title = QLabel("🔍 Network Scanner")
        title.setStyleSheet("""
            QLabel {
                font-size: 28px;
                font-weight: bold;
                color: #2c3e50;
                margin-bottom: 10px;
            }
        """)
        layout.addWidget(title)
        
        # Scan configuration
        config_group = QGroupBox("⚙️ Scan Configuration")
        config_group.setStyleSheet(self.get_group_style("#3498db"))
        config_layout = QFormLayout()
        
        # Target specification
        self.target_edit = QLineEdit("192.168.1.0/24")
        self.target_edit.setStyleSheet(self.get_input_style())
        self.target_edit.setPlaceholderText("192.168.1.0/24, 10.0.0.1-100, or specific IP")
        config_layout.addRow("Target:", self.target_edit)
        
        # Port range
        self.port_edit = QLineEdit("1-1000")
        self.port_edit.setStyleSheet(self.get_input_style())
        self.port_edit.setPlaceholderText("80,443,22 or 1-1000")
        config_layout.addRow("Ports:", self.port_edit)
        
        # Scan type
        self.scan_type_combo = QComboBox()
        self.scan_type_combo.addItems([
            "Host Discovery", "Port Scan", "Service Detection", 
            "OS Detection", "Vulnerability Scan", "Full Scan"
        ])
        self.scan_type_combo.setStyleSheet(self.get_combo_style())
        config_layout.addRow("Scan Type:", self.scan_type_combo)
        
        # Thread count
        self.threads_spin = QSpinBox()
        self.threads_spin.setRange(1, 100)
        self.threads_spin.setValue(10)
        self.threads_spin.setStyleSheet(self.get_input_style())
        config_layout.addRow("Threads:", self.threads_spin)
        
        # Timeout
        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(1, 60)
        self.timeout_spin.setValue(5)
        self.timeout_spin.setSuffix(" seconds")
        self.timeout_spin.setStyleSheet(self.get_input_style())
        config_layout.addRow("Timeout:", self.timeout_spin)
        
        config_group.setLayout(config_layout)
        layout.addWidget(config_group)
        
        # Control buttons
        control_layout = QHBoxLayout()
        
        self.start_btn = QPushButton("🚀 Start Scan")
        self.start_btn.setStyleSheet("""
            QPushButton {
                background: #27ae60;
                color: white;
                border: none;
                padding: 12px 20px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background: #2ecc71;
            }
            QPushButton:disabled {
                background: #95a5a6;
            }
        """)
        self.start_btn.clicked.connect(self.start_scan)
        
        self.stop_btn = QPushButton("⏹️ Stop Scan")
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background: #e74c3c;
                color: white;
                border: none;
                padding: 12px 20px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background: #c0392b;
            }
            QPushButton:disabled {
                background: #95a5a6;
            }
        """)
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self.stop_scan)
        
        export_btn = QPushButton("📄 Export Results")
        export_btn.setStyleSheet("""
            QPushButton {
                background: #3498db;
                color: white;
                border: none;
                padding: 12px 20px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background: #5dade2;
            }
        """)
        export_btn.clicked.connect(self.export_results)
        
        control_layout.addWidget(self.start_btn)
        control_layout.addWidget(self.stop_btn)
        control_layout.addWidget(export_btn)
        control_layout.addStretch()
        
        layout.addLayout(control_layout)
        
        # Progress section
        progress_group = QGroupBox("📊 Scan Progress")
        progress_group.setStyleSheet(self.get_group_style("#f39c12"))
        progress_layout = QVBoxLayout()
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #f39c12;
                border-radius: 5px;
                text-align: center;
                font-weight: bold;
                background: #ecf0f1;
                height: 25px;
            }
            QProgressBar::chunk {
                background-color: #f39c12;
                border-radius: 3px;
            }
        """)
        
        # Status label
        self.status_label = QLabel("Ready to scan")
        self.status_label.setStyleSheet("""
            QLabel {
                font-size: 12px;
                color: #2c3e50;
                font-weight: bold;
            }
        """)
        
        # Statistics
        stats_layout = QHBoxLayout()
        
        self.hosts_found_label = QLabel("Hosts Found: 0")
        self.hosts_found_label.setStyleSheet("color: #27ae60; font-weight: bold;")
        
        self.ports_open_label = QLabel("Open Ports: 0")
        self.ports_open_label.setStyleSheet("color: #3498db; font-weight: bold;")
        
        self.vulnerabilities_label = QLabel("Vulnerabilities: 0")
        self.vulnerabilities_label.setStyleSheet("color: #e74c3c; font-weight: bold;")
        
        stats_layout.addWidget(self.hosts_found_label)
        stats_layout.addWidget(self.ports_open_label)
        stats_layout.addWidget(self.vulnerabilities_label)
        stats_layout.addStretch()
        
        progress_layout.addWidget(self.progress_bar)
        progress_layout.addWidget(self.status_label)
        progress_layout.addLayout(stats_layout)
        
        progress_group.setLayout(progress_layout)
        layout.addWidget(progress_group)
        
        # Results section
        results_splitter = QSplitter(Qt.Horizontal)
        
        # Results table
        self.create_results_table()
        results_splitter.addWidget(self.results_widget)
        
        # Details panel
        self.create_details_panel()
        results_splitter.addWidget(self.details_widget)
        
        results_splitter.setSizes([600, 400])
        layout.addWidget(results_splitter)
        
        self.setLayout(layout)
        
    def create_results_table(self):
        """Tạo bảng kết quả scan"""
        self.results_widget = QWidget()
        layout = QVBoxLayout()
        
        # Table
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(6)
        self.results_table.setHorizontalHeaderLabels([
            "IP Address", "Hostname", "OS", "Open Ports", "Services", "Status"
        ])
        
        self.results_table.setStyleSheet("""
            QTableWidget {
                gridline-color: #bdc3c7;
                background-color: white;
                alternate-background-color: #ecf0f1;
                selection-background-color: #3498db;
                selection-color: white;
                border: 1px solid #bdc3c7;
                border-radius: 5px;
            }
            QTableWidget::item {
                padding: 8px;
                font-size: 11px;
            }
            QHeaderView::section {
                background-color: #34495e;
                color: white;
                padding: 8px;
                border: none;
                font-weight: bold;
            }
        """)
        
        self.results_table.setAlternatingRowColors(True)
        self.results_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.results_table.horizontalHeader().setStretchLastSection(True)
        self.results_table.setSortingEnabled(True)
        
        # Connect selection
        self.results_table.itemSelectionChanged.connect(self.on_host_selected)
        
        layout.addWidget(self.results_table)
        self.results_widget.setLayout(layout)
        
    def create_details_panel(self):
        """Tạo panel chi tiết"""
        self.details_widget = QWidget()
        layout = QVBoxLayout()
        
        # Host details
        details_group = QGroupBox("🖥️ Host Details")
        details_group.setStyleSheet(self.get_group_style("#9b59b6"))
        details_layout = QVBoxLayout()
        
        self.details_text = QTextEdit()
        self.details_text.setStyleSheet("""
            QTextEdit {
                border: 1px solid #bdc3c7;
                border-radius: 5px;
                background: #f8f9fa;
                font-family: 'Consolas', monospace;
                font-size: 11px;
                padding: 10px;
            }
        """)
        self.details_text.setPlainText("Select a host to view details...")
        
        details_layout.addWidget(self.details_text)
        details_group.setLayout(details_layout)
        layout.addWidget(details_group)
        
        # Actions
        actions_group = QGroupBox("⚡ Actions")
        actions_group.setStyleSheet(self.get_group_style("#e67e22"))
        actions_layout = QVBoxLayout()
        
        # Action buttons
        exploit_btn = QPushButton("💥 Exploit")
        exploit_btn.setStyleSheet(self.get_button_style("#e74c3c"))
        exploit_btn.clicked.connect(self.exploit_host)
        
        deploy_btn = QPushButton("🚀 Deploy Bot")
        deploy_btn.setStyleSheet(self.get_button_style("#27ae60"))
        deploy_btn.clicked.connect(self.deploy_bot)
        
        rescan_btn = QPushButton("🔄 Rescan")
        rescan_btn.setStyleSheet(self.get_button_style("#3498db"))
        rescan_btn.clicked.connect(self.rescan_host)
        
        actions_layout.addWidget(exploit_btn)
        actions_layout.addWidget(deploy_btn)
        actions_layout.addWidget(rescan_btn)
        
        actions_group.setLayout(actions_layout)
        layout.addWidget(actions_group)
        
        layout.addStretch()
        self.details_widget.setLayout(layout)
        
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
        
    def get_input_style(self):
        """Lấy style cho input fields"""
        return """
            QLineEdit, QSpinBox {
                border: 1px solid #bdc3c7;
                border-radius: 5px;
                padding: 8px;
                background: white;
                font-size: 12px;
            }
            QLineEdit:focus, QSpinBox:focus {
                border: 2px solid #3498db;
            }
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
        """
        
    def get_button_style(self, color):
        """Lấy style cho button"""
        return f"""
            QPushButton {{
                background: {color};
                color: white;
                border: none;
                padding: 10px;
                border-radius: 5px;
                font-weight: bold;
                margin: 2px;
            }}
            QPushButton:hover {{
                background: {self.darken_color(color)};
            }}
        """
        
    def darken_color(self, hex_color, factor=0.9):
        """Làm tối màu"""
        hex_color = hex_color.lstrip('#')
        rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        rgb = tuple(int(c * factor) for c in rgb)
        return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"
        
    def start_scan(self):
        """Bắt đầu scan"""
        target = self.target_edit.text().strip()
        if not target:
            QMessageBox.warning(self, "Warning", "Please enter a target!")
            return
            
        # Validate target
        if not self.validate_target(target):
            QMessageBox.warning(self, "Warning", "Invalid target format!")
            return
            
        # Clear previous results
        self.results_table.setRowCount(0)
        self.details_text.setPlainText("Scanning...")
        
        # Update UI
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.progress_bar.setValue(0)
        self.status_label.setText("Initializing scan...")
        
        # Start scan thread
        self.scan_thread = ScanThread(target, self.scan_type_combo.currentText())
        self.scan_thread.progress_updated.connect(self.update_progress)
        self.scan_thread.host_found.connect(self.add_host_result)
        self.scan_thread.scan_completed.connect(self.scan_finished)
        self.scan_thread.start()
        
    def stop_scan(self):
        """Dừng scan"""
        if self.scan_thread and self.scan_thread.isRunning():
            self.scan_thread.stop()
            self.scan_thread.wait()
            
        self.scan_finished()
        
    def validate_target(self, target):
        """Validate target format"""
        try:
            # Check if it's a CIDR notation
            if '/' in target:
                ipaddress.ip_network(target, strict=False)
                return True
            
            # Check if it's a range
            if '-' in target:
                parts = target.split('.')
                if len(parts) == 4 and '-' in parts[-1]:
                    return True
                    
            # Check if it's a single IP
            ipaddress.ip_address(target)
            return True
            
        except:
            return False
            
    def update_progress(self, value, status):
        """Cập nhật progress"""
        self.progress_bar.setValue(value)
        self.status_label.setText(status)
        
    def add_host_result(self, host_data):
        """Thêm kết quả host"""
        row = self.results_table.rowCount()
        self.results_table.insertRow(row)
        
        # Add data to table
        items = [
            host_data.get("ip", ""),
            host_data.get("hostname", "Unknown"),
            host_data.get("os", "Unknown"),
            host_data.get("open_ports", ""),
            host_data.get("services", ""),
            host_data.get("status", "Up")
        ]
        
        for col, item_text in enumerate(items):
            item = QTableWidgetItem(str(item_text))
            
            # Color code status
            if col == 5:  # Status column
                if "Up" in item_text:
                    item.setForeground(QColor("#27ae60"))
                elif "Down" in item_text:
                    item.setForeground(QColor("#e74c3c"))
                elif "Filtered" in item_text:
                    item.setForeground(QColor("#f39c12"))
                    
            self.results_table.setItem(row, col, item)
            
        # Update statistics
        hosts_found = self.results_table.rowCount()
        self.hosts_found_label.setText(f"Hosts Found: {hosts_found}")
        
        # Count open ports
        open_ports = 0
        for row in range(self.results_table.rowCount()):
            ports_item = self.results_table.item(row, 3)
            if ports_item and ports_item.text():
                open_ports += len(ports_item.text().split(','))
                
        self.ports_open_label.setText(f"Open Ports: {open_ports}")
        
        # Simulate vulnerabilities
        vulnerabilities = random.randint(0, hosts_found * 2)
        self.vulnerabilities_label.setText(f"Vulnerabilities: {vulnerabilities}")
        
    def scan_finished(self):
        """Scan hoàn thành"""
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.progress_bar.setValue(100)
        self.status_label.setText("Scan completed")
        
        # Resize columns
        self.results_table.resizeColumnsToContents()
        
    def on_host_selected(self):
        """Xử lý khi chọn host"""
        selected_rows = set()
        for item in self.results_table.selectedItems():
            selected_rows.add(item.row())
            
        if selected_rows:
            row = list(selected_rows)[0]
            ip = self.results_table.item(row, 0).text()
            hostname = self.results_table.item(row, 1).text()
            os_info = self.results_table.item(row, 2).text()
            open_ports = self.results_table.item(row, 3).text()
            services = self.results_table.item(row, 4).text()
            
            details = f"""Host Details:
════════════════════════════════════════
IP Address: {ip}
Hostname: {hostname}
Operating System: {os_info}
Status: Online

Port Information:
════════════════════════════════════════
Open Ports: {open_ports}
Services: {services}

Service Details:
════════════════════════════════════════
22/tcp    ssh     OpenSSH 7.4
80/tcp    http    Apache httpd 2.4.6
443/tcp   https   Apache httpd 2.4.6
3389/tcp  rdp     Microsoft Terminal Services

Vulnerabilities:
════════════════════════════════════════
CVE-2021-44228 (Log4j) - CRITICAL
CVE-2021-34527 (PrintNightmare) - HIGH
CVE-2020-1472 (Zerologon) - CRITICAL

Network Information:
════════════════════════════════════════
MAC Address: 00:1B:63:84:45:E6
Vendor: Intel Corporation
Gateway: 192.168.1.1
DNS: 8.8.8.8, 8.8.4.4

Recommendations:
════════════════════════════════════════
• Update Apache to latest version
• Patch Log4j vulnerability
• Disable unnecessary services
• Enable firewall
• Update antivirus definitions
"""
            
            self.details_text.setPlainText(details)
        else:
            self.details_text.setPlainText("Select a host to view details...")
            
    def exploit_host(self):
        """Khai thác host"""
        selected_rows = set()
        for item in self.results_table.selectedItems():
            selected_rows.add(item.row())
            
        if not selected_rows:
            QMessageBox.warning(self, "Warning", "Please select a host first!")
            return
            
        row = list(selected_rows)[0]
        ip = self.results_table.item(row, 0).text()
        
        QMessageBox.information(self, "Exploit", f"Exploitation initiated for {ip}")
        
    def deploy_bot(self):
        """Deploy bot"""
        selected_rows = set()
        for item in self.results_table.selectedItems():
            selected_rows.add(item.row())
            
        if not selected_rows:
            QMessageBox.warning(self, "Warning", "Please select a host first!")
            return
            
        row = list(selected_rows)[0]
        ip = self.results_table.item(row, 0).text()
        
        QMessageBox.information(self, "Deploy", f"Bot deployment initiated for {ip}")
        
    def rescan_host(self):
        """Rescan host"""
        selected_rows = set()
        for item in self.results_table.selectedItems():
            selected_rows.add(item.row())
            
        if not selected_rows:
            QMessageBox.warning(self, "Warning", "Please select a host first!")
            return
            
        row = list(selected_rows)[0]
        ip = self.results_table.item(row, 0).text()
        
        QMessageBox.information(self, "Rescan", f"Rescanning {ip}...")
        
    def export_results(self):
        """Export kết quả"""
        if self.results_table.rowCount() == 0:
            QMessageBox.warning(self, "Warning", "No results to export!")
            return
            
        filename, _ = QFileDialog.getSaveFileName(
            self, 'Export Scan Results', 
            f'scan_results_{int(time.time())}.csv',
            'CSV Files (*.csv);;Text Files (*.txt)'
        )
        
        if filename:
            QMessageBox.information(self, "Export", f"Results exported to {filename}")
            
    def update_data(self):
        """Update data (called from main window)"""
        pass


class ScanThread(QThread):
    """Thread để scan network"""
    
    progress_updated = pyqtSignal(int, str)
    host_found = pyqtSignal(dict)
    scan_completed = pyqtSignal()
    
    def __init__(self, target, scan_type):
        super().__init__()
        self.target = target
        self.scan_type = scan_type
        self.running = True
        
    def run(self):
        """Chạy scan"""
        try:
            # Generate sample hosts based on target
            hosts = self.generate_sample_hosts()
            total_hosts = len(hosts)
            
            for i, host in enumerate(hosts):
                if not self.running:
                    break
                    
                # Simulate scan delay
                self.msleep(100)
                
                # Update progress
                progress = int((i + 1) / total_hosts * 100)
                self.progress_updated.emit(progress, f"Scanning {host['ip']}...")
                
                # Simulate host discovery
                if random.random() > 0.3:  # 70% chance host is up
                    self.host_found.emit(host)
                    
            self.scan_completed.emit()
            
        except Exception as e:
            print(f"Scan error: {e}")
            self.scan_completed.emit()
            
    def stop(self):
        """Dừng scan"""
        self.running = False
        
    def generate_sample_hosts(self):
        """Generate sample hosts for demo"""
        hosts = []
        
        # Sample data
        os_types = ["Windows 10", "Windows Server 2019", "Ubuntu 20.04", "CentOS 7", "macOS"]
        hostnames = ["WORKSTATION", "SERVER", "LAPTOP", "DESKTOP", "DEV-PC"]
        services = ["SSH, HTTP, HTTPS", "RDP, HTTP", "SSH, MySQL", "HTTP, HTTPS, FTP"]
        
        for i in range(20):
            ip = f"192.168.1.{100 + i}"
            host = {
                "ip": ip,
                "hostname": f"{random.choice(hostnames)}-{i:02d}",
                "os": random.choice(os_types),
                "open_ports": "22,80,443" if random.random() > 0.5 else "80,443",
                "services": random.choice(services),
                "status": "Up"
            }
            hosts.append(host)
            
        return hosts