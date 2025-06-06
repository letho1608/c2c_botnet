#!/usr/bin/env python3
"""
Monitoring Widget Component
"""

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtChart import *
import time
import psutil
import random


class MonitoringWidget(QWidget):
    """Widget monitoring hệ thống"""
    
    def __init__(self, server=None):
        super().__init__()
        self.server = server
        
        self.init_ui()
        self.init_timers()
        
    def init_ui(self):
        """Khởi tạo giao diện monitoring"""
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Title
        title = QLabel("📊 System Monitoring")
        title.setStyleSheet("""
            QLabel {
                font-size: 28px;
                font-weight: bold;
                color: #2c3e50;
                margin-bottom: 10px;
            }
        """)
        layout.addWidget(title)
        
        # System metrics row
        metrics_layout = QHBoxLayout()
        
        # CPU usage
        self.cpu_widget = self.create_progress_bar("💻 CPU Usage", "#e74c3c")
        metrics_layout.addWidget(self.cpu_widget)
        
        # Memory usage
        self.memory_widget = self.create_progress_bar("🧠 Memory Usage", "#3498db")
        metrics_layout.addWidget(self.memory_widget)
        
        # Disk usage
        self.disk_widget = self.create_progress_bar("💾 Disk Usage", "#2ecc71")
        metrics_layout.addWidget(self.disk_widget)
        
        # Network usage
        self.network_widget = self.create_progress_bar("🌐 Network Usage", "#f39c12")
        metrics_layout.addWidget(self.network_widget)
        
        layout.addLayout(metrics_layout)
        
        # Charts section
        charts_layout = QHBoxLayout()
        
        # Network traffic chart
        network_group = QGroupBox("📈 Network Traffic")
        network_group.setStyleSheet(self.get_group_style("#3498db"))
        network_layout = QVBoxLayout()
        
        self.network_chart = self.create_network_chart()
        network_layout.addWidget(self.network_chart)
        network_group.setLayout(network_layout)
        
        charts_layout.addWidget(network_group)
        
        # Bot activity chart
        activity_group = QGroupBox("🤖 Bot Activity")
        activity_group.setStyleSheet(self.get_group_style("#2ecc71"))
        activity_layout = QVBoxLayout()
        
        self.activity_chart = self.create_activity_chart()
        activity_layout.addWidget(self.activity_chart)
        activity_group.setLayout(activity_layout)
        
        charts_layout.addWidget(activity_group)
        
        layout.addLayout(charts_layout)
        
        # Connection log
        log_group = QGroupBox("🔗 Connection Log")
        log_group.setStyleSheet(self.get_group_style("#f39c12"))
        
        log_layout = QVBoxLayout()
        
        # Log filter toolbar
        filter_layout = QHBoxLayout()
        
        filter_label = QLabel("Filter:")
        filter_label.setStyleSheet("font-weight: bold; color: #2c3e50;")
        
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["All Events", "Connections", "Commands", "Errors"])
        self.filter_combo.setStyleSheet("""
            QComboBox {
                padding: 5px;
                border: 1px solid #bdc3c7;
                border-radius: 3px;
                background: white;
            }
        """)
        
        clear_btn = QPushButton("🗑️ Clear")
        clear_btn.setStyleSheet("""
            QPushButton {
                background: #e74c3c;
                color: white;
                border: none;
                padding: 5px 10px;
                border-radius: 3px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #c0392b;
            }
        """)
        clear_btn.clicked.connect(self.clear_log)
        
        filter_layout.addWidget(filter_label)
        filter_layout.addWidget(self.filter_combo)
        filter_layout.addStretch()
        filter_layout.addWidget(clear_btn)
        
        log_layout.addLayout(filter_layout)
        
        # Log table
        self.log_table = QTableWidget()
        self.log_table.setColumnCount(4)
        self.log_table.setHorizontalHeaderLabels([
            "Timestamp", "Event Type", "Source", "Details"
        ])
        
        self.log_table.setStyleSheet("""
            QTableWidget {
                gridline-color: #bdc3c7;
                background-color: white;
                alternate-background-color: #ecf0f1;
                border: 1px solid #bdc3c7;
                border-radius: 5px;
            }
            QTableWidget::item {
                padding: 8px;
                font-size: 11px;
                font-family: 'Consolas', monospace;
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
        self.log_table.setMaximumHeight(200)
        
        # Add sample log entries
        self.add_log_entry("Connection", "192.168.1.100", "🟢 New bot connected successfully")
        self.add_log_entry("Command", "BOT001", "📊 Screenshot command executed")
        self.add_log_entry("Connection", "192.168.1.101", "🟢 Bot reconnected after timeout")
        self.add_log_entry("Error", "System", "❌ Failed to connect to 192.168.1.200")
        
        log_layout.addWidget(self.log_table)
        log_group.setLayout(log_layout)
        layout.addWidget(log_group)
        
        self.setLayout(layout)
        
    def create_progress_bar(self, label, color):
        """Tạo progress bar widget"""
        widget = QWidget()
        widget.setFixedHeight(120)
        widget.setStyleSheet(f"""
            QWidget {{
                background: white;
                border: 2px solid {color};
                border-radius: 10px;
                margin: 5px;
            }}
        """)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(8)
        
        # Label
        label_widget = QLabel(label)
        label_widget.setStyleSheet("""
            QLabel {
                font-weight: bold;
                color: #2c3e50;
                font-size: 12px;
            }
        """)
        label_widget.setAlignment(Qt.AlignCenter)
        
        # Progress bar
        progress = QProgressBar()
        progress.setStyleSheet(f"""
            QProgressBar {{
                border: 2px solid {color};
                border-radius: 8px;
                text-align: center;
                font-weight: bold;
                background: #ecf0f1;
                height: 25px;
            }}
            QProgressBar::chunk {{
                background-color: {color};
                border-radius: 6px;
                margin: 1px;
            }}
        """)
        progress.setMinimum(0)
        progress.setMaximum(100)
        progress.setValue(0)
        
        # Value label
        value_label = QLabel("0%")
        value_label.setStyleSheet(f"""
            QLabel {{
                font-size: 24px;
                font-weight: bold;
                color: {color};
            }}
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
        """Tạo network traffic chart"""
        chart = QChart()
        chart.setTitle("Real-time Network Traffic")
        chart.setAnimationOptions(QChart.SeriesAnimations)
        
        # Upload series
        self.upload_series = QLineSeries()
        self.upload_series.setName("Upload (KB/s)")
        pen = QPen(QColor("#e74c3c"))
        pen.setWidth(3)
        self.upload_series.setPen(pen)
        
        # Download series
        self.download_series = QLineSeries()
        self.download_series.setName("Download (KB/s)")
        pen = QPen(QColor("#2ecc71"))
        pen.setWidth(3)
        self.download_series.setPen(pen)
        
        # Initialize with data
        for i in range(60):
            self.upload_series.append(i, 0)
            self.download_series.append(i, 0)
            
        chart.addSeries(self.upload_series)
        chart.addSeries(self.download_series)
        chart.createDefaultAxes()
        
        # Customize axes
        axis_x = chart.axes(Qt.Horizontal)[0]
        axis_x.setRange(0, 60)
        axis_x.setTitleText("Time (seconds)")
        
        axis_y = chart.axes(Qt.Vertical)[0]
        axis_y.setRange(0, 1000)
        axis_y.setTitleText("Speed (KB/s)")
        
        chart_view = QChartView(chart)
        chart_view.setRenderHint(QPainter.Antialiasing)
        chart_view.setMaximumHeight(250)
        
        return chart_view
        
    def create_activity_chart(self):
        """Tạo bot activity pie chart"""
        chart = QChart()
        chart.setTitle("Bot Status Distribution")
        chart.setAnimationOptions(QChart.SeriesAnimations)
        
        # Pie series
        self.activity_series = QPieSeries()
        
        # Sample data
        online_slice = self.activity_series.append("🟢 Online", 15)
        idle_slice = self.activity_series.append("🟡 Idle", 8)
        offline_slice = self.activity_series.append("🔴 Offline", 3)
        
        # Style slices
        online_slice.setColor(QColor("#2ecc71"))
        idle_slice.setColor(QColor("#f39c12"))
        offline_slice.setColor(QColor("#e74c3c"))
        
        # Make online slice exploded
        online_slice.setExploded(True)
        online_slice.setLabelVisible(True)
        idle_slice.setLabelVisible(True)
        offline_slice.setLabelVisible(True)
        
        chart.addSeries(self.activity_series)
        
        chart_view = QChartView(chart)
        chart_view.setRenderHint(QPainter.Antialiasing)
        chart_view.setMaximumHeight(250)
        
        return chart_view
        
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
        
    def add_log_entry(self, event_type, source, details):
        """Thêm log entry"""
        timestamp = time.strftime("%H:%M:%S")
        
        row_count = self.log_table.rowCount()
        self.log_table.insertRow(0)  # Insert at top
        
        self.log_table.setItem(0, 0, QTableWidgetItem(timestamp))
        self.log_table.setItem(0, 1, QTableWidgetItem(event_type))
        self.log_table.setItem(0, 2, QTableWidgetItem(source))
        self.log_table.setItem(0, 3, QTableWidgetItem(details))
        
        # Color code by event type
        color = QColor("#2c3e50")  # default
        if "Connection" in event_type:
            color = QColor("#2ecc71")
        elif "Command" in event_type:
            color = QColor("#3498db")
        elif "Error" in event_type:
            color = QColor("#e74c3c")
            
        for col in range(4):
            item = self.log_table.item(0, col)
            if item:
                item.setForeground(color)
                
        # Keep only last 100 entries
        while self.log_table.rowCount() > 100:
            self.log_table.removeRow(self.log_table.rowCount() - 1)
            
    def clear_log(self):
        """Xóa log"""
        reply = QMessageBox.question(
            self, 'Clear Log',
            'Are you sure you want to clear all log entries?',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.log_table.setRowCount(0)
            
    def init_timers(self):
        """Khởi tạo timers"""
        # Update system metrics every 2 seconds
        self.metrics_timer = QTimer()
        self.metrics_timer.timeout.connect(self.update_metrics)
        self.metrics_timer.start(2000)
        
        # Update charts every 1 second
        self.chart_timer = QTimer()
        self.chart_timer.timeout.connect(self.update_charts)
        self.chart_timer.start(1000)
        
        # Add random log entries
        self.log_timer = QTimer()
        self.log_timer.timeout.connect(self.add_random_log)
        self.log_timer.start(5000)  # Every 5 seconds
        
    def update_metrics(self):
        """Cập nhật system metrics"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent()
            self.cpu_widget.progress.setValue(int(cpu_percent))
            self.cpu_widget.value_label.setText(f"{cpu_percent:.1f}%")
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            self.memory_widget.progress.setValue(int(memory_percent))
            self.memory_widget.value_label.setText(f"{memory_percent:.1f}%")
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            self.disk_widget.progress.setValue(int(disk_percent))
            self.disk_widget.value_label.setText(f"{disk_percent:.1f}%")
            
            # Network usage (simulated)
            network_percent = random.randint(0, 100)
            self.network_widget.progress.setValue(network_percent)
            self.network_widget.value_label.setText(f"{network_percent}%")
            
        except Exception as e:
            print(f"Error updating metrics: {e}")
            
    def update_charts(self):
        """Cập nhật charts"""
        try:
            # Update network chart
            upload_speed = random.randint(0, 500)
            download_speed = random.randint(0, 800)
            
            self.update_line_series(self.upload_series, upload_speed)
            self.update_line_series(self.download_series, download_speed)
            
            # Update activity chart (occasionally)
            if random.random() < 0.1:  # 10% chance
                online = random.randint(10, 25)
                idle = random.randint(5, 15)
                offline = random.randint(0, 8)
                
                self.activity_series.clear()
                if online > 0:
                    slice_online = self.activity_series.append("🟢 Online", online)
                    slice_online.setColor(QColor("#2ecc71"))
                    slice_online.setExploded(True)
                    slice_online.setLabelVisible(True)
                if idle > 0:
                    slice_idle = self.activity_series.append("🟡 Idle", idle)
                    slice_idle.setColor(QColor("#f39c12"))
                    slice_idle.setLabelVisible(True)
                if offline > 0:
                    slice_offline = self.activity_series.append("🔴 Offline", offline)
                    slice_offline.setColor(QColor("#e74c3c"))
                    slice_offline.setLabelVisible(True)
                    
        except Exception as e:
            print(f"Error updating charts: {e}")
            
    def update_line_series(self, series, new_value):
        """Cập nhật line series"""
        points = []
        
        # Shift existing points left
        for i in range(1, series.count()):
            point = series.at(i)
            points.append(QPointF(i - 1, point.y()))
            
        # Add new point at the end
        points.append(QPointF(59, new_value))
        
        # Replace all points
        series.replace(points)
        
    def add_random_log(self):
        """Thêm random log entry"""
        log_entries = [
            ("Connection", "192.168.1.105", "🟢 Bot connected successfully"),
            ("Command", "BOT003", "📷 Screenshot captured"),
            ("Connection", "192.168.1.102", "🔄 Bot reconnected"),
            ("Command", "BOT001", "⌨️ Keylogger started"),
            ("Error", "System", "❌ Connection timeout"),
            ("Command", "BOT005", "💾 File downloaded"),
            ("Connection", "192.168.1.108", "🔴 Bot disconnected"),
            ("Command", "BOT002", "ℹ️ System info retrieved"),
        ]
        
        if random.random() < 0.7:  # 70% chance to add log
            event_type, source, details = random.choice(log_entries)
            self.add_log_entry(event_type, source, details)
            
    def update_data(self):
        """Update data (called from main window)"""
        # This method is called periodically from main window
        pass