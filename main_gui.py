import sys
import json
import threading
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import asdict
from collections import deque

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtChart import *

import psutil
import socket
import os

# AI imports
try:
    from sklearn.ensemble import RandomForestClassifier, IsolationForest
    from sklearn.neural_network import MLPClassifier, MLPRegressor
    from sklearn.cluster import KMeans
    import numpy as np
    import joblib
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False
    print("AI libraries not available. Some features will be limited.")

class ModernSidebar(QWidget):
    """Sidebar hiện đại với animation và icons"""
    
    def __init__(self):
        super().__init__()
        self.expanded = True
        self.animation = QPropertyAnimation(self, b"maximumWidth")
        self.animation.setDuration(300)
        self.animation.setEasingCurve(QEasingCurve.OutCubic)
        self.init_ui()
        
    def init_ui(self):
        self.setFixedWidth(250)
        self.setMaximumWidth(250)
        self.setMinimumWidth(60)
        self.setStyleSheet("""
            ModernSidebar {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #2c3e50, stop:1 #34495e);
                border-right: 2px solid #3498db;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header với toggle button
        header = self.create_header()
        layout.addWidget(header)
        
        # Menu items
        self.menu_items = [
            ("🏠", "Dashboard", "dashboard"),
            ("🧠", "AI Dashboard", "ai_dashboard"),
            ("🤖", "Bot Management", "bots"),
            ("📊", "Monitoring", "monitoring"),
            ("🔍", "Network Scanner", "scanner"),
            ("⚙️", "Payload Builder", "payload"),
            ("📝", "Logs", "logs"),
            ("🔧", "Settings", "settings"),
            ("ℹ️", "About", "about")
        ]
        
        self.buttons = []
        for icon, text, action in self.menu_items:
            btn = self.create_menu_button(icon, text, action)
            self.buttons.append(btn)
            layout.addWidget(btn)
        
        layout.addStretch()
        
        # Footer
        footer = self.create_footer()
        layout.addWidget(footer)
        
        self.setLayout(layout)
        
    def create_header(self):
        header = QWidget()
        header.setFixedHeight(60)
        header.setStyleSheet("""
            QWidget {
                background: rgba(0, 0, 0, 0.2);
                border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            }
        """)
        
        layout = QHBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Logo/Title
        title = QLabel("C2C Control")
        title.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 16px;
                font-weight: bold;
            }
        """)
        
        # Toggle button
        self.toggle_btn = QPushButton("☰")
        self.toggle_btn.setFixedSize(30, 30)
        self.toggle_btn.setStyleSheet("""
            QPushButton {
                color: white;
                background: transparent;
                border: none;
                font-size: 16px;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.1);
                border-radius: 15px;
            }
        """)
        self.toggle_btn.clicked.connect(self.toggle_sidebar)
        
        layout.addWidget(title)
        layout.addStretch()
        layout.addWidget(self.toggle_btn)
        
        header.setLayout(layout)
        return header
        
    def create_menu_button(self, icon, text, action):
        btn = QPushButton()
        btn.setFixedHeight(50)
        btn.setCursor(Qt.PointingHandCursor)
        
        # Layout cho button
        layout = QHBoxLayout()
        layout.setContentsMargins(15, 0, 15, 0)
        
        # Icon
        icon_label = QLabel(icon)
        icon_label.setFixedSize(24, 24)
        icon_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 18px;
            }
        """)
        
        # Text
        text_label = QLabel(text)
        text_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 14px;
                font-weight: 500;
            }
        """)
        
        layout.addWidget(icon_label)
        layout.addSpacing(10)
        layout.addWidget(text_label)
        layout.addStretch()
        
        widget = QWidget()
        widget.setLayout(layout)
        btn.setLayout(QVBoxLayout())
        btn.layout().addWidget(widget)
        btn.layout().setContentsMargins(0, 0, 0, 0)
        
        btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                text-align: left;
            }
            QPushButton:hover {
                background: rgba(52, 152, 219, 0.3);
            }
            QPushButton:pressed {
                background: rgba(52, 152, 219, 0.5);
            }
        """)
        
        # Connect action
        btn.clicked.connect(lambda: self.parent().switch_page(action))
        
        return btn
        
    def create_footer(self):
        footer = QWidget()
        footer.setFixedHeight(80)
        footer.setStyleSheet("""
            QWidget {
                background: rgba(0, 0, 0, 0.3);
                border-top: 1px solid rgba(255, 255, 255, 0.1);
            }
        """)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Status
        status = QLabel("🟢 Server Active")
        status.setStyleSheet("""
            QLabel {
                color: #2ecc71;
                font-size: 12px;
                font-weight: bold;
            }
        """)
        
        # Version
        version = QLabel("v2.0 Thread-Safe")
        version.setStyleSheet("""
            QLabel {
                color: #bdc3c7;
                font-size: 10px;
            }
        """)
        
        layout.addWidget(status)
        layout.addWidget(version)
        
        footer.setLayout(layout)
        return footer
        
    def toggle_sidebar(self):
        if self.expanded:
            self.animation.setStartValue(250)
            self.animation.setEndValue(60)
        else:
            self.animation.setStartValue(60)
            self.animation.setEndValue(250)
            
        self.animation.start()
        self.expanded = not self.expanded

class DashboardWidget(QWidget):
    """Dashboard với thống kê tổng quan"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("📊 Dashboard")
        title.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #2c3e50;
                margin-bottom: 20px;
            }
        """)
        layout.addWidget(title)
        
        # Stats cards
        stats_layout = QHBoxLayout()
        
        self.connected_bots_card = self.create_stat_card("🤖", "Connected Bots", "0", "#3498db")
        self.active_commands_card = self.create_stat_card("⚡", "Active Commands", "0", "#e74c3c")
        self.data_collected_card = self.create_stat_card("📥", "Data Collected", "0 MB", "#2ecc71")
        self.uptime_card = self.create_stat_card("⏱️", "Server Uptime", "00:00:00", "#f39c12")
        
        stats_layout.addWidget(self.connected_bots_card)
        stats_layout.addWidget(self.active_commands_card)
        stats_layout.addWidget(self.data_collected_card)
        stats_layout.addWidget(self.uptime_card)
        
        layout.addLayout(stats_layout)
        
        # Charts
        charts_layout = QHBoxLayout()
        
        # CPU Usage Chart
        self.cpu_chart = self.create_cpu_chart()
        charts_layout.addWidget(self.cpu_chart)
        
        # Memory Usage Chart
        self.memory_chart = self.create_memory_chart()
        charts_layout.addWidget(self.memory_chart)
        
        layout.addLayout(charts_layout)
        
        # Recent activity
        activity_group = QGroupBox("🕒 Recent Activity")
        activity_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #bdc3c7;
                border-radius: 10px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
        activity_layout = QVBoxLayout()
        self.activity_list = QListWidget()
        self.activity_list.setStyleSheet("""
            QListWidget {
                border: none;
                background: transparent;
            }
            QListWidget::item {
                padding: 5px;
                margin: 2px;
                background: #ecf0f1;
                border-radius: 5px;
            }
            QListWidget::item:hover {
                background: #d5dbdb;
            }
        """)
        
        activity_layout.addWidget(self.activity_list)
        activity_group.setLayout(activity_layout)
        layout.addWidget(activity_group)
        
        self.setLayout(layout)
        
        # Timer để cập nhật dữ liệu
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_dashboard)
        self.update_timer.start(1000)  # Update every second
        
    def create_stat_card(self, icon, title, value, color):
        card = QFrame()
        card.setFrameStyle(QFrame.StyledPanel)
        card.setStyleSheet(f"""
            QFrame {{
                background: white;
                border: 2px solid {color};
                border-radius: 10px;
                padding: 10px;
            }}
        """)
        
        layout = QVBoxLayout()
        
        # Icon and title
        header_layout = QHBoxLayout()
        icon_label = QLabel(icon)
        icon_label.setStyleSheet(f"""
            QLabel {{
                font-size: 24px;
                color: {color};
            }}
        """)
        
        title_label = QLabel(title)
        title_label.setStyleSheet(f"""
            QLabel {{
                font-size: 14px;
                font-weight: bold;
                color: {color};
            }}
        """)
        
        header_layout.addWidget(icon_label)
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        # Value
        value_label = QLabel(value)
        value_label.setStyleSheet("""
            QLabel {
                font-size: 20px;
                font-weight: bold;
                color: #2c3e50;
                margin-top: 10px;
            }
        """)
        value_label.setAlignment(Qt.AlignCenter)
        
        layout.addLayout(header_layout)
        layout.addWidget(value_label)
        
        card.setLayout(layout)
        
        # Store value label for updates
        card.value_label = value_label
        
        return card
        
    def create_cpu_chart(self):
        chart = QChart()
        chart.setTitle("CPU Usage (%)")
        chart.setAnimationOptions(QChart.SeriesAnimations)
        
        # Line series
        self.cpu_series = QLineSeries()
        self.cpu_series.setName("CPU")
        
        # Add initial data
        for i in range(60):
            self.cpu_series.append(i, 0)
            
        chart.addSeries(self.cpu_series)
        chart.createDefaultAxes()
        
        chart_view = QChartView(chart)
        chart_view.setRenderHint(QPainter.Antialiasing)
        chart_view.setMaximumHeight(200)
        
        return chart_view
        
    def create_memory_chart(self):
        chart = QChart()
        chart.setTitle("Memory Usage (%)")
        chart.setAnimationOptions(QChart.SeriesAnimations)
        
        # Line series
        self.memory_series = QLineSeries()
        self.memory_series.setName("Memory")
        
        # Add initial data
        for i in range(60):
            self.memory_series.append(i, 0)
            
        chart.addSeries(self.memory_series)
        chart.createDefaultAxes()
        
        chart_view = QChartView(chart)
        chart_view.setRenderHint(QPainter.Antialiasing)
        chart_view.setMaximumHeight(200)
        
        return chart_view
        
    def update_dashboard(self):
        """Cập nhật dữ liệu dashboard"""
        try:
            # Update CPU usage
            cpu_percent = psutil.cpu_percent()
            
            # Update CPU chart
            if hasattr(self, 'cpu_series'):
                points = self.cpu_series.pointsVector()
                if len(points) >= 60:
                    # Shift data left
                    for i in range(len(points) - 1):
                        points[i].setY(points[i + 1].y())
                    points[-1].setY(cpu_percent)
                else:
                    self.cpu_series.append(len(points), cpu_percent)
                    
            # Update Memory usage
            memory_percent = psutil.virtual_memory().percent
            
            # Update Memory chart
            if hasattr(self, 'memory_series'):
                points = self.memory_series.pointsVector()
                if len(points) >= 60:
                    # Shift data left
                    for i in range(len(points) - 1):
                        points[i].setY(points[i + 1].y())
                    points[-1].setY(memory_percent)
                else:
                    self.memory_series.append(len(points), memory_percent)
                    
        except Exception as e:
            print(f"Error updating dashboard: {e}")

class BotManagementWidget(QWidget):
    """Widget quản lý bot với table và thông tin chi tiết"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("🤖 Bot Management")
        title.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #2c3e50;
                margin-bottom: 20px;
            }
        """)
        layout.addWidget(title)
        
        # Toolbar
        toolbar_layout = QHBoxLayout()
        
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.setStyleSheet("""
            QPushButton {
                background: #3498db;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #2980b9;
            }
        """)
        
        select_all_btn = QPushButton("☑️ Select All")
        select_all_btn.setStyleSheet("""
            QPushButton {
                background: #2ecc71;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #27ae60;
            }
        """)
        
        disconnect_btn = QPushButton("❌ Disconnect Selected")
        disconnect_btn.setStyleSheet("""
            QPushButton {
                background: #e74c3c;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #c0392b;
            }
        """)
        
        toolbar_layout.addWidget(refresh_btn)
        toolbar_layout.addWidget(select_all_btn)
        toolbar_layout.addWidget(disconnect_btn)
        toolbar_layout.addStretch()
        
        layout.addLayout(toolbar_layout)
        
        # Splitter for table and details
        splitter = QSplitter(Qt.Horizontal)
        
        # Bot table
        self.bot_table = QTableWidget()
        self.bot_table.setColumnCount(6)
        self.bot_table.setHorizontalHeaderLabels([
            "ID", "IP Address", "OS", "Country", "Status", "Last Seen"
        ])
        
        # Style table
        self.bot_table.setStyleSheet("""
            QTableWidget {
                gridline-color: #bdc3c7;
                background-color: white;
                alternate-background-color: #ecf0f1;
            }
            QTableWidget::item {
                padding: 8px;
            }
            QTableWidget::item:selected {
                background-color: #3498db;
                color: white;
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
        
        splitter.addWidget(self.bot_table)
        
        # Bot details panel
        details_panel = QWidget()
        details_layout = QVBoxLayout()
        
        details_title = QLabel("📋 Bot Details")
        details_title.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #2c3e50;
                margin-bottom: 10px;
            }
        """)
        details_layout.addWidget(details_title)
        
        self.details_text = QTextEdit()
        self.details_text.setStyleSheet("""
            QTextEdit {
                border: 2px solid #bdc3c7;
                border-radius: 5px;
                padding: 10px;
                font-family: 'Consolas', monospace;
                font-size: 12px;
            }
        """)
        self.details_text.setPlainText("Select a bot to view details...")
        
        details_layout.addWidget(self.details_text)
        
        # Control buttons
        control_layout = QHBoxLayout()
        
        shell_btn = QPushButton("💻 Shell")
        keylog_btn = QPushButton("⌨️ Keylogger")
        screenshot_btn = QPushButton("📷 Screenshot")
        
        for btn in [shell_btn, keylog_btn, screenshot_btn]:
            btn.setStyleSheet("""
                QPushButton {
                    background: #9b59b6;
                    color: white;
                    border: none;
                    padding: 8px 12px;
                    border-radius: 5px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background: #8e44ad;
                }
            """)
            
        control_layout.addWidget(shell_btn)
        control_layout.addWidget(keylog_btn)
        control_layout.addWidget(screenshot_btn)
        
        details_layout.addLayout(control_layout)
        details_panel.setLayout(details_layout)
        
        splitter.addWidget(details_panel)
        splitter.setSizes([600, 400])
        
        layout.addWidget(splitter)
        
        self.setLayout(layout)
        
        # Connect signals
        self.bot_table.itemSelectionChanged.connect(self.on_bot_selected)
        refresh_btn.clicked.connect(self.refresh_bots)
        
    def on_bot_selected(self):
        """Xử lý khi chọn bot"""
        selected_rows = set()
        for item in self.bot_table.selectedItems():
            selected_rows.add(item.row())
            
        if selected_rows:
            row = list(selected_rows)[0]
            bot_id = self.bot_table.item(row, 0).text()
            
            # Update details
            details = f"""
