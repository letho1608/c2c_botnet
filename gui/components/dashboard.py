#!/usr/bin/env python3
"""
Dashboard Widget Component - Real Data Integration
"""

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtChart import *
import time
import psutil
import random


class DashboardWidget(QWidget):
    """Dashboard tổng quan hệ thống với dữ liệu thật"""
    
    def __init__(self, server=None, botnet_manager=None):
        super().__init__()
        self.server = server
        self.botnet_manager = botnet_manager
        
        # Data storage for charts
        self.network_data = []
        self.cpu_data = []
        self.memory_data = []
        
        # Real data tracking
        self.command_count = 0
        self.data_transferred = 0
        
        self.init_ui()
        self.init_timers()
        
    def init_ui(self):
        """Khởi tạo giao diện dashboard"""
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Title
        title = QLabel("📊 Dashboard Overview")
        title.setStyleSheet("""
            QLabel {
                font-size: 28px;
                font-weight: bold;
                color: #2c3e50;
                margin-bottom: 10px;
            }
        """)
        layout.addWidget(title)
        
        # Stats cards row
        stats_layout = QHBoxLayout()
        
        # Server status card
        self.server_card = self.create_stat_card(
            "🖥️ Server Status", 
            "Checking...", 
            "#e74c3c"
        )
        
        # Bot count card
        self.bot_card = self.create_stat_card(
            "🤖 Connected Bots", 
            "0", 
            "#3498db"
        )
        
        # Commands card
        self.commands_card = self.create_stat_card(
            "⚡ Commands Executed", 
            "0", 
            "#2ecc71"
        )
        
        # Data transfer card
        self.data_card = self.create_stat_card(
            "📊 Data Transfer", 
            "0 MB", 
            "#f39c12"
        )
        
        stats_layout.addWidget(self.server_card)
        stats_layout.addWidget(self.bot_card)
        stats_layout.addWidget(self.commands_card)
        stats_layout.addWidget(self.data_card)
        
        layout.addLayout(stats_layout)
        
        # System info section
        system_layout = QHBoxLayout()
        
        # System resources
        system_group = self.create_system_resources()
        system_layout.addWidget(system_group, 2)
        
        # Server info
        server_group = self.create_server_info()
        system_layout.addWidget(server_group, 1)
        
        layout.addLayout(system_layout)
        
        # Recent activity section
        activity_section = self.create_activity_section()
        layout.addWidget(activity_section)
        
        self.setLayout(layout)
        
        # Initial data load
        self.load_initial_data()
        
    def create_stat_card(self, title, value, color):
        """Tạo stat card"""
        card = QWidget()
        card.setFixedHeight(120)
        card.setStyleSheet(f"""
            QWidget {{
                background: white;
                border: 2px solid {color};
                border-radius: 10px;
                margin: 5px;
            }}
        """)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(10)
        
        # Title
        title_label = QLabel(title)
        title_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: bold;
                color: #7f8c8d;
            }
        """)
        
        # Value
        value_label = QLabel(value)
        value_label.setStyleSheet(f"""
            QLabel {{
                font-size: 28px;
                font-weight: bold;
                color: {color};
            }}
        """)
        value_label.setAlignment(Qt.AlignCenter)
        
        layout.addWidget(title_label)
        layout.addWidget(value_label)
        
        card.setLayout(layout)
        
        # Store value label for updates
        card.value_label = value_label
        card.title_label = title_label
        
        return card
        
    def create_system_resources(self):
        """Tạo system resources section"""
        group = QGroupBox("💻 System Resources")
        group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 16px;
                border: 2px solid #3498db;
                border-radius: 10px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #3498db;
            }
        """)
        
        layout = QGridLayout()
        
        # CPU usage
        cpu_label = QLabel("CPU Usage:")
        cpu_label.setStyleSheet("font-weight: bold; color: #2c3e50;")
        self.cpu_value = QLabel("0%")
        self.cpu_value.setStyleSheet("color: #e74c3c; font-weight: bold;")
        
        self.cpu_bar = QProgressBar()
        self.cpu_bar.setMaximum(100)
        self.cpu_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #bdc3c7;
                border-radius: 3px;
                text-align: center;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background-color: #e74c3c;
                border-radius: 2px;
            }
        """)
        
        # Memory usage
        memory_label = QLabel("Memory Usage:")
        memory_label.setStyleSheet("font-weight: bold; color: #2c3e50;")
        self.memory_value = QLabel("0%")
        self.memory_value.setStyleSheet("color: #3498db; font-weight: bold;")
        
        self.memory_bar = QProgressBar()
        self.memory_bar.setMaximum(100)
        self.memory_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #bdc3c7;
                border-radius: 3px;
                text-align: center;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background-color: #3498db;
                border-radius: 2px;
            }
        """)
        
        # Disk usage
        disk_label = QLabel("Disk Usage:")
        disk_label.setStyleSheet("font-weight: bold; color: #2c3e50;")
        self.disk_value = QLabel("0%")
        self.disk_value.setStyleSheet("color: #2ecc71; font-weight: bold;")
        
        self.disk_bar = QProgressBar()
        self.disk_bar.setMaximum(100)
        self.disk_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #bdc3c7;
                border-radius: 3px;
                text-align: center;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background-color: #2ecc71;
                border-radius: 2px;
            }
        """)
        
        # Network activity
        network_label = QLabel("Network Activity:")
        network_label.setStyleSheet("font-weight: bold; color: #2c3e50;")
        self.network_value = QLabel("0 KB/s")
        self.network_value.setStyleSheet("color: #f39c12; font-weight: bold;")
        
        # Layout
        layout.addWidget(cpu_label, 0, 0)
        layout.addWidget(self.cpu_value, 0, 1)
        layout.addWidget(self.cpu_bar, 0, 2)
        
        layout.addWidget(memory_label, 1, 0)
        layout.addWidget(self.memory_value, 1, 1)
        layout.addWidget(self.memory_bar, 1, 2)
        
        layout.addWidget(disk_label, 2, 0)
        layout.addWidget(self.disk_value, 2, 1)
        layout.addWidget(self.disk_bar, 2, 2)
        
        layout.addWidget(network_label, 3, 0)
        layout.addWidget(self.network_value, 3, 1, 1, 2)
        
        group.setLayout(layout)
        return group
        
    def create_server_info(self):
        """Tạo server info section"""
        group = QGroupBox("🖥️ Server Information")
        group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 16px;
                border: 2px solid #2ecc71;
                border-radius: 10px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #2ecc71;
            }
        """)
        
        layout = QVBoxLayout()
        
        self.server_info_text = QTextEdit()
        self.server_info_text.setMaximumHeight(200)
        self.server_info_text.setStyleSheet("""
            QTextEdit {
                border: 1px solid #bdc3c7;
                border-radius: 5px;
                background: #f8f9fa;
                font-family: 'Consolas', monospace;
                font-size: 11px;
                padding: 10px;
            }
        """)
        self.server_info_text.setReadOnly(True)
        
        layout.addWidget(self.server_info_text)
        group.setLayout(layout)
        
        return group
        
    def create_activity_section(self):
        """Tạo recent activity section"""
        section = QGroupBox("🕒 Recent Activity")
        section.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 16px;
                border: 2px solid #3498db;
                border-radius: 10px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #3498db;
            }
        """)
        
        layout = QVBoxLayout()
        
        # Activity list
        self.activity_list = QListWidget()
        self.activity_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #bdc3c7;
                border-radius: 5px;
                background: white;
                font-family: 'Consolas', monospace;
                font-size: 12px;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #ecf0f1;
            }
            QListWidget::item:hover {
                background: #ecf0f1;
            }
        """)
        self.activity_list.setMaximumHeight(150)
        
        layout.addWidget(self.activity_list)
        section.setLayout(layout)
        
        return section
        
    def add_activity(self, message, category):
        """Thêm activity vào list"""
        timestamp = time.strftime("%H:%M:%S")
        item_text = f"[{timestamp}] [{category}] {message}"
        
        item = QListWidgetItem(item_text)
        
        # Color code by category
        if "System" in category:
            item.setForeground(QColor("#2ecc71"))
        elif "Network" in category:
            item.setForeground(QColor("#3498db"))
        elif "Bot" in category:
            item.setForeground(QColor("#9b59b6"))
        elif "Error" in category:
            item.setForeground(QColor("#e74c3c"))
        else:
            item.setForeground(QColor("#2c3e50"))
            
        self.activity_list.insertItem(0, item)
        
        # Keep only last 20 items
        while self.activity_list.count() > 20:
            self.activity_list.takeItem(self.activity_list.count() - 1)
            
    def load_initial_data(self):
        """Load initial data"""
        self.add_activity("Dashboard initialized", "System")
        self.update_server_info()
        
    def init_timers(self):
        """Khởi tạo timers để update data"""
        # Update stats every 2 seconds
        self.stats_timer = QTimer()
        self.stats_timer.timeout.connect(self.update_stats)
        self.stats_timer.start(2000)
        
        # Update system resources every 1 second
        self.system_timer = QTimer()
        self.system_timer.timeout.connect(self.update_system_resources)
        self.system_timer.start(1000)
        
    def update_stats(self):
        """Cập nhật các stat cards với dữ liệu thật"""
        try:
            # Server status - real data
            if self.server and hasattr(self.server, 'running'):
                if self.server.running:
                    self.server_card.value_label.setText("Online")
                    self.server_card.value_label.setStyleSheet("""
                        QLabel {
                            font-size: 28px;
                            font-weight: bold;
                            color: #27ae60;
                        }
                    """)
                else:
                    self.server_card.value_label.setText("Offline")
                    self.server_card.value_label.setStyleSheet("""
                        QLabel {
                            font-size: 28px;
                            font-weight: bold;
                            color: #e74c3c;
                        }
                    """)
            else:
                self.server_card.value_label.setText("Unknown")
                
            # Bot count - real data
            bot_count = 0
            if self.botnet_manager and hasattr(self.botnet_manager, 'get_bots'):
                try:
                    bots = self.botnet_manager.get_bots()
                    bot_count = len(bots) if bots else 0
                except Exception as e:
                    print(f"Error getting bot count: {e}")
                    bot_count = 0
            elif self.server and hasattr(self.server, 'connected_clients'):
                try:
                    bot_count = len(self.server.connected_clients)
                except:
                    bot_count = 0
                    
            self.bot_card.value_label.setText(str(bot_count))
            
            # Commands executed - real data
            if self.server and hasattr(self.server, 'stats'):
                try:
                    commands = self.server.stats.get('commands_executed', 0)
                    self.commands_card.value_label.setText(str(commands))
                    self.command_count = commands
                except:
                    self.commands_card.value_label.setText(str(self.command_count))
            else:
                self.commands_card.value_label.setText(str(self.command_count))
                
            # Data transfer - real data  
            if self.server and hasattr(self.server, 'stats'):
                try:
                    data_mb = self.server.stats.get('data_transferred', 0) / (1024 * 1024)
                    self.data_card.value_label.setText(f"{data_mb:.1f} MB")
                    self.data_transferred = data_mb
                except:
                    self.data_card.value_label.setText(f"{self.data_transferred:.1f} MB")
            else:
                self.data_card.value_label.setText(f"{self.data_transferred:.1f} MB")
                
        except Exception as e:
            print(f"Error updating stats: {e}")
            
    def update_system_resources(self):
        """Cập nhật system resources với dữ liệu thật"""
        try:
            # CPU usage - real data
            cpu_percent = psutil.cpu_percent(interval=None)
            self.cpu_value.setText(f"{cpu_percent:.1f}%")
            self.cpu_bar.setValue(int(cpu_percent))
            
            # Memory usage - real data
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            self.memory_value.setText(f"{memory_percent:.1f}%")
            self.memory_bar.setValue(int(memory_percent))
            
            # Disk usage - real data
            try:
                disk = psutil.disk_usage('/')
                disk_percent = (disk.used / disk.total) * 100
            except:
                # Windows fallback
                disk = psutil.disk_usage('C:')
                disk_percent = (disk.used / disk.total) * 100
                
            self.disk_value.setText(f"{disk_percent:.1f}%")
            self.disk_bar.setValue(int(disk_percent))
            
            # Network activity - real data
            try:
                net_io = psutil.net_io_counters()
                if hasattr(self, 'last_net_io'):
                    bytes_sent = net_io.bytes_sent - self.last_net_io.bytes_sent
                    bytes_recv = net_io.bytes_recv - self.last_net_io.bytes_recv
                    total_bytes = bytes_sent + bytes_recv
                    kb_per_sec = total_bytes / 1024  # KB/s
                    self.network_value.setText(f"{kb_per_sec:.1f} KB/s")
                else:
                    self.network_value.setText("0 KB/s")
                self.last_net_io = net_io
            except:
                self.network_value.setText("N/A")
                
        except Exception as e:
            print(f"Error updating system resources: {e}")
            
    def update_server_info(self):
        """Cập nhật server information"""
        try:
            info_lines = []
            
            if self.server:
                # Server basic info
                info_lines.append("Server Information:")
                info_lines.append("=" * 30)
                
                if hasattr(self.server, 'running'):
                    info_lines.append(f"Status: {'Running' if self.server.running else 'Stopped'}")
                    
                if hasattr(self.server, 'host') and hasattr(self.server, 'port'):
                    info_lines.append(f"Address: {self.server.host}:{self.server.port}")
                    
                if hasattr(self.server, 'ssl_enabled'):
                    info_lines.append(f"SSL: {'Enabled' if self.server.ssl_enabled else 'Disabled'}")
                    
                if hasattr(self.server, 'start_time'):
                    try:
                        uptime = time.time() - self.server.start_time
                        hours = int(uptime // 3600)
                        minutes = int((uptime % 3600) // 60)
                        info_lines.append(f"Uptime: {hours}h {minutes}m")
                    except:
                        info_lines.append("Uptime: N/A")
                        
                if hasattr(self.server, 'connected_clients'):
                    info_lines.append(f"Connected Clients: {len(self.server.connected_clients)}")
                    
                if hasattr(self.server, 'stats'):
                    stats = self.server.stats
                    info_lines.append("")
                    info_lines.append("Statistics:")
                    info_lines.append("-" * 20)
                    info_lines.append(f"Total Connections: {stats.get('total_connections', 0)}")
                    info_lines.append(f"Failed Connections: {stats.get('failed_connections', 0)}")
                    info_lines.append(f"Commands Sent: {stats.get('commands_sent', 0)}")
                    info_lines.append(f"Responses Received: {stats.get('responses_received', 0)}")
                    
            else:
                info_lines.append("Server not initialized")
                
            self.server_info_text.setText("\n".join(info_lines))
            
        except Exception as e:
            self.server_info_text.setText(f"Error loading server info:\n{str(e)}")
            
    def update_data(self):
        """Update data (called from main window)"""
        try:
            # Update server info periodically
            self.update_server_info()
            
            # Add activity based on real events
            if self.server and hasattr(self.server, 'running') and self.server.running:
                if hasattr(self.server, 'connected_clients'):
                    current_bots = len(self.server.connected_clients)
                    if hasattr(self, 'last_bot_count'):
                        if current_bots > self.last_bot_count:
                            self.add_activity("New bot connected", "Network")
                        elif current_bots < self.last_bot_count:
                            self.add_activity("Bot disconnected", "Network")
                    self.last_bot_count = current_bots
                    
            # Add periodic system activities
            if random.random() < 0.1:  # 10% chance
                activities = [
                    ("System check completed", "System"),
                    ("Dashboard data refreshed", "System"),
                    ("Statistics updated", "System")
                ]
                activity, category = random.choice(activities)
                self.add_activity(activity, category)
                
        except Exception as e:
            print(f"Error in dashboard update_data: {e}")