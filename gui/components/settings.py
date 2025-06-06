#!/usr/bin/env python3
"""
Settings Widget Component
"""

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import json
import os


class SettingsWidget(QWidget):
    """Widget cài đặt"""
    
    def __init__(self):
        super().__init__()
        self.settings_file = "settings.json"
        self.settings = self.load_settings()
        
        self.init_ui()
        
    def init_ui(self):
        """Khởi tạo giao diện settings"""
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Title
        title = QLabel("🔧 Settings")
        title.setStyleSheet("""
            QLabel {
                font-size: 28px;
                font-weight: bold;
                color: #2c3e50;
                margin-bottom: 10px;
            }
        """)
        layout.addWidget(title)
        
        # Settings tabs
        tab_widget = QTabWidget()
        tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 2px solid #3498db;
                border-radius: 5px;
                background: white;
            }
            QTabBar::tab {
                background: #ecf0f1;
                padding: 10px 20px;
                margin-right: 2px;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
            }
            QTabBar::tab:selected {
                background: #3498db;
                color: white;
            }
            QTabBar::tab:hover {
                background: #5dade2;
                color: white;
            }
        """)
        
        # Server settings tab
        server_tab = self.create_server_settings()
        tab_widget.addTab(server_tab, "🖥️ Server")
        
        # Security settings tab
        security_tab = self.create_security_settings()
        tab_widget.addTab(security_tab, "🔒 Security")
        
        # Network settings tab
        network_tab = self.create_network_settings()
        tab_widget.addTab(network_tab, "🌐 Network")
        
        # Logging settings tab
        logging_tab = self.create_logging_settings()
        tab_widget.addTab(logging_tab, "📝 Logging")
        
        # UI settings tab
        ui_tab = self.create_ui_settings()
        tab_widget.addTab(ui_tab, "🎨 Interface")
        
        # Advanced settings tab
        advanced_tab = self.create_advanced_settings()
        tab_widget.addTab(advanced_tab, "⚡ Advanced")
        
        layout.addWidget(tab_widget)
        
        # Control buttons
        button_layout = QHBoxLayout()
        
        save_btn = QPushButton("💾 Save Settings")
        save_btn.setStyleSheet("""
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
        """)
        save_btn.clicked.connect(self.save_settings)
        
        reset_btn = QPushButton("🔄 Reset to Default")
        reset_btn.setStyleSheet("""
            QPushButton {
                background: #f39c12;
                color: white;
                border: none;
                padding: 12px 20px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background: #e67e22;
            }
        """)
        reset_btn.clicked.connect(self.reset_settings)
        
        apply_btn = QPushButton("✅ Apply")
        apply_btn.setStyleSheet("""
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
        apply_btn.clicked.connect(self.apply_settings)
        
        button_layout.addStretch()
        button_layout.addWidget(save_btn)
        button_layout.addWidget(reset_btn)
        button_layout.addWidget(apply_btn)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
    def create_server_settings(self):
        """Tạo tab server settings"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Server configuration
        server_group = QGroupBox("🖥️ Server Configuration")
        server_group.setStyleSheet(self.get_group_style("#3498db"))
        server_layout = QFormLayout()
        
        # Host
        self.host_edit = QLineEdit(self.settings.get("server", {}).get("host", "0.0.0.0"))
        self.host_edit.setStyleSheet(self.get_input_style())
        server_layout.addRow("Host:", self.host_edit)
        
        # Port
        self.port_spin = QSpinBox()
        self.port_spin.setRange(1, 65535)
        self.port_spin.setValue(self.settings.get("server", {}).get("port", 4444))
        self.port_spin.setStyleSheet(self.get_input_style())
        server_layout.addRow("Port:", self.port_spin)
        
        # Max clients
        self.max_clients_spin = QSpinBox()
        self.max_clients_spin.setRange(1, 10000)
        self.max_clients_spin.setValue(self.settings.get("server", {}).get("max_clients", 500))
        self.max_clients_spin.setStyleSheet(self.get_input_style())
        server_layout.addRow("Max Clients:", self.max_clients_spin)
        
        # Timeout
        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(1, 3600)
        self.timeout_spin.setValue(self.settings.get("server", {}).get("timeout", 300))
        self.timeout_spin.setSuffix(" seconds")
        self.timeout_spin.setStyleSheet(self.get_input_style())
        server_layout.addRow("Client Timeout:", self.timeout_spin)
        
        # Auto start
        self.auto_start_cb = QCheckBox("Auto-start server on launch")
        self.auto_start_cb.setChecked(self.settings.get("server", {}).get("auto_start", True))
        self.auto_start_cb.setStyleSheet(self.get_checkbox_style())
        server_layout.addRow("", self.auto_start_cb)
        
        server_group.setLayout(server_layout)
        layout.addWidget(server_group)
        
        # Performance settings
        perf_group = QGroupBox("⚡ Performance")
        perf_group.setStyleSheet(self.get_group_style("#2ecc71"))
        perf_layout = QFormLayout()
        
        # Thread pool size
        self.thread_pool_spin = QSpinBox()
        self.thread_pool_spin.setRange(1, 100)
        self.thread_pool_spin.setValue(self.settings.get("performance", {}).get("thread_pool_size", 32))
        self.thread_pool_spin.setStyleSheet(self.get_input_style())
        perf_layout.addRow("Thread Pool Size:", self.thread_pool_spin)
        
        # Update interval
        self.update_interval_spin = QSpinBox()
        self.update_interval_spin.setRange(1, 60)
        self.update_interval_spin.setValue(self.settings.get("performance", {}).get("update_interval", 5))
        self.update_interval_spin.setSuffix(" seconds")
        self.update_interval_spin.setStyleSheet(self.get_input_style())
        perf_layout.addRow("Update Interval:", self.update_interval_spin)
        
        # Memory limit
        self.memory_limit_spin = QSpinBox()
        self.memory_limit_spin.setRange(100, 8192)
        self.memory_limit_spin.setValue(self.settings.get("performance", {}).get("memory_limit", 1024))
        self.memory_limit_spin.setSuffix(" MB")
        self.memory_limit_spin.setStyleSheet(self.get_input_style())
        perf_layout.addRow("Memory Limit:", self.memory_limit_spin)
        
        perf_group.setLayout(perf_layout)
        layout.addWidget(perf_group)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
        
    def create_security_settings(self):
        """Tạo tab security settings"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Encryption settings
        encrypt_group = QGroupBox("🔐 Encryption")
        encrypt_group.setStyleSheet(self.get_group_style("#e74c3c"))
        encrypt_layout = QFormLayout()
        
        # Enable SSL
        self.ssl_cb = QCheckBox("Enable SSL/TLS encryption")
        self.ssl_cb.setChecked(self.settings.get("security", {}).get("ssl_enabled", True))
        self.ssl_cb.setStyleSheet(self.get_checkbox_style())
        encrypt_layout.addRow("", self.ssl_cb)
        
        # SSL certificate
        self.cert_edit = QLineEdit(self.settings.get("security", {}).get("ssl_cert", "server.crt"))
        self.cert_edit.setStyleSheet(self.get_input_style())
        cert_btn = QPushButton("📁 Browse")
        cert_btn.setStyleSheet(self.get_small_button_style())
        cert_btn.clicked.connect(lambda: self.browse_file(self.cert_edit, "Certificate Files (*.crt *.pem)"))
        cert_layout = QHBoxLayout()
        cert_layout.addWidget(self.cert_edit)
        cert_layout.addWidget(cert_btn)
        encrypt_layout.addRow("SSL Certificate:", cert_layout)
        
        # SSL key
        self.key_edit = QLineEdit(self.settings.get("security", {}).get("ssl_key", "server.key"))
        self.key_edit.setStyleSheet(self.get_input_style())
        key_btn = QPushButton("📁 Browse")
        key_btn.setStyleSheet(self.get_small_button_style())
        key_btn.clicked.connect(lambda: self.browse_file(self.key_edit, "Key Files (*.key *.pem)"))
        key_layout = QHBoxLayout()
        key_layout.addWidget(self.key_edit)
        key_layout.addWidget(key_btn)
        encrypt_layout.addRow("SSL Key:", key_layout)
        
        encrypt_group.setLayout(encrypt_layout)
        layout.addWidget(encrypt_group)
        
        # Authentication settings
        auth_group = QGroupBox("🔑 Authentication")
        auth_group.setStyleSheet(self.get_group_style("#9b59b6"))
        auth_layout = QFormLayout()
        
        # Require authentication
        self.auth_cb = QCheckBox("Require bot authentication")
        self.auth_cb.setChecked(self.settings.get("security", {}).get("require_auth", True))
        self.auth_cb.setStyleSheet(self.get_checkbox_style())
        auth_layout.addRow("", self.auth_cb)
        
        # Auth key
        self.auth_key_edit = QLineEdit(self.settings.get("security", {}).get("auth_key", ""))
        self.auth_key_edit.setEchoMode(QLineEdit.Password)
        self.auth_key_edit.setStyleSheet(self.get_input_style())
        auth_layout.addRow("Authentication Key:", self.auth_key_edit)
        
        # Show auth key button
        show_key_btn = QPushButton("👁️ Show")
        show_key_btn.setStyleSheet(self.get_small_button_style())
        show_key_btn.setCheckable(True)
        show_key_btn.toggled.connect(lambda checked: self.auth_key_edit.setEchoMode(
            QLineEdit.Normal if checked else QLineEdit.Password))
        auth_layout.addRow("", show_key_btn)
        
        auth_group.setLayout(auth_layout)
        layout.addWidget(auth_group)
        
        # Access control
        access_group = QGroupBox("🚫 Access Control")
        access_group.setStyleSheet(self.get_group_style("#f39c12"))
        access_layout = QVBoxLayout()
        
        # IP whitelist
        whitelist_label = QLabel("IP Whitelist (one per line):")
        whitelist_label.setStyleSheet("font-weight: bold; color: #2c3e50;")
        
        self.whitelist_text = QTextEdit()
        self.whitelist_text.setMaximumHeight(100)
        self.whitelist_text.setStyleSheet(self.get_input_style())
        whitelist_ips = self.settings.get("security", {}).get("ip_whitelist", [])
        self.whitelist_text.setPlainText("\n".join(whitelist_ips))
        
        access_layout.addWidget(whitelist_label)
        access_layout.addWidget(self.whitelist_text)
        
        access_group.setLayout(access_layout)
        layout.addWidget(access_group)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
        
    def create_network_settings(self):
        """Tạo tab network settings"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Connection settings
        conn_group = QGroupBox("🌐 Connection Settings")
        conn_group.setStyleSheet(self.get_group_style("#3498db"))
        conn_layout = QFormLayout()
        
        # Rate limiting
        self.rate_limit_spin = QSpinBox()
        self.rate_limit_spin.setRange(1, 1000)
        self.rate_limit_spin.setValue(self.settings.get("network", {}).get("rate_limit", 100))
        self.rate_limit_spin.setSuffix(" connections/min")
        self.rate_limit_spin.setStyleSheet(self.get_input_style())
        conn_layout.addRow("Rate Limit:", self.rate_limit_spin)
        
        # Keep alive interval
        self.keepalive_spin = QSpinBox()
        self.keepalive_spin.setRange(10, 600)
        self.keepalive_spin.setValue(self.settings.get("network", {}).get("keepalive_interval", 30))
        self.keepalive_spin.setSuffix(" seconds")
        self.keepalive_spin.setStyleSheet(self.get_input_style())
        conn_layout.addRow("Keep-alive Interval:", self.keepalive_spin)
        
        # Buffer size
        self.buffer_size_spin = QSpinBox()
        self.buffer_size_spin.setRange(1024, 65536)
        self.buffer_size_spin.setValue(self.settings.get("network", {}).get("buffer_size", 4096))
        self.buffer_size_spin.setSuffix(" bytes")
        self.buffer_size_spin.setStyleSheet(self.get_input_style())
        conn_layout.addRow("Buffer Size:", self.buffer_size_spin)
        
        conn_group.setLayout(conn_layout)
        layout.addWidget(conn_group)
        
        # Proxy settings
        proxy_group = QGroupBox("🔀 Proxy Settings")
        proxy_group.setStyleSheet(self.get_group_style("#e67e22"))
        proxy_layout = QFormLayout()
        
        # Enable proxy
        self.proxy_cb = QCheckBox("Use proxy for connections")
        self.proxy_cb.setChecked(self.settings.get("network", {}).get("proxy_enabled", False))
        self.proxy_cb.setStyleSheet(self.get_checkbox_style())
        proxy_layout.addRow("", self.proxy_cb)
        
        # Proxy type
        self.proxy_type_combo = QComboBox()
        self.proxy_type_combo.addItems(["HTTP", "SOCKS4", "SOCKS5"])
        self.proxy_type_combo.setCurrentText(self.settings.get("network", {}).get("proxy_type", "HTTP"))
        self.proxy_type_combo.setStyleSheet(self.get_combo_style())
        proxy_layout.addRow("Proxy Type:", self.proxy_type_combo)
        
        # Proxy host
        self.proxy_host_edit = QLineEdit(self.settings.get("network", {}).get("proxy_host", ""))
        self.proxy_host_edit.setStyleSheet(self.get_input_style())
        proxy_layout.addRow("Proxy Host:", self.proxy_host_edit)
        
        # Proxy port
        self.proxy_port_spin = QSpinBox()
        self.proxy_port_spin.setRange(1, 65535)
        self.proxy_port_spin.setValue(self.settings.get("network", {}).get("proxy_port", 8080))
        self.proxy_port_spin.setStyleSheet(self.get_input_style())
        proxy_layout.addRow("Proxy Port:", self.proxy_port_spin)
        
        proxy_group.setLayout(proxy_layout)
        layout.addWidget(proxy_group)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
        
    def create_logging_settings(self):
        """Tạo tab logging settings"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Log configuration
        log_group = QGroupBox("📝 Log Configuration")
        log_group.setStyleSheet(self.get_group_style("#2ecc71"))
        log_layout = QFormLayout()
        
        # Log level
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        self.log_level_combo.setCurrentText(self.settings.get("logging", {}).get("level", "INFO"))
        self.log_level_combo.setStyleSheet(self.get_combo_style())
        log_layout.addRow("Log Level:", self.log_level_combo)
        
        # Log file
        self.log_file_edit = QLineEdit(self.settings.get("logging", {}).get("file", "server.log"))
        self.log_file_edit.setStyleSheet(self.get_input_style())
        log_file_btn = QPushButton("📁 Browse")
        log_file_btn.setStyleSheet(self.get_small_button_style())
        log_file_btn.clicked.connect(lambda: self.browse_save_file(self.log_file_edit, "Log Files (*.log *.txt)"))
        log_file_layout = QHBoxLayout()
        log_file_layout.addWidget(self.log_file_edit)
        log_file_layout.addWidget(log_file_btn)
        log_layout.addRow("Log File:", log_file_layout)
        
        # Max log size
        self.log_size_spin = QSpinBox()
        self.log_size_spin.setRange(1, 1000)
        self.log_size_spin.setValue(self.settings.get("logging", {}).get("max_size", 10))
        self.log_size_spin.setSuffix(" MB")
        self.log_size_spin.setStyleSheet(self.get_input_style())
        log_layout.addRow("Max Log Size:", self.log_size_spin)
        
        # Log rotation
        self.log_rotation_spin = QSpinBox()
        self.log_rotation_spin.setRange(1, 100)
        self.log_rotation_spin.setValue(self.settings.get("logging", {}).get("backup_count", 5))
        self.log_rotation_spin.setStyleSheet(self.get_input_style())
        log_layout.addRow("Log Rotation Count:", self.log_rotation_spin)
        
        # Console logging
        self.console_log_cb = QCheckBox("Enable console logging")
        self.console_log_cb.setChecked(self.settings.get("logging", {}).get("console", True))
        self.console_log_cb.setStyleSheet(self.get_checkbox_style())
        log_layout.addRow("", self.console_log_cb)
        
        log_group.setLayout(log_layout)
        layout.addWidget(log_group)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
        
    def create_ui_settings(self):
        """Tạo tab UI settings"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Theme settings
        theme_group = QGroupBox("🎨 Theme Settings")
        theme_group.setStyleSheet(self.get_group_style("#9b59b6"))
        theme_layout = QFormLayout()
        
        # Theme selection
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Dark", "Light", "Blue", "Green"])
        self.theme_combo.setCurrentText(self.settings.get("ui", {}).get("theme", "Dark"))
        self.theme_combo.setStyleSheet(self.get_combo_style())
        theme_layout.addRow("Theme:", self.theme_combo)
        
        # Font size
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 24)
        self.font_size_spin.setValue(self.settings.get("ui", {}).get("font_size", 12))
        self.font_size_spin.setStyleSheet(self.get_input_style())
        theme_layout.addRow("Font Size:", self.font_size_spin)
        
        # Language
        self.language_combo = QComboBox()
        self.language_combo.addItems(["English", "Vietnamese", "Chinese", "Japanese"])
        self.language_combo.setCurrentText(self.settings.get("ui", {}).get("language", "English"))
        self.language_combo.setStyleSheet(self.get_combo_style())
        theme_layout.addRow("Language:", self.language_combo)
        
        theme_group.setLayout(theme_layout)
        layout.addWidget(theme_group)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
        
    def create_advanced_settings(self):
        """Tạo tab advanced settings"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Debug settings
        debug_group = QGroupBox("🐛 Debug Settings")
        debug_group.setStyleSheet(self.get_group_style("#e74c3c"))
        debug_layout = QVBoxLayout()
        
        # Debug mode
        self.debug_cb = QCheckBox("Enable debug mode")
        self.debug_cb.setChecked(self.settings.get("advanced", {}).get("debug_mode", False))
        self.debug_cb.setStyleSheet(self.get_checkbox_style())
        debug_layout.addWidget(self.debug_cb)
        
        # Verbose logging
        self.verbose_cb = QCheckBox("Verbose logging")
        self.verbose_cb.setChecked(self.settings.get("advanced", {}).get("verbose_logging", False))
        self.verbose_cb.setStyleSheet(self.get_checkbox_style())
        debug_layout.addWidget(self.verbose_cb)
        
        # Auto-update
        self.auto_update_cb = QCheckBox("Auto-update components")
        self.auto_update_cb.setChecked(self.settings.get("advanced", {}).get("auto_update", True))
        self.auto_update_cb.setStyleSheet(self.get_checkbox_style())
        debug_layout.addWidget(self.auto_update_cb)
        
        debug_group.setLayout(debug_layout)
        layout.addWidget(debug_group)
        
        # Custom configuration
        custom_group = QGroupBox("⚙️ Custom Configuration")
        custom_group.setStyleSheet(self.get_group_style("#34495e"))
        custom_layout = QVBoxLayout()
        
        custom_label = QLabel("Advanced JSON Configuration:")
        custom_label.setStyleSheet("font-weight: bold; color: #2c3e50;")
        
        self.custom_config_text = QTextEdit()
        self.custom_config_text.setStyleSheet("""
            QTextEdit {
                border: 1px solid #bdc3c7;
                border-radius: 5px;
                background: #2c3e50;
                color: #ecf0f1;
                font-family: 'Consolas', monospace;
                font-size: 11px;
                padding: 10px;
            }
        """)
        
        # Load custom config
        custom_config = self.settings.get("advanced", {}).get("custom_config", {})
        self.custom_config_text.setPlainText(json.dumps(custom_config, indent=2))
        
        custom_layout.addWidget(custom_label)
        custom_layout.addWidget(self.custom_config_text)
        
        custom_group.setLayout(custom_layout)
        layout.addWidget(custom_group)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
        
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
            QLineEdit, QSpinBox, QTextEdit {
                border: 1px solid #bdc3c7;
                border-radius: 5px;
                padding: 8px;
                background: white;
                font-size: 12px;
            }
            QLineEdit:focus, QSpinBox:focus, QTextEdit:focus {
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
        
    def get_small_button_style(self):
        """Lấy style cho small button"""
        return """
            QPushButton {
                background: #95a5a6;
                color: white;
                border: none;
                padding: 8px 12px;
                border-radius: 5px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background: #7f8c8d;
            }
        """
        
    def browse_file(self, line_edit, file_filter):
        """Browse cho file"""
        filename, _ = QFileDialog.getOpenFileName(self, 'Select File', '', file_filter)
        if filename:
            line_edit.setText(filename)
            
    def browse_save_file(self, line_edit, file_filter):
        """Browse cho save file"""
        filename, _ = QFileDialog.getSaveFileName(self, 'Select File', '', file_filter)
        if filename:
            line_edit.setText(filename)
            
    def load_settings(self):
        """Load settings từ file"""
        default_settings = {
            "server": {
                "host": "0.0.0.0",
                "port": 4444,
                "max_clients": 500,
                "timeout": 300,
                "auto_start": True
            },
            "performance": {
                "thread_pool_size": 32,
                "update_interval": 5,
                "memory_limit": 1024
            },
            "security": {
                "ssl_enabled": True,
                "ssl_cert": "server.crt",
                "ssl_key": "server.key",
                "require_auth": True,
                "auth_key": "",
                "ip_whitelist": []
            },
            "network": {
                "rate_limit": 100,
                "keepalive_interval": 30,
                "buffer_size": 4096,
                "proxy_enabled": False,
                "proxy_type": "HTTP",
                "proxy_host": "",
                "proxy_port": 8080
            },
            "logging": {
                "level": "INFO",
                "file": "server.log",
                "max_size": 10,
                "backup_count": 5,
                "console": True
            },
            "ui": {
                "theme": "Dark",
                "font_size": 12,
                "language": "English"
            },
            "advanced": {
                "debug_mode": False,
                "verbose_logging": False,
                "auto_update": True,
                "custom_config": {}
            }
        }
        
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r') as f:
                    loaded_settings = json.load(f)
                    # Merge with defaults
                    for category in default_settings:
                        if category in loaded_settings:
                            default_settings[category].update(loaded_settings[category])
                        
            return default_settings
        except Exception as e:
            print(f"Error loading settings: {e}")
            return default_settings
            
    def save_settings(self):
        """Lưu settings"""
        try:
            # Collect settings from UI
            settings = {
                "server": {
                    "host": self.host_edit.text(),
                    "port": self.port_spin.value(),
                    "max_clients": self.max_clients_spin.value(),
                    "timeout": self.timeout_spin.value(),
                    "auto_start": self.auto_start_cb.isChecked()
                },
                "performance": {
                    "thread_pool_size": self.thread_pool_spin.value(),
                    "update_interval": self.update_interval_spin.value(),
                    "memory_limit": self.memory_limit_spin.value()
                },
                "security": {
                    "ssl_enabled": self.ssl_cb.isChecked(),
                    "ssl_cert": self.cert_edit.text(),
                    "ssl_key": self.key_edit.text(),
                    "require_auth": self.auth_cb.isChecked(),
                    "auth_key": self.auth_key_edit.text(),
                    "ip_whitelist": self.whitelist_text.toPlainText().strip().split('\n')
                },
                "network": {
                    "rate_limit": self.rate_limit_spin.value(),
                    "keepalive_interval": self.keepalive_spin.value(),
                    "buffer_size": self.buffer_size_spin.value(),
                    "proxy_enabled": self.proxy_cb.isChecked(),
                    "proxy_type": self.proxy_type_combo.currentText(),
                    "proxy_host": self.proxy_host_edit.text(),
                    "proxy_port": self.proxy_port_spin.value()
                },
                "logging": {
                    "level": self.log_level_combo.currentText(),
                    "file": self.log_file_edit.text(),
                    "max_size": self.log_size_spin.value(),
                    "backup_count": self.log_rotation_spin.value(),
                    "console": self.console_log_cb.isChecked()
                },
                "ui": {
                    "theme": self.theme_combo.currentText(),
                    "font_size": self.font_size_spin.value(),
                    "language": self.language_combo.currentText()
                },
                "advanced": {
                    "debug_mode": self.debug_cb.isChecked(),
                    "verbose_logging": self.verbose_cb.isChecked(),
                    "auto_update": self.auto_update_cb.isChecked(),
                    "custom_config": json.loads(self.custom_config_text.toPlainText())
                }
            }
            
            with open(self.settings_file, 'w') as f:
                json.dump(settings, f, indent=2)
                
            self.settings = settings
            QMessageBox.information(self, "Success", "Settings saved successfully!")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save settings:\n{str(e)}")
            
    def reset_settings(self):
        """Reset settings về default"""
        reply = QMessageBox.question(
            self, 'Reset Settings',
            'Are you sure you want to reset all settings to default values?',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            if os.path.exists(self.settings_file):
                os.remove(self.settings_file)
            self.settings = self.load_settings()
            
            # Update UI with default values
            self.update_ui_from_settings()
            
            QMessageBox.information(self, "Reset", "Settings reset to default values!")
            
    def apply_settings(self):
        """Áp dụng settings"""
        self.save_settings()
        QMessageBox.information(self, "Apply", "Settings applied successfully!")
        
    def update_ui_from_settings(self):
        """Cập nhật UI từ settings"""
        # Server settings
        self.host_edit.setText(self.settings.get("server", {}).get("host", "0.0.0.0"))
        self.port_spin.setValue(self.settings.get("server", {}).get("port", 4444))
        self.max_clients_spin.setValue(self.settings.get("server", {}).get("max_clients", 500))
        self.timeout_spin.setValue(self.settings.get("server", {}).get("timeout", 300))
        self.auto_start_cb.setChecked(self.settings.get("server", {}).get("auto_start", True))
        
        # Performance settings
        self.thread_pool_spin.setValue(self.settings.get("performance", {}).get("thread_pool_size", 32))
        self.update_interval_spin.setValue(self.settings.get("performance", {}).get("update_interval", 5))
        self.memory_limit_spin.setValue(self.settings.get("performance", {}).get("memory_limit", 1024))
        
        # Continue updating other settings...
        
    def update_data(self):
        """Update data (called from main window)"""
        pass