Bot ID: {bot_id}
IP Address: {self.bot_table.item(row, 1).text()}
Operating System: {self.bot_table.item(row, 2).text()}
Country: {self.bot_table.item(row, 3).text()}
Status: {self.bot_table.item(row, 4).text()}
Last Seen: {self.bot_table.item(row, 5).text()}

=== System Information ===
CPU: Intel Core i7-10700K
RAM: 16 GB DDR4
Disk: 512 GB SSD
Network: Ethernet 1Gbps

=== Security Status ===
Antivirus: Windows Defender (Active)
Firewall: Enabled
UAC: Enabled
Last Scan: 2 hours ago

=== Available Commands ===
• shell <command> - Execute shell command
• keylogger start/stop - Control keylogger
• screenshot - Take screenshot
• sysinfo - Get detailed system info
• persist install - Install persistence
            """
            
            self.details_text.setPlainText(details.strip())
            
    def refresh_bots(self):
        """Làm mới danh sách bot"""
        # Clear current data
        self.bot_table.setRowCount(0)
        
        # Add sample data (in real implementation, get from server)
        sample_bots = [
            ["BOT001", "192.168.1.100", "Windows 11", "🇺🇸 USA", "🟢 Online", "2 mins ago"],
            ["BOT002", "10.0.0.50", "Windows 10", "🇩🇪 Germany", "🟢 Online", "5 mins ago"],
            ["BOT003", "172.16.1.25", "Ubuntu 20.04", "🇬🇧 UK", "🟡 Idle", "10 mins ago"],
            ["BOT004", "192.168.0.15", "macOS Big Sur", "🇫🇷 France", "🟢 Online", "1 min ago"],
            ["BOT005", "10.1.1.80", "Windows 10", "🇯🇵 Japan", "🔴 Offline", "2 hours ago"],
        ]
        
        for i, bot_data in enumerate(sample_bots):
            self.bot_table.insertRow(i)
            for j, value in enumerate(bot_data):
                item = QTableWidgetItem(str(value))
                
                # Color coding for status
                if j == 4:  # Status column
                    if "Online" in value:
                        item.setBackground(QColor("#d5f4e6"))
                    elif "Idle" in value:
                        item.setBackground(QColor("#fff3cd"))
                    elif "Offline" in value:
                        item.setBackground(QColor("#f8d7da"))
                        
                self.bot_table.setItem(i, j, item)
                
        # Auto-resize columns
        self.bot_table.resizeColumnsToContents()

class MonitoringWidget(QWidget):
    """Widget giám sát hệ thống với charts và metrics"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("📊 System Monitoring")
        title.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #2c3e50;
                margin-bottom: 20px;
            }
        """)
        layout.addWidget(title)
        
        # Real-time metrics
        metrics_group = QGroupBox("📈 Real-time Metrics")
        metrics_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #3498db;
                border-radius: 10px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
        metrics_layout = QGridLayout()
        
        # System metrics
        self.cpu_progress = self.create_progress_bar("CPU Usage", "#e74c3c")
        self.memory_progress = self.create_progress_bar("Memory Usage", "#f39c12")
        self.disk_progress = self.create_progress_bar("Disk Usage", "#9b59b6")
        self.network_progress = self.create_progress_bar("Network I/O", "#2ecc71")
        
        metrics_layout.addWidget(self.cpu_progress, 0, 0)
        metrics_layout.addWidget(self.memory_progress, 0, 1)
        metrics_layout.addWidget(self.disk_progress, 1, 0)
        metrics_layout.addWidget(self.network_progress, 1, 1)
        
        metrics_group.setLayout(metrics_layout)
        layout.addWidget(metrics_group)
        
        # Charts
        charts_group = QGroupBox("📊 Performance Charts")
        charts_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #2ecc71;
                border-radius: 10px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
        charts_layout = QHBoxLayout()
        
        # Network traffic chart
        self.network_chart = self.create_network_chart()
        charts_layout.addWidget(self.network_chart)
        
        # Bot activity chart
        self.activity_chart = self.create_activity_chart()
        charts_layout.addWidget(self.activity_chart)
        
        charts_group.setLayout(charts_layout)
        layout.addWidget(charts_group)
        
        # Connection log
        log_group = QGroupBox("🔗 Connection Log")
        log_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #f39c12;
                border-radius: 10px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
        log_layout = QVBoxLayout()
        
        self.log_table = QTableWidget()
        self.log_table.setColumnCount(4)
        self.log_table.setHorizontalHeaderLabels([
            "Timestamp", "Event", "Source", "Details"
        ])
        
        self.log_table.setStyleSheet("""
            QTableWidget {
                gridline-color: #bdc3c7;
                background-color: white;
                alternate-background-color: #ecf0f1;
            }
            QTableWidget::item {
                padding: 5px;
            }
            QHeaderView::section {
                background-color: #f39c12;
                color: white;
                padding: 8px;
                border: none;
                font-weight: bold;
            }
        """)
        
        self.log_table.setAlternatingRowColors(True)
        self.log_table.horizontalHeader().setStretchLastSection(True)
        self.log_table.setMaximumHeight(150)
        
        # Add sample log entries
        self.add_log_entry("2025-01-15 10:30:25", "🟢 Bot Connected", "192.168.1.100", "New bot BOT001 connected successfully")
        self.add_log_entry("2025-01-15 10:28:15", "📊 Command Executed", "BOT002", "Keylogger started on target system")
        self.add_log_entry("2025-01-15 10:25:45", "🔍 Scan Complete", "Network Scanner", "Found 5 potential targets in subnet")
        
        log_layout.addWidget(self.log_table)
        log_group.setLayout(log_layout)
        layout.addWidget(log_group)
        
        self.setLayout(layout)
        
        # Update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_monitoring)
        self.update_timer.start(2000)  # Update every 2 seconds
        
    def create_progress_bar(self, label, color):
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Label
        label_widget = QLabel(label)
        label_widget.setStyleSheet("""
            QLabel {
                font-weight: bold;
                color: #2c3e50;
            }
        """)
        
        # Progress bar
        progress = QProgressBar()
        progress.setStyleSheet(f"""
            QProgressBar {{
                border: 2px solid {color};
                border-radius: 5px;
                text-align: center;
                font-weight: bold;
            }}
            QProgressBar::chunk {{
                background-color: {color};
                border-radius: 3px;
            }}
        """)
        progress.setMinimum(0)
        progress.setMaximum(100)
        progress.setValue(0)
        
        # Value label
        value_label = QLabel("0%")
        value_label.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #2c3e50;
            }
        """)
        value_label.setAlignment(Qt.AlignCenter)
        
        layout.addWidget(label_widget)
        layout.addWidget(progress)
        layout.addWidget(value_label)
        
        widget.setLayout(layout)
        
        # Store references for updates
        widget.progress = progress
        widget.value_label = value_label
        
        return widget
        
    def create_network_chart(self):
        chart = QChart()
        chart.setTitle("Network Traffic (KB/s)")
        chart.setAnimationOptions(QChart.SeriesAnimations)
        
        # Create series
        self.upload_series = QLineSeries()
        self.upload_series.setName("Upload")
        self.download_series = QLineSeries()
        self.download_series.setName("Download")
        
        # Add initial data
        for i in range(30):
            self.upload_series.append(i, 0)
            self.download_series.append(i, 0)
            
        chart.addSeries(self.upload_series)
        chart.addSeries(self.download_series)
        chart.createDefaultAxes()
        
        chart_view = QChartView(chart)
        chart_view.setRenderHint(QPainter.Antialiasing)
        
        return chart_view
        
    def create_activity_chart(self):
        chart = QChart()
        chart.setTitle("Bot Activity")
        chart.setAnimationOptions(QChart.SeriesAnimations)
        
        # Pie chart for bot status
        series = QPieSeries()
        series.append("Online", 70)
        series.append("Idle", 20)
        series.append("Offline", 10)
        
        # Style slices
        slices = series.slices()
        if len(slices) >= 3:
            slices[0].setColor(QColor("#2ecc71"))
            slices[1].setColor(QColor("#f39c12"))
            slices[2].setColor(QColor("#e74c3c"))
            
        chart.addSeries(series)
        chart.setTitle("Bot Status Distribution")
        
        chart_view = QChartView(chart)
        chart_view.setRenderHint(QPainter.Antialiasing)
        
        return chart_view
        
    def add_log_entry(self, timestamp, event, source, details):
        row_count = self.log_table.rowCount()
        self.log_table.insertRow(0)  # Insert at top
        
        self.log_table.setItem(0, 0, QTableWidgetItem(timestamp))
        self.log_table.setItem(0, 1, QTableWidgetItem(event))
        self.log_table.setItem(0, 2, QTableWidgetItem(source))
        self.log_table.setItem(0, 3, QTableWidgetItem(details))
        
        # Color code events
        if "Connected" in event:
            for col in range(4):
                self.log_table.item(0, col).setBackground(QColor("#d5f4e6"))
        elif "Error" in event or "Failed" in event:
            for col in range(4):
                self.log_table.item(0, col).setBackground(QColor("#f8d7da"))
                
        # Keep only last 50 entries
        if self.log_table.rowCount() > 50:
            self.log_table.removeRow(50)
            
    def update_monitoring(self):
        """Cập nhật dữ liệu monitoring"""
        try:
            # Update system metrics
            cpu_percent = psutil.cpu_percent()
            memory_percent = psutil.virtual_memory().percent
            disk_percent = psutil.disk_usage('/').percent if os.name != 'nt' else psutil.disk_usage('C:').percent
            
            # Update progress bars
            self.cpu_progress.progress.setValue(int(cpu_percent))
            self.cpu_progress.value_label.setText(f"{cpu_percent:.1f}%")
            
            self.memory_progress.progress.setValue(int(memory_percent))
            self.memory_progress.value_label.setText(f"{memory_percent:.1f}%")
            
            self.disk_progress.progress.setValue(int(disk_percent))
            self.disk_progress.value_label.setText(f"{disk_percent:.1f}%")
            
            # Network usage (simulated)
            import random
            network_percent = random.randint(10, 80)
            self.network_progress.progress.setValue(network_percent)
            self.network_progress.value_label.setText(f"{network_percent}%")
            
        except Exception as e:
            print(f"Error updating monitoring: {e}")

