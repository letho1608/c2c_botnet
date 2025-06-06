#!/usr/bin/env python3
"""
Logs Widget Component
"""

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import time
import random


class LogsWidget(QWidget):
    """Widget hiển thị logs"""
    
    def __init__(self):
        super().__init__()
        
        self.init_ui()
        self.init_sample_logs()
        
    def init_ui(self):
        """Khởi tạo giao diện logs"""
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Title
        title = QLabel("📝 System Logs")
        title.setStyleSheet("""
            QLabel {
                font-size: 28px;
                font-weight: bold;
                color: #2c3e50;
                margin-bottom: 10px;
            }
        """)
        layout.addWidget(title)
        
        # Filter and search toolbar
        toolbar_layout = QHBoxLayout()
        
        # Log level filter
        level_label = QLabel("Level:")
        level_label.setStyleSheet("font-weight: bold; color: #2c3e50;")
        
        self.level_combo = QComboBox()
        self.level_combo.addItems(["All", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        self.level_combo.setStyleSheet(self.get_combo_style())
        self.level_combo.currentTextChanged.connect(self.filter_logs)
        
        # Category filter
        category_label = QLabel("Category:")
        category_label.setStyleSheet("font-weight: bold; color: #2c3e50;")
        
        self.category_combo = QComboBox()
        self.category_combo.addItems([
            "All", "System", "Network", "Bot", "Command", "Security", "Error"
        ])
        self.category_combo.setStyleSheet(self.get_combo_style())
        self.category_combo.currentTextChanged.connect(self.filter_logs)
        
        # Search box
        search_label = QLabel("Search:")
        search_label.setStyleSheet("font-weight: bold; color: #2c3e50;")
        
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search logs...")
        self.search_edit.setStyleSheet(self.get_input_style())
        self.search_edit.textChanged.connect(self.filter_logs)
        
        # Control buttons
        clear_btn = QPushButton("🗑️ Clear")
        clear_btn.setStyleSheet(self.get_button_style("#e74c3c"))
        clear_btn.clicked.connect(self.clear_logs)
        
        export_btn = QPushButton("📄 Export")
        export_btn.setStyleSheet(self.get_button_style("#3498db"))
        export_btn.clicked.connect(self.export_logs)
        
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.setStyleSheet(self.get_button_style("#2ecc71"))
        refresh_btn.clicked.connect(self.refresh_logs)
        
        toolbar_layout.addWidget(level_label)
        toolbar_layout.addWidget(self.level_combo)
        toolbar_layout.addWidget(category_label)
        toolbar_layout.addWidget(self.category_combo)
        toolbar_layout.addWidget(search_label)
        toolbar_layout.addWidget(self.search_edit)
        toolbar_layout.addStretch()
        toolbar_layout.addWidget(clear_btn)
        toolbar_layout.addWidget(export_btn)
        toolbar_layout.addWidget(refresh_btn)
        
        layout.addLayout(toolbar_layout)
        
        # Logs display
        logs_splitter = QSplitter(Qt.Vertical)
        
        # Main logs table
        self.create_logs_table()
        logs_splitter.addWidget(self.logs_table_widget)
        
        # Log details
        self.create_log_details()
        logs_splitter.addWidget(self.details_widget)
        
        logs_splitter.setSizes([400, 200])
        layout.addWidget(logs_splitter)
        
        self.setLayout(layout)
        
    def create_logs_table(self):
        """Tạo bảng logs"""
        self.logs_table_widget = QWidget()
        layout = QVBoxLayout()
        
        # Statistics
        stats_layout = QHBoxLayout()
        
        self.total_logs_label = QLabel("Total: 0")
        self.total_logs_label.setStyleSheet("color: #2c3e50; font-weight: bold;")
        
        self.errors_label = QLabel("Errors: 0")
        self.errors_label.setStyleSheet("color: #e74c3c; font-weight: bold;")
        
        self.warnings_label = QLabel("Warnings: 0")
        self.warnings_label.setStyleSheet("color: #f39c12; font-weight: bold;")
        
        self.info_label = QLabel("Info: 0")
        self.info_label.setStyleSheet("color: #3498db; font-weight: bold;")
        
        stats_layout.addWidget(self.total_logs_label)
        stats_layout.addWidget(self.errors_label)
        stats_layout.addWidget(self.warnings_label)
        stats_layout.addWidget(self.info_label)
        stats_layout.addStretch()
        
        layout.addLayout(stats_layout)
        
        # Logs table
        self.logs_table = QTableWidget()
        self.logs_table.setColumnCount(5)
        self.logs_table.setHorizontalHeaderLabels([
            "Timestamp", "Level", "Category", "Source", "Message"
        ])
        
        self.logs_table.setStyleSheet("""
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
                font-family: 'Consolas', monospace;
            }
            QHeaderView::section {
                background-color: #34495e;
                color: white;
                padding: 8px;
                border: none;
                font-weight: bold;
            }
        """)
        
        self.logs_table.setAlternatingRowColors(True)
        self.logs_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.logs_table.horizontalHeader().setStretchLastSection(True)
        self.logs_table.setSortingEnabled(True)
        
        # Connect selection
        self.logs_table.itemSelectionChanged.connect(self.on_log_selected)
        
        layout.addWidget(self.logs_table)
        self.logs_table_widget.setLayout(layout)
        
    def create_log_details(self):
        """Tạo panel chi tiết log"""
        self.details_widget = QGroupBox("📋 Log Details")
        self.details_widget.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 14px;
                border: 2px solid #9b59b6;
                border-radius: 10px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #9b59b6;
            }
        """)
        
        layout = QVBoxLayout()
        
        # Log detail text
        self.detail_text = QTextEdit()
        self.detail_text.setStyleSheet("""
            QTextEdit {
                border: 1px solid #bdc3c7;
                border-radius: 5px;
                background: #f8f9fa;
                font-family: 'Consolas', monospace;
                font-size: 11px;
                padding: 10px;
            }
        """)
        self.detail_text.setPlainText("Select a log entry to view details...")
        self.detail_text.setMaximumHeight(150)
        
        layout.addWidget(self.detail_text)
        self.details_widget.setLayout(layout)
        
    def get_combo_style(self):
        """Lấy style cho combobox"""
        return """
            QComboBox {
                border: 1px solid #bdc3c7;
                border-radius: 5px;
                padding: 5px;
                background: white;
                font-size: 12px;
                min-width: 80px;
            }
            QComboBox:hover {
                border: 2px solid #3498db;
            }
        """
        
    def get_input_style(self):
        """Lấy style cho input fields"""
        return """
            QLineEdit {
                border: 1px solid #bdc3c7;
                border-radius: 5px;
                padding: 5px;
                background: white;
                font-size: 12px;
                min-width: 200px;
            }
            QLineEdit:focus {
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
                padding: 8px 12px;
                border-radius: 5px;
                font-weight: bold;
                font-size: 11px;
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
        
    def init_sample_logs(self):
        """Khởi tạo dữ liệu logs mẫu"""
        sample_logs = [
            ("INFO", "System", "Server", "Server started successfully on port 4444"),
            ("INFO", "Network", "Connection", "New client connected from 192.168.1.100"),
            ("DEBUG", "Bot", "BOT001", "Heartbeat received from bot"),
            ("INFO", "Command", "BOT001", "Screenshot command executed successfully"),
            ("WARNING", "Security", "System", "Multiple failed login attempts detected"),
            ("ERROR", "Network", "Connection", "Failed to connect to backup server"),
            ("INFO", "Bot", "BOT002", "Bot registered with ID: BOT002"),
            ("DEBUG", "System", "Database", "Database connection established"),
            ("WARNING", "Bot", "BOT003", "Bot connection timeout, attempting reconnect"),
            ("CRITICAL", "Security", "System", "Potential intrusion detected from 203.0.113.45"),
            ("INFO", "Command", "BOT001", "Keylogger started successfully"),
            ("ERROR", "System", "FileSystem", "Failed to write log file: permission denied"),
            ("INFO", "Network", "Scanner", "Network scan completed: 25 hosts found"),
            ("WARNING", "Bot", "BOT004", "Bot report anomalous behavior"),
            ("INFO", "System", "Cleanup", "Cleanup task completed: 150 MB freed"),
        ]
        
        self.logs_table.setRowCount(len(sample_logs))
        
        for row, (level, category, source, message) in enumerate(sample_logs):
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S", 
                                    time.localtime(time.time() - (len(sample_logs) - row) * 60))
            
            items = [timestamp, level, category, source, message]
            
            for col, item_text in enumerate(items):
                item = QTableWidgetItem(str(item_text))
                
                # Color code by level
                if col == 1:  # Level column
                    if level == "CRITICAL":
                        item.setForeground(QColor("#8e44ad"))
                        item.setBackground(QColor("#f8d7da"))
                    elif level == "ERROR":
                        item.setForeground(QColor("#e74c3c"))
                    elif level == "WARNING":
                        item.setForeground(QColor("#f39c12"))
                    elif level == "INFO":
                        item.setForeground(QColor("#3498db"))
                    elif level == "DEBUG":
                        item.setForeground(QColor("#95a5a6"))
                        
                self.logs_table.setItem(row, col, item)
                
        # Update statistics
        self.update_statistics()
        
        # Resize columns
        self.logs_table.resizeColumnsToContents()
        
    def update_statistics(self):
        """Cập nhật thống kê logs"""
        total = self.logs_table.rowCount()
        errors = 0
        warnings = 0
        info = 0
        
        for row in range(total):
            level_item = self.logs_table.item(row, 1)
            if level_item:
                level = level_item.text()
                if level in ["ERROR", "CRITICAL"]:
                    errors += 1
                elif level == "WARNING":
                    warnings += 1
                elif level == "INFO":
                    info += 1
                    
        self.total_logs_label.setText(f"Total: {total}")
        self.errors_label.setText(f"Errors: {errors}")
        self.warnings_label.setText(f"Warnings: {warnings}")
        self.info_label.setText(f"Info: {info}")
        
    def filter_logs(self):
        """Lọc logs theo filter"""
        level_filter = self.level_combo.currentText()
        category_filter = self.category_combo.currentText()
        search_text = self.search_edit.text().lower()
        
        for row in range(self.logs_table.rowCount()):
            show_row = True
            
            # Level filter
            if level_filter != "All":
                level_item = self.logs_table.item(row, 1)
                if level_item and level_item.text() != level_filter:
                    show_row = False
                    
            # Category filter
            if category_filter != "All" and show_row:
                category_item = self.logs_table.item(row, 2)
                if category_item and category_item.text() != category_filter:
                    show_row = False
                    
            # Search filter
            if search_text and show_row:
                row_text = ""
                for col in range(self.logs_table.columnCount()):
                    item = self.logs_table.item(row, col)
                    if item:
                        row_text += item.text().lower() + " "
                        
                if search_text not in row_text:
                    show_row = False
                    
            self.logs_table.setRowHidden(row, not show_row)
            
    def on_log_selected(self):
        """Xử lý khi chọn log"""
        selected_rows = set()
        for item in self.logs_table.selectedItems():
            selected_rows.add(item.row())
            
        if selected_rows:
            row = list(selected_rows)[0]
            
            timestamp = self.logs_table.item(row, 0).text()
            level = self.logs_table.item(row, 1).text()
            category = self.logs_table.item(row, 2).text()
            source = self.logs_table.item(row, 3).text()
            message = self.logs_table.item(row, 4).text()
            
            details = f"""Log Entry Details:
════════════════════════════════════════
Timestamp: {timestamp}
Level: {level}
Category: {category}
Source: {source}
Message: {message}

Extended Information:
════════════════════════════════════════
Thread ID: 12345
Process ID: 6789
Memory Usage: 45.2 MB
CPU Usage: 2.1%

Stack Trace (if applicable):
════════════════════════════════════════
File "/opt/c2c/server.py", line 123, in handle_client
    response = process_command(command)
File "/opt/c2c/commands.py", line 45, in process_command
    return execute_command(cmd_type, cmd_data)
File "/opt/c2c/executor.py", line 78, in execute_command
    result = getattr(self, f"cmd_{cmd_type}")(cmd_data)

Related Events:
════════════════════════════════════════
• Previous event: Bot connection established
• Next event: Command response sent
• Error count in last hour: 3
• Similar events today: 15

Recommendations:
════════════════════════════════════════
• Monitor bot connection stability
• Check network connectivity
• Review command execution logs
• Update bot software if needed
"""
            
            self.detail_text.setPlainText(details)
        else:
            self.detail_text.setPlainText("Select a log entry to view details...")
            
    def add_log_entry(self, level, category, source, message):
        """Thêm log entry mới"""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        
        row = self.logs_table.rowCount()
        self.logs_table.insertRow(0)  # Insert at top
        
        items = [timestamp, level, category, source, message]
        
        for col, item_text in enumerate(items):
            item = QTableWidgetItem(str(item_text))
            
            # Color code by level
            if col == 1:  # Level column
                if level == "CRITICAL":
                    item.setForeground(QColor("#8e44ad"))
                    item.setBackground(QColor("#f8d7da"))
                elif level == "ERROR":
                    item.setForeground(QColor("#e74c3c"))
                elif level == "WARNING":
                    item.setForeground(QColor("#f39c12"))
                elif level == "INFO":
                    item.setForeground(QColor("#3498db"))
                elif level == "DEBUG":
                    item.setForeground(QColor("#95a5a6"))
                    
            self.logs_table.setItem(0, col, item)
            
        # Keep only last 1000 entries
        while self.logs_table.rowCount() > 1000:
            self.logs_table.removeRow(self.logs_table.rowCount() - 1)
            
        # Update statistics
        self.update_statistics()
        
    def clear_logs(self):
        """Xóa tất cả logs"""
        reply = QMessageBox.question(
            self, 'Clear Logs',
            'Are you sure you want to clear all log entries?',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.logs_table.setRowCount(0)
            self.detail_text.setPlainText("Logs cleared.")
            self.update_statistics()
            
    def export_logs(self):
        """Export logs"""
        if self.logs_table.rowCount() == 0:
            QMessageBox.warning(self, "Warning", "No logs to export!")
            return
            
        filename, _ = QFileDialog.getSaveFileName(
            self, 'Export Logs', 
            f'logs_{int(time.time())}.csv',
            'CSV Files (*.csv);;Text Files (*.txt)'
        )
        
        if filename:
            # Simulate export
            QMessageBox.information(self, "Export", f"Logs exported to {filename}")
            
    def refresh_logs(self):
        """Refresh logs"""
        # Add some new sample logs
        new_logs = [
            ("INFO", "System", "Server", "System refresh completed"),
            ("DEBUG", "Network", "Monitor", "Network status checked"),
            ("INFO", "Bot", f"BOT{random.randint(1,10):03d}", "Bot status updated"),
        ]
        
        for level, category, source, message in new_logs:
            self.add_log_entry(level, category, source, message)
            
        QMessageBox.information(self, "Refresh", "Logs refreshed successfully!")
        
    def update_data(self):
        """Update data (called from main window)"""
        # Occasionally add new log entries
        if random.random() < 0.3:  # 30% chance
            levels = ["INFO", "DEBUG", "WARNING", "ERROR"]
            categories = ["System", "Network", "Bot", "Command", "Security"]
            sources = ["Server", "Bot001", "Bot002", "Network", "Scanner"]
            messages = [
                "Operation completed successfully",
                "Connection established",
                "Command executed",
                "Status updated",
                "Heartbeat received"
            ]
            
            level = random.choice(levels)
            category = random.choice(categories)
            source = random.choice(sources)
            message = random.choice(messages)
            
            self.add_log_entry(level, category, source, message)