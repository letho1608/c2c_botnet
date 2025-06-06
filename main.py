#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
C2C Botnet Management System - Main Entry Point
Modular GUI Application
"""

import sys
import os

# Set Qt attributes BEFORE creating QApplication
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication

# Must set these attributes before QApplication is created
QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

# Thêm thư mục hiện tại vào Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt5.QtGui import QIcon

# Import GUI module
from gui import MainWindow

def setup_application():
    """Thiết lập application"""
    app = QApplication(sys.argv)
    
    # Application properties
    app.setApplicationName("C2C Botnet Management System")
    app.setApplicationDisplayName("C2C Control Panel")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("C2C Security Research")
    app.setOrganizationDomain("c2c.local")
    
    # Set application icon nếu có
    if os.path.exists("assets/icon.png"):
        app.setWindowIcon(QIcon("assets/icon.png"))
    
    return app

def main():
    """Main function"""
    try:
        # Tạo application
        app = setup_application()
        
        print("Starting C2C Botnet Management System")
        print("Initializing main window...")
        
        # Tạo main window
        window = MainWindow()
        
        # Hiển thị window
        window.show()
        print("Application started successfully!")
        print("GUI ready for use")
        
        # Start event loop
        return app.exec_()
        
    except ImportError as e:
        print(f"Import Error: {e}")
        print("Please install required dependencies:")
        print("   pip install PyQt5 PyQt5-tools")
        print("   pip install psutil")
        return 1
        
    except Exception as e:
        print(f"Application Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