class AIDashboardWidget(QWidget):
    """AI Dashboard với thống kê AI và machine learning"""
    
    def __init__(self, server=None):
        super().__init__()
        self.server = server
        self.ai_integration = None
        
        # Try to initialize AI components
        if AI_AVAILABLE:
            try:
                from ai_integration import AIIntegrationManager
                self.ai_integration = AIIntegrationManager()
            except ImportError:
                print("AI Integration Manager not available")
        
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("🧠 AI Control Dashboard")
        title.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #2c3e50;
                margin-bottom: 20px;
            }
        """)
        layout.addWidget(title)
        
        # AI Status cards
        ai_status_layout = QHBoxLayout()
        
        self.ai_status_card = self.create_ai_status_card("🧠", "AI System", "Available" if AI_AVAILABLE else "Limited", "#3498db")
        self.model_status_card = self.create_ai_status_card("🎯", "Models Trained", "0/4", "#e74c3c")
        self.predictions_card = self.create_ai_status_card("📈", "Predictions Made", "0", "#2ecc71")
        self.accuracy_card = self.create_ai_status_card("🎯", "Model Accuracy", "0%", "#f39c12")
        
        ai_status_layout.addWidget(self.ai_status_card)
        ai_status_layout.addWidget(self.model_status_card)
        ai_status_layout.addWidget(self.predictions_card)
        ai_status_layout.addWidget(self.accuracy_card)
        
        layout.addLayout(ai_status_layout)
        
        # AI Components Grid
        components_group = QGroupBox("🔧 AI Components Status")
        components_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #9b59b6;
                border-radius: 10px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
        components_layout = QGridLayout()
        
        # Component status indicators
        self.bot_ai_status = self.create_component_status("Bot Management AI", "🤖", "#3498db")
        self.security_ai_status = self.create_component_status("Security AI", "🛡️", "#e74c3c")
        self.network_ai_status = self.create_component_status("Network Analysis AI", "🔍", "#2ecc71")
        self.keylogger_ai_status = self.create_component_status("Keylogger AI", "⌨️", "#f39c12")
        
        components_layout.addWidget(self.bot_ai_status, 0, 0)
        components_layout.addWidget(self.security_ai_status, 0, 1)
        components_layout.addWidget(self.network_ai_status, 1, 0)
        components_layout.addWidget(self.keylogger_ai_status, 1, 1)
        
        components_group.setLayout(components_layout)
        layout.addWidget(components_group)
        
        # AI Controls
        controls_group = QGroupBox("🎛️ AI Controls")
        controls_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #34495e;
                border-radius: 10px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
        controls_layout = QHBoxLayout()
        
        # Control buttons
        self.train_models_btn = QPushButton("🎓 Train Models")
        self.analyze_patterns_btn = QPushButton("📊 Analyze Patterns")
        self.optimize_performance_btn = QPushButton("⚡ Optimize Performance")
        self.export_intelligence_btn = QPushButton("📤 Export Intelligence")
        
        for btn in [self.train_models_btn, self.analyze_patterns_btn, 
                   self.optimize_performance_btn, self.export_intelligence_btn]:
            btn.setStyleSheet("""
                QPushButton {
                    background: #9b59b6;
                    color: white;
                    border: none;
                    padding: 12px 20px;
                    border-radius: 8px;
                    font-weight: bold;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background: #8e44ad;
                }
                QPushButton:pressed {
                    background: #7d3c98;
                }
            """)
            controls_layout.addWidget(btn)
        
        controls_group.setLayout(controls_layout)
        layout.addWidget(controls_group)
        
        # AI Performance Charts
        charts_group = QGroupBox("📈 AI Performance Metrics")
        charts_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #16a085;
                border-radius: 10px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
        charts_layout = QHBoxLayout()
        
        # Threat detection chart
        self.threat_chart = self.create_threat_detection_chart()
        charts_layout.addWidget(self.threat_chart)
        
        # Bot performance chart
        self.performance_chart = self.create_bot_performance_chart()
        charts_layout.addWidget(self.performance_chart)
        
        charts_group.setLayout(charts_layout)
        layout.addWidget(charts_group)
        
        # AI Insights Panel
        insights_group = QGroupBox("💡 AI Insights & Recommendations")
        insights_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #e67e22;
                border-radius: 10px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
        insights_layout = QVBoxLayout()
        
        self.insights_text = QTextEdit()
        self.insights_text.setStyleSheet("""
            QTextEdit {
                border: 2px solid #bdc3c7;
                border-radius: 5px;
                padding: 10px;
                font-family: 'Consolas', monospace;
                font-size: 12px;
                background-color: #f8f9fa;
            }
        """)
        self.insights_text.setMaximumHeight(150)
        self.insights_text.setPlainText("AI system initializing...\nWaiting for data to generate insights...")
        
        insights_layout.addWidget(self.insights_text)
        insights_group.setLayout(insights_layout)
        layout.addWidget(insights_group)
        
        self.setLayout(layout)
        
        # Connect button signals
        self.train_models_btn.clicked.connect(self.train_ai_models)
        self.analyze_patterns_btn.clicked.connect(self.analyze_patterns)
        self.optimize_performance_btn.clicked.connect(self.optimize_performance)
        self.export_intelligence_btn.clicked.connect(self.export_intelligence)
        
        # Timer để cập nhật AI dashboard
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_ai_dashboard)
        self.update_timer.start(5000)  # Update every 5 seconds
        
    def create_ai_status_card(self, icon, title, value, color):
        card = QFrame()
        card.setFrameStyle(QFrame.StyledPanel)
        card.setStyleSheet(f"""
            QFrame {{
                background: white;
                border: 2px solid {color};
                border-radius: 10px;
                padding: 15px;
            }}
        """)
        
        layout = QVBoxLayout()
        
        # Icon and title
        header_layout = QHBoxLayout()
        icon_label = QLabel(icon)
        icon_label.setStyleSheet(f"""
            QLabel {{
                font-size: 28px;
                color: {color};
            }}
        """)
        
        title_label = QLabel(title)
        title_label.setStyleSheet(f"""
            QLabel {{
                font-size: 14px;
                font-weight: bold;
                color: {color};
            }}
        """)
        
        header_layout.addWidget(icon_label)
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        # Value
        value_label = QLabel(value)
        value_label.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #2c3e50;
                margin-top: 10px;
            }
        """)
        value_label.setAlignment(Qt.AlignCenter)
        
        layout.addLayout(header_layout)
        layout.addWidget(value_label)
        
        card.setLayout(layout)
        card.value_label = value_label
        
        return card
        
    def create_component_status(self, name, icon, color):
        widget = QWidget()
        layout = QHBoxLayout()
        
        # Icon
        icon_label = QLabel(icon)
        icon_label.setStyleSheet(f"""
            QLabel {{
                font-size: 24px;
                color: {color};
            }}
        """)
        
        # Name and status
        info_layout = QVBoxLayout()
        
        name_label = QLabel(name)
        name_label.setStyleSheet("""
            QLabel {
                font-weight: bold;
                color: #2c3e50;
                font-size: 14px;
            }
        """)
        
        status_label = QLabel("Inactive")
        status_label.setStyleSheet("""
            QLabel {
                color: #e74c3c;
                font-size: 12px;
            }
        """)
        
        info_layout.addWidget(name_label)
        info_layout.addWidget(status_label)
        
        layout.addWidget(icon_label)
        layout.addLayout(info_layout)
        layout.addStretch()
        
        widget.setLayout(layout)
        widget.status_label = status_label
        
        return widget
        
    def create_threat_detection_chart(self):
        chart = QChart()
        chart.setTitle("Threat Detection Over Time")
        chart.setAnimationOptions(QChart.SeriesAnimations)
        
        # Line series for threats
        self.threats_series = QLineSeries()
        self.threats_series.setName("Threats Detected")
        
        # Add initial data
        for i in range(24):
            self.threats_series.append(i, 0)
            
        chart.addSeries(self.threats_series)
        chart.createDefaultAxes()
        
        chart_view = QChartView(chart)
        chart_view.setRenderHint(QPainter.Antialiasing)
        chart_view.setMaximumHeight(200)
        
        return chart_view
        
    def create_bot_performance_chart(self):
        chart = QChart()
        chart.setTitle("Bot AI Performance")
        chart.setAnimationOptions(QChart.SeriesAnimations)
        
        # Pie chart for performance distribution
        series = QPieSeries()
        series.append("High Performance", 60)
        series.append("Medium Performance", 30)
        series.append("Low Performance", 10)
        
        # Style slices
        slices = series.slices()
        if len(slices) >= 3:
            slices[0].setColor(QColor("#2ecc71"))
            slices[1].setColor(QColor("#f39c12"))
            slices[2].setColor(QColor("#e74c3c"))
            
        chart.addSeries(series)
        
        chart_view = QChartView(chart)
        chart_view.setRenderHint(QPainter.Antialiasing)
        chart_view.setMaximumHeight(200)
        
        return chart_view
        
    def train_ai_models(self):
        """Train AI models"""
        self.insights_text.append("🎓 Starting AI model training...")
        # In real implementation, trigger actual training
        QTimer.singleShot(2000, lambda: self.insights_text.append("✅ Model training completed successfully!"))
        
    def analyze_patterns(self):
        """Analyze patterns"""
        self.insights_text.append("📊 Analyzing patterns in bot behavior and network traffic...")
        QTimer.singleShot(1500, lambda: self.insights_text.append("💡 Pattern analysis: Detected potential optimization opportunities"))
        
    def optimize_performance(self):
        """Optimize performance"""
        self.insights_text.append("⚡ Optimizing bot allocation and task distribution...")
        QTimer.singleShot(1000, lambda: self.insights_text.append("🚀 Performance optimization applied"))
        
    def export_intelligence(self):
        """Export intelligence data"""
        filename, _ = QFileDialog.getSaveFileName(self, "Export AI Intelligence", "ai_intelligence.json", "JSON Files (*.json)")
        if filename:
            self.insights_text.append(f"📤 Exporting intelligence data to {filename}...")
            QTimer.singleShot(500, lambda: self.insights_text.append("✅ Intelligence data exported successfully"))
            
    def update_ai_dashboard(self):
        """Update AI dashboard data"""
        try:
            # Update AI status (simulated for now)
            if AI_AVAILABLE:
                # Update model status
                models_trained = 2  # Placeholder
                self.model_status_card.value_label.setText(f"{models_trained}/4")
                
                # Update predictions count
                predictions = 156  # Placeholder
                self.predictions_card.value_label.setText(str(predictions))
                
                # Update accuracy
                accuracy = 87.5  # Placeholder
                self.accuracy_card.value_label.setText(f"{accuracy}%")
                
                # Update component statuses
                self.bot_ai_status.status_label.setText("Active")
                self.bot_ai_status.status_label.setStyleSheet("color: #2ecc71; font-size: 12px;")
                
                self.security_ai_status.status_label.setText("Active")
                self.security_ai_status.status_label.setStyleSheet("color: #2ecc71; font-size: 12px;")
                
                # Update threat detection chart
                import random
                if hasattr(self, 'threats_series'):
                    points = self.threats_series.pointsVector()
                    if len(points) >= 24:
                        # Shift data left
                        for i in range(len(points) - 1):
                            points[i].setY(points[i + 1].y())
                        points[-1].setY(random.randint(0, 10))
                    
        except Exception as e:
            print(f"Error updating AI dashboard: {e}")

