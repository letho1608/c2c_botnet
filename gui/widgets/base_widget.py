#!/usr/bin/env python3
"""
Base Widget Class
"""

from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import QTimer


class BaseWidget(QWidget):
    """Base widget class cho tất cả các widget"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.update_timer = None
        
    def start_updates(self, interval=5000):
        """Bắt đầu auto-update"""
        if self.update_timer is None:
            self.update_timer = QTimer()
            self.update_timer.timeout.connect(self.update_data)
            
        self.update_timer.start(interval)
        
    def stop_updates(self):
        """Dừng auto-update"""
        if self.update_timer:
            self.update_timer.stop()
            
    def update_data(self):
        """Override method này để implement update logic"""
        pass
        
    def get_common_styles(self):
        """Lấy common styles"""
        return {
            'group_box': """
                QGroupBox {
                    font-weight: bold;
                    font-size: 14px;
                    border: 2px solid {color};
                    border-radius: 10px;
                    margin-top: 10px;
                    padding-top: 10px;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 10px;
                    padding: 0 5px 0 5px;
                    color: {color};
                }
            """,
            'input': """
                QLineEdit, QTextEdit, QSpinBox {
                    border: 1px solid #bdc3c7;
                    border-radius: 5px;
                    padding: 8px;
                    background: white;
                    font-size: 12px;
                }
                QLineEdit:focus, QTextEdit:focus, QSpinBox:focus {
                    border: 2px solid #3498db;
                }
            """,
            'button': """
                QPushButton {
                    background: {color};
                    color: white;
                    border: none;
                    padding: 10px 15px;
                    border-radius: 8px;
                    font-weight: bold;
                    font-size: 12px;
                }
                QPushButton:hover {
                    background: {hover_color};
                }
                QPushButton:pressed {
                    background: {pressed_color};
                }
            """,
            'table': """
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
                    font-size: 12px;
                }
                QHeaderView::section {
                    background-color: #34495e;
                    color: white;
                    padding: 8px;
                    border: none;
                    font-weight: bold;
                }
            """
        }