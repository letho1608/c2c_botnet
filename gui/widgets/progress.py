#!/usr/bin/env python3
"""
Progress Widgets
"""

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *


class ProgressWidget(QWidget):
    """Enhanced progress widget with label and percentage"""
    
    def __init__(self, title="Progress", parent=None):
        super().__init__(parent)
        self.title = title
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Title
        self.title_label = QLabel(self.title)
        self.title_label.setStyleSheet("""
            QLabel {
                font-weight: bold;
                color: #2c3e50;
                font-size: 14px;
            }
        """)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #3498db;
                border-radius: 8px;
                text-align: center;
                font-weight: bold;
                background: #ecf0f1;
                height: 25px;
            }
            QProgressBar::chunk {
                background-color: #3498db;
                border-radius: 6px;
                margin: 1px;
            }
        """)
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        
        # Status label
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("""
            QLabel {
                color: #7f8c8d;
                font-size: 12px;
            }
        """)
        
        layout.addWidget(self.title_label)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.status_label)
        
        self.setLayout(layout)
        
    def set_progress(self, value, status=""):
        """Set progress value and status"""
        self.progress_bar.setValue(value)
        if status:
            self.status_label.setText(status)
            
    def set_title(self, title):
        """Set progress title"""
        self.title = title
        self.title_label.setText(title)
        
    def reset(self):
        """Reset progress"""
        self.progress_bar.setValue(0)
        self.status_label.setText("Ready")


class CircularProgress(QWidget):
    """Circular progress indicator"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.value = 0
        self.setFixedSize(100, 100)
        
    def set_value(self, value):
        """Set progress value (0-100)"""
        self.value = max(0, min(100, value))
        self.update()
        
    def paintEvent(self, event):
        """Paint the circular progress"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Background circle
        painter.setPen(QPen(QColor("#ecf0f1"), 8))
        painter.drawEllipse(10, 10, 80, 80)
        
        # Progress arc
        painter.setPen(QPen(QColor("#3498db"), 8, Qt.SolidLine, Qt.RoundCap))
        
        # Calculate angle (0-360 degrees, starting from top)
        angle = int(360 * self.value / 100)
        painter.drawArc(10, 10, 80, 80, 90 * 16, -angle * 16)
        
        # Center text
        painter.setPen(QColor("#2c3e50"))
        painter.setFont(QFont("Arial", 12, QFont.Bold))
        painter.drawText(self.rect(), Qt.AlignCenter, f"{self.value}%")


class TaskProgress(QWidget):
    """Task progress with multiple steps"""
    
    def __init__(self, tasks=None, parent=None):
        super().__init__(parent)
        self.tasks = tasks or []
        self.current_task = 0
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Overall progress
        self.overall_progress = QProgressBar()
        self.overall_progress.setStyleSheet("""
            QProgressBar {
                border: 2px solid #2ecc71;
                border-radius: 8px;
                text-align: center;
                font-weight: bold;
                background: #ecf0f1;
                height: 30px;
            }
            QProgressBar::chunk {
                background-color: #2ecc71;
                border-radius: 6px;
                margin: 1px;
            }
        """)
        
        # Task list
        self.task_list = QListWidget()
        self.task_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #bdc3c7;
                border-radius: 5px;
                background: white;
                font-size: 12px;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #ecf0f1;
            }
        """)
        self.task_list.setMaximumHeight(150)
        
        # Add tasks to list
        for i, task in enumerate(self.tasks):
            item = QListWidgetItem(f"⏳ {task}")
            self.task_list.addItem(item)
            
        layout.addWidget(QLabel("Overall Progress:"))
        layout.addWidget(self.overall_progress)
        layout.addWidget(QLabel("Tasks:"))
        layout.addWidget(self.task_list)
        
        self.setLayout(layout)
        
    def set_task_progress(self, task_index, completed=False):
        """Set progress for specific task"""
        if 0 <= task_index < len(self.tasks):
            item = self.task_list.item(task_index)
            if completed:
                item.setText(f"✅ {self.tasks[task_index]}")
                item.setForeground(QColor("#27ae60"))
            else:
                item.setText(f"🔄 {self.tasks[task_index]}")
                item.setForeground(QColor("#3498db"))
                
        # Update overall progress
        completed_tasks = sum(1 for i in range(len(self.tasks)) 
                            if self.task_list.item(i).text().startswith("✅"))
        progress = int(completed_tasks / len(self.tasks) * 100) if self.tasks else 0
        self.overall_progress.setValue(progress)
        
    def complete_task(self, task_index):
        """Mark task as completed"""
        self.set_task_progress(task_index, True)
        
    def start_task(self, task_index):
        """Mark task as in progress"""
        self.set_task_progress(task_index, False)
        
    def reset(self):
        """Reset all tasks"""
        for i, task in enumerate(self.tasks):
            item = self.task_list.item(i)
            item.setText(f"⏳ {task}")
            item.setForeground(QColor("#7f8c8d"))
        self.overall_progress.setValue(0)