# Enhanced Bot Management Widget with AI Integration
class EnhancedBotManagementWidget(BotManagementWidget):
    """Enhanced Bot Management with AI features"""
    
    def __init__(self):
        super().__init__()
        self.add_ai_features()
        
    def add_ai_features(self):
        """Add AI-specific controls and features"""
        # Add AI panel after the main layout
        ai_panel = QGroupBox("🧠 AI Bot Analysis")
        ai_panel.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #9b59b6;
                border-radius: 10px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
        ai_layout = QHBoxLayout()
        
        # AI controls
        ai_cluster_btn = QPushButton("🎯 Cluster Bots")
        ai_optimize_btn = QPushButton("⚡ AI Optimize")
        ai_predict_btn = QPushButton("🔮 Predict Performance")
        ai_recommend_btn = QPushButton("💡 Get Recommendations")
        
        for btn in [ai_cluster_btn, ai_optimize_btn, ai_predict_btn, ai_recommend_btn]:
            btn.setStyleSheet("""
                QPushButton {
                    background: #9b59b6;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 5px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background: #8e44ad;
                }
            """)
            ai_layout.addWidget(btn)
            
        ai_panel.setLayout(ai_layout)
        
        # Insert AI panel into main layout
        main_layout = self.layout()
        main_layout.insertWidget(main_layout.count() - 1, ai_panel)
        
        # Connect AI button signals
        ai_cluster_btn.clicked.connect(self.cluster_bots)
        ai_optimize_btn.clicked.connect(self.ai_optimize)
        ai_predict_btn.clicked.connect(self.predict_performance)
        ai_recommend_btn.clicked.connect(self.get_recommendations)
        
    def cluster_bots(self):
        """Cluster bots using AI"""
        self.details_text.append("\n🎯 AI Clustering Analysis:")
        self.details_text.append("• High-performance cluster: BOT001, BOT002")
        self.details_text.append("• Medium-performance cluster: BOT003")
        self.details_text.append("• Low-performance cluster: BOT005")
        
    def ai_optimize(self):
        """AI optimization"""
        self.details_text.append("\n⚡ AI Optimization Results:")
        self.details_text.append("• Task allocation optimized for efficiency")
        self.details_text.append("• Bot workload balanced")
        self.details_text.append("• Estimated 25% performance improvement")
        
    def predict_performance(self):
        """Predict bot performance"""
        self.details_text.append("\n🔮 Performance Prediction:")
        self.details_text.append("• BOT001: 95% success rate (High confidence)")
        self.details_text.append("• BOT002: 88% success rate (Medium confidence)")
        self.details_text.append("• BOT003: 76% success rate (Low confidence)")
        
    def get_recommendations(self):
        """Get AI recommendations"""
        self.details_text.append("\n💡 AI Recommendations:")
        self.details_text.append("• BOT005: Consider redeployment (low activity)")
        self.details_text.append("• BOT001-002: Ideal for high-priority tasks")
        self.details_text.append("• Network: Expand coverage in detected gaps")

