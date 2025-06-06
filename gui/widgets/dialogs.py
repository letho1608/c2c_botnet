#!/usr/bin/env python3
"""
Dialog Widgets
"""

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *


class SettingsDialog(QDialog):
    """Settings configuration dialog"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setModal(True)
        self.resize(600, 400)
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Placeholder content
        label = QLabel("Settings Dialog\n(Implementation in settings.py)")
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                color: #2c3e50;
                padding: 20px;
            }
        """)
        
        layout.addWidget(label)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self.accept)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(ok_btn)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)


class AboutDialog(QDialog):
    """About application dialog"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("About")
        self.setModal(True)
        self.setFixedSize(400, 300)
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        # App icon/logo
        icon_label = QLabel("🤖")
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet("""
            QLabel {
                font-size: 48px;
                margin: 20px;
            }
        """)
        
        # App info
        info_text = """
        <h2>C2C Botnet Management System</h2>
        <p><b>Version:</b> 1.0.0</p>
        <p><b>Author:</b> Security Research Team</p>
        <p><b>Description:</b> Comprehensive botnet management platform</p>
        <br>
        <p><i>⚠️ For educational and research purposes only!</i></p>
        """
        
        info_label = QLabel(info_text)
        info_label.setAlignment(Qt.AlignCenter)
        info_label.setWordWrap(True)
        info_label.setStyleSheet("""
            QLabel {
                color: #2c3e50;
                font-size: 12px;
            }
        """)
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        close_btn.setStyleSheet("""
            QPushButton {
                background: #3498db;
                color: white;
                border: none;
                padding: 8px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #2980b9;
            }
        """)
        
        layout.addWidget(icon_label)
        layout.addWidget(info_label)
        layout.addStretch()
        layout.addWidget(close_btn, alignment=Qt.AlignCenter)
        
        self.setLayout(layout)


class ConfirmDialog(QDialog):
    """Generic confirmation dialog"""
    
    def __init__(self, title, message, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setFixedSize(350, 150)
        self.init_ui(message)
        
    def init_ui(self, message):
        layout = QVBoxLayout()
        
        # Icon and message
        content_layout = QHBoxLayout()
        
        icon_label = QLabel("❓")
        icon_label.setStyleSheet("font-size: 32px;")
        
        message_label = QLabel(message)
        message_label.setWordWrap(True)
        message_label.setStyleSheet("""
            QLabel {
                color: #2c3e50;
                font-size: 12px;
            }
        """)
        
        content_layout.addWidget(icon_label)
        content_layout.addWidget(message_label)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        yes_btn = QPushButton("Yes")
        yes_btn.setStyleSheet("""
            QPushButton {
                background: #27ae60;
                color: white;
                border: none;
                padding: 8px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #229954;
            }
        """)
        yes_btn.clicked.connect(self.accept)
        
        no_btn = QPushButton("No")
        no_btn.setStyleSheet("""
            QPushButton {
                background: #e74c3c;
                color: white;
                border: none;
                padding: 8px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #c0392b;
            }
        """)
        no_btn.clicked.connect(self.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(yes_btn)
        button_layout.addWidget(no_btn)
        
        layout.addLayout(content_layout)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)