#!/usr/bin/env python3
"""
Table Widgets
"""

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *


class BotTable(QTableWidget):
    """Specialized table for bots"""
    
    def __init__(self):
        super().__init__()
        self.init_table()
        
    def init_table(self):
        self.setColumnCount(6)
        self.setHorizontalHeaderLabels([
            "ID", "IP Address", "OS", "Country", "Status", "Last Seen"
        ])
        
        # Style
        self.setStyleSheet("""
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
        """)
        
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.horizontalHeader().setStretchLastSection(True)
        self.setSortingEnabled(True)


class LogTable(QTableWidget):
    """Specialized table for logs"""
    
    def __init__(self):
        super().__init__()
        self.init_table()
        
    def init_table(self):
        self.setColumnCount(4)
        self.setHorizontalHeaderLabels([
            "Timestamp", "Level", "Source", "Message"
        ])
        
        # Style
        self.setStyleSheet("""
            QTableWidget {
                gridline-color: #bdc3c7;
                background-color: white;
                alternate-background-color: #ecf0f1;
                border: 1px solid #bdc3c7;
                border-radius: 5px;
                font-family: 'Consolas', monospace;
            }
            QTableWidget::item {
                padding: 6px;
                font-size: 11px;
            }
            QHeaderView::section {
                background-color: #2c3e50;
                color: white;
                padding: 8px;
                border: none;
                font-weight: bold;
            }
        """)
        
        self.setAlternatingRowColors(True)
        self.horizontalHeader().setStretchLastSection(True)
        self.setSortingEnabled(True)


class ScanTable(QTableWidget):
    """Specialized table for scan results"""
    
    def __init__(self):
        super().__init__()
        self.init_table()
        
    def init_table(self):
        self.setColumnCount(6)
        self.setHorizontalHeaderLabels([
            "IP Address", "Hostname", "OS", "Open Ports", "Services", "Status"
        ])
        
        # Style
        self.setStyleSheet("""
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
            }
            QHeaderView::section {
                background-color: #34495e;
                color: white;
                padding: 8px;
                border: none;
                font-weight: bold;
            }
        """)
        
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.horizontalHeader().setStretchLastSection(True)
        self.setSortingEnabled(True)