# Enhanced Monitoring Widget with AI Integration
class EnhancedMonitoringWidget(MonitoringWidget):
    """Enhanced Monitoring with AI analytics"""
    
    def __init__(self):
        super().__init__()
        self.add_ai_monitoring()
        
    def add_ai_monitoring(self):
        """Add AI monitoring capabilities"""
        # AI Threat Analysis Panel
        ai_threat_group = QGroupBox("🛡️ AI Threat Analysis")
        ai_threat_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #e74c3c;
                border-radius: 10px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
        threat_layout = QGridLayout()
        
        # Threat metrics
        self.threat_level = self.create_threat_indicator("Threat Level", "LOW", "#2ecc71")
        self.anomaly_score = self.create_threat_indicator("Anomaly Score", "0.12", "#f39c12")
        self.security_status = self.create_threat_indicator("Security Status", "SECURE", "#2ecc71")
        self.ai_alerts = self.create_threat_indicator("AI Alerts", "0", "#3498db")
        
        threat_layout.addWidget(self.threat_level, 0, 0)
        threat_layout.addWidget(self.anomaly_score, 0, 1)
        threat_layout.addWidget(self.security_status, 1, 0)
        threat_layout.addWidget(self.ai_alerts, 1, 1)
        
        ai_threat_group.setLayout(threat_layout)
        
        # Insert into main layout
        main_layout = self.layout()
        main_layout.insertWidget(2, ai_threat_group)
        
    def create_threat_indicator(self, label, value, color):
        widget = QWidget()
        layout = QVBoxLayout()
        
        label_widget = QLabel(label)
        label_widget.setStyleSheet("""
            QLabel {
                font-weight: bold;
                color: #2c3e50;
                font-size: 12px;
            }
        """)
        
        value_widget = QLabel(value)
        value_widget.setStyleSheet(f"""
            QLabel {{
                font-size: 20px;
                font-weight: bold;
                color: {color};
                background: rgba(255, 255, 255, 0.8);
                padding: 10px;
                border-radius: 8px;
                border: 2px solid {color};
            }}
        """)
        value_widget.setAlignment(Qt.AlignCenter)
        
        layout.addWidget(label_widget)
        layout.addWidget(value_widget)
        
        widget.setLayout(layout)
        widget.value_widget = value_widget
        
        return widget
        
    def update_monitoring(self):
        """Enhanced monitoring with AI data"""
        super().update_monitoring()
        
        # Update AI threat indicators
        import random
        
        # Simulate threat level updates
        threat_levels = ["LOW", "MEDIUM", "HIGH"]
        colors = ["#2ecc71", "#f39c12", "#e74c3c"]
        
        current_threat = random.choice(threat_levels)
        threat_color = colors[threat_levels.index(current_threat)]
        
        self.threat_level.value_widget.setText(current_threat)
        self.threat_level.value_widget.setStyleSheet(f"""
            QLabel {{
                font-size: 20px;
                font-weight: bold;
                color: {threat_color};
                background: rgba(255, 255, 255, 0.8);
                padding: 10px;
                border-radius: 8px;
                border: 2px solid {threat_color};
            }}
        """)
        
        # Update anomaly score
        anomaly = round(random.uniform(0.1, 0.9), 2)
        self.anomaly_score.value_widget.setText(str(anomaly))

