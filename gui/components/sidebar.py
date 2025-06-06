#!/usr/bin/env python3
"""
Modern Sidebar Component
"""

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *


class ModernSidebar(QWidget):
    """Sidebar hiện đại với animation và icons"""
    
    page_changed = pyqtSignal(str)  # Signal khi thay đổi page
    
    def __init__(self):
        super().__init__()
        self.expanded = True
        self.current_button = None
        
        # Animation
        self.animation = QPropertyAnimation(self, b"maximumWidth")
        self.animation.setDuration(300)
        self.animation.setEasingCurve(QEasingCurve.OutCubic)
        
        self.init_ui()
        
    def init_ui(self):
        """Khởi tạo giao diện sidebar"""
        self.setFixedWidth(250)
        self.setMaximumWidth(250)
        self.setMinimumWidth(60)
        
        # Styling
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
            ("🤖", "Bot Management", "bots"),
            ("📊", "Monitoring", "monitoring"),
            ("🔍", "Network Scanner", "scanner"),
            ("⚙️", "Payload Builder", "payload"),
            ("📝", "Logs", "logs"),
            ("🔧", "Settings", "settings")
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
        
        # Set default selection
        if self.buttons:
            self.set_active_button(self.buttons[0])
        
    def create_header(self):
        """Tạo header với logo và toggle button"""
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
        
        # Logo
        logo_label = QLabel("🤖")
        logo_label.setStyleSheet("""
            QLabel {
                font-size: 24px;
                color: #f39c12;
            }
        """)
        
        # Title
        title_label = QLabel("C2C Control")
        title_label.setStyleSheet("""
            QLabel {
                color: #ecf0f1;
                font-weight: bold;
                font-size: 14px;
            }
        """)
        
        # Toggle button
        self.toggle_btn = QPushButton("☰")
        self.toggle_btn.setFixedSize(30, 30)
        self.toggle_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: 1px solid rgba(255, 255, 255, 0.3);
                border-radius: 5px;
                color: #ecf0f1;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: rgba(52, 152, 219, 0.3);
                border: 1px solid #3498db;
            }
            QPushButton:pressed {
                background: rgba(52, 152, 219, 0.5);
            }
        """)
        self.toggle_btn.clicked.connect(self.toggle_sidebar)
        
        layout.addWidget(logo_label)
        layout.addWidget(title_label)
        layout.addStretch()
        layout.addWidget(self.toggle_btn)
        
        header.setLayout(layout)
        return header
        
    def create_menu_button(self, icon, text, action):
        """Tạo menu button"""
        btn = QPushButton()
        btn.setFixedHeight(50)
        btn.setCursor(Qt.PointingHandCursor)
        
        # Layout cho button
        layout = QHBoxLayout()
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(10)
        
        # Icon
        icon_label = QLabel(icon)
        icon_label.setFixedSize(24, 24)
        icon_label.setStyleSheet("""
            QLabel {
                font-size: 18px;
                color: #bdc3c7;
            }
        """)
        icon_label.setAlignment(Qt.AlignCenter)
        
        # Text
        text_label = QLabel(text)
        text_label.setStyleSheet("""
            QLabel {
                color: #bdc3c7;
                font-weight: 500;
                font-size: 13px;
            }
        """)
        
        layout.addWidget(icon_label)
        layout.addWidget(text_label)
        layout.addStretch()
        
        # Widget container
        widget = QWidget()
        widget.setLayout(layout)
        
        # Button layout
        btn_layout = QVBoxLayout()
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.addWidget(widget)
        btn.setLayout(btn_layout)
        
        # Styling
        btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                text-align: left;
                border-radius: 8px;
                margin: 2px;
            }
            QPushButton:hover {
                background: rgba(52, 152, 219, 0.2);
                border-left: 3px solid #3498db;
            }
        """)
        
        # Store action and connect
        btn.action = action
        btn.icon_label = icon_label
        btn.text_label = text_label
        btn.clicked.connect(lambda: self.on_menu_clicked(btn))
        
        return btn
        
    def create_footer(self):
        """Tạo footer với thông tin version"""
        footer = QWidget()
        footer.setFixedHeight(40)
        footer.setStyleSheet("""
            QWidget {
                background: rgba(0, 0, 0, 0.2);
                border-top: 1px solid rgba(255, 255, 255, 0.1);
            }
        """)
        
        layout = QHBoxLayout()
        layout.setContentsMargins(15, 10, 15, 10)
        
        version_label = QLabel("v1.0.0")
        version_label.setStyleSheet("""
            QLabel {
                color: #95a5a6;
                font-size: 11px;
                font-weight: 500;
            }
        """)
        
        layout.addWidget(version_label)
        layout.addStretch()
        
        footer.setLayout(layout)
        return footer
        
    def toggle_sidebar(self):
        """Toggle sidebar expand/collapse"""
        if self.expanded:
            # Collapse
            self.animation.setStartValue(250)
            self.animation.setEndValue(60)
            self.expanded = False
            
            # Hide text labels
            for btn in self.buttons:
                btn.text_label.hide()
                
        else:
            # Expand
            self.animation.setStartValue(60)
            self.animation.setEndValue(250)
            self.expanded = True
            
            # Show text labels
            for btn in self.buttons:
                btn.text_label.show()
                
        self.animation.start()
        
    def on_menu_clicked(self, button):
        """Xử lý khi click menu"""
        # Set active button
        self.set_active_button(button)
        
        # Emit signal
        self.page_changed.emit(button.action)
        
    def set_active_button(self, button):
        """Set button active"""
        # Reset all buttons
        for btn in self.buttons:
            btn.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    border: none;
                    text-align: left;
                    border-radius: 8px;
                    margin: 2px;
                }
                QPushButton:hover {
                    background: rgba(52, 152, 219, 0.2);
                    border-left: 3px solid #3498db;
                }
            """)
            btn.icon_label.setStyleSheet("""
                QLabel {
                    font-size: 18px;
                    color: #bdc3c7;
                }
            """)
            btn.text_label.setStyleSheet("""
                QLabel {
                    color: #bdc3c7;
                    font-weight: 500;
                    font-size: 13px;
                }
            """)
        
        # Set active button
        button.setStyleSheet("""
            QPushButton {
                background: rgba(52, 152, 219, 0.3);
                border: none;
                border-left: 3px solid #3498db;
                text-align: left;
                border-radius: 8px;
                margin: 2px;
            }
            QPushButton:hover {
                background: rgba(52, 152, 219, 0.4);
                border-left: 3px solid #3498db;
            }
        """)
        button.icon_label.setStyleSheet("""
            QLabel {
                font-size: 18px;
                color: #3498db;
            }
        """)
        button.text_label.setStyleSheet("""
            QLabel {
                color: #ecf0f1;
                font-weight: bold;
                font-size: 13px;
            }
        """)
        
        self.current_button = button
        
    def set_current_page(self, page_name):
        """Set trang hiện tại từ bên ngoài"""
        for btn in self.buttons:
            if btn.action == page_name:
                self.set_active_button(btn)
                break