class PyQtMainWindow(QMainWindow):
    """Main window với modern sidebar và multiple pages"""
    
    def __init__(self, server=None):
        super().__init__()
        self.server = server
        self.current_page = "dashboard"
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("C2C Botnet Control Panel")
        self.setGeometry(100, 100, 1400, 900)
        
        # Set window icon
        self.setWindowIcon(self.style().standardIcon(QStyle.SP_ComputerIcon))
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Sidebar
        self.sidebar = ModernSidebar()
        main_layout.addWidget(self.sidebar)
        
        # Content area
        self.content_area = QStackedWidget()
        self.content_area.setStyleSheet("""
            QStackedWidget {
                background-color: #ecf0f1;
                border-left: 1px solid #bdc3c7;
            }
        """)
        
        # Create pages
        self.create_pages()
        
        main_layout.addWidget(self.content_area)
        central_widget.setLayout(main_layout)
        
        # Status bar
        self.create_status_bar()
        
        # Apply dark theme
        self.apply_dark_theme()
        
    def create_pages(self):
        """Tạo các trang cho ứng dụng"""
        # Dashboard
        self.dashboard = DashboardWidget()
        self.content_area.addWidget(self.dashboard)
          # AI Dashboard
        self.ai_dashboard = AIDashboardWidget()
        self.content_area.addWidget(self.ai_dashboard)
        
        # Enhanced Bot Management with AI features
        self.bot_management = EnhancedBotManagementWidget()
        self.content_area.addWidget(self.bot_management)
        
        # Enhanced Monitoring with AI analytics
        self.monitoring = EnhancedMonitoringWidget()
        self.content_area.addWidget(self.monitoring)
        
        # Other pages (placeholder)
        for page_name in ["scanner", "payload", "logs", "settings", "about"]:
            placeholder = self.create_placeholder_page(page_name)
            self.content_area.addWidget(placeholder)
            
    def create_placeholder_page(self, page_name):
        """Tạo trang placeholder"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        title_map = {
            "scanner": "🔍 Network Scanner",
            "payload": "⚙️ Payload Builder", 
            "logs": "📝 System Logs",
            "settings": "🔧 Settings",
            "about": "ℹ️ About"
        }
        
        title = QLabel(title_map.get(page_name, page_name.title()))
        title.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #2c3e50;
                margin: 50px;
            }
        """)
        title.setAlignment(Qt.AlignCenter)
        
        description = QLabel(f"This is the {page_name} page.\nFeatures will be implemented here.")
        description.setStyleSheet("""
            QLabel {
                font-size: 16px;
                color: #7f8c8d;
                margin: 20px;
            }
        """)
        description.setAlignment(Qt.AlignCenter)
        
        layout.addWidget(title)
        layout.addWidget(description)
        layout.addStretch()
        
        widget.setLayout(layout)
        return widget
        
    def create_status_bar(self):
        """Tạo status bar"""
        self.status_bar = self.statusBar()
        self.status_bar.setStyleSheet("""
            QStatusBar {
                background: #34495e;
                color: white;
                border-top: 1px solid #2c3e50;
            }
        """)
        
        # Server status
        self.server_status = QLabel("🟢 Server: Active")
        self.server_status.setStyleSheet("color: #2ecc71; font-weight: bold;")
        
        # Connected bots
        self.bots_count = QLabel("🤖 Bots: 5 connected")
        self.bots_count.setStyleSheet("color: #3498db; font-weight: bold;")
        
        # Current time
        self.time_label = QLabel()
        self.time_label.setStyleSheet("color: #ecf0f1;")
        
        self.status_bar.addWidget(self.server_status)
        self.status_bar.addPermanentWidget(self.bots_count)
        self.status_bar.addPermanentWidget(self.time_label)
        
        # Update time
        self.time_timer = QTimer()
        self.time_timer.timeout.connect(self.update_time)
        self.time_timer.start(1000)
        self.update_time()
        
    def update_time(self):
        """Cập nhật thời gian"""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.time_label.setText(f"⏰ {current_time}")
        
    def switch_page(self, page_name):
        """Chuyển đổi trang"""
        page_map = {
            "dashboard": 0,
            "ai_dashboard": 1,
            "bots": 2,
            "monitoring": 3,
            "scanner": 4,
            "payload": 5,
            "logs": 6,
            "settings": 7,
            "about": 8
        }
        
        if page_name in page_map:
            self.content_area.setCurrentIndex(page_map[page_name])
            self.current_page = page_name
            
    def apply_dark_theme(self):
        """Áp dụng theme tối"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2c3e50;
            }
            QWidget {
                background-color: #ecf0f1;
                color: #2c3e50;
            }
            QMenuBar {
                background-color: #34495e;
                color: white;
                border: none;
            }
            QMenuBar::item {
                background-color: transparent;
                padding: 8px 12px;
            }
            QMenuBar::item:selected {
                background-color: #3498db;
            }
        """)

class PyQtGUI:
    """Main GUI class để khởi chạy ứng dụng PyQt"""
    
    def __init__(self, server=None):
        self.server = server
        self.app = None
        self.window = None
        
    def start(self):
        """Khởi chạy GUI"""
        if not QApplication.instance():
            self.app = QApplication(sys.argv)
        else:
            self.app = QApplication.instance()
            
        # Set application properties
        self.app.setApplicationName("C2C Botnet Control Panel")
        self.app.setApplicationVersion("2.0")
        self.app.setOrganizationName("Security Research")
        
        # Create main window
        self.window = PyQtMainWindow(self.server)
        self.window.show()
        
        # Start event loop
        return self.app.exec_()
        
    def stop(self):
        """Dừng GUI"""
        if self.window:
            self.window.close()
        if self.app:
            self.app.quit()

def main():
    """Test function để chạy GUI độc lập"""
    gui = PyQtGUI()
    gui.start()

if __name__ == "__main__":
    main()
