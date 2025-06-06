#!/usr/bin/env python3
"""
Console Widget
"""

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import time


class ConsoleWidget(QWidget):
    """Console output widget"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.command_history = []
        self.history_index = 0
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Console output
        self.output_text = QTextEdit()
        self.output_text.setStyleSheet("""
            QTextEdit {
                background-color: #2c3e50;
                color: #ecf0f1;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 12px;
                border: 1px solid #34495e;
                border-radius: 5px;
                padding: 10px;
            }
        """)
        self.output_text.setReadOnly(True)
        
        # Command input
        input_layout = QHBoxLayout()
        
        prompt_label = QLabel("C2C >")
        prompt_label.setStyleSheet("""
            QLabel {
                color: #3498db;
                font-family: 'Consolas', monospace;
                font-weight: bold;
                font-size: 12px;
            }
        """)
        
        self.command_input = QLineEdit()
        self.command_input.setStyleSheet("""
            QLineEdit {
                background-color: #34495e;
                color: #ecf0f1;
                font-family: 'Consolas', monospace;
                font-size: 12px;
                border: 1px solid #3498db;
                border-radius: 3px;
                padding: 5px;
            }
            QLineEdit:focus {
                border: 2px solid #3498db;
            }
        """)
        self.command_input.returnPressed.connect(self.execute_command)
        self.command_input.keyPressEvent = self.handle_key_press
        
        input_layout.addWidget(prompt_label)
        input_layout.addWidget(self.command_input)
        
        layout.addWidget(self.output_text)
        layout.addLayout(input_layout)
        
        self.setLayout(layout)
        
        # Add welcome message
        self.add_output("🤖 C2C Botnet Management Console")
        self.add_output("Type 'help' for available commands")
        self.add_output("")
        
    def handle_key_press(self, event):
        """Handle special key presses"""
        if event.key() == Qt.Key_Up:
            # Previous command
            if self.command_history and self.history_index > 0:
                self.history_index -= 1
                self.command_input.setText(self.command_history[self.history_index])
        elif event.key() == Qt.Key_Down:
            # Next command
            if self.command_history and self.history_index < len(self.command_history) - 1:
                self.history_index += 1
                self.command_input.setText(self.command_history[self.history_index])
            elif self.history_index >= len(self.command_history) - 1:
                self.command_input.clear()
        else:
            # Default handling
            QLineEdit.keyPressEvent(self.command_input, event)
            
    def execute_command(self):
        """Execute entered command"""
        command = self.command_input.text().strip()
        if not command:
            return
            
        # Add to history
        if command not in self.command_history:
            self.command_history.append(command)
        self.history_index = len(self.command_history)
        
        # Display command
        self.add_output(f"C2C > {command}", color="#3498db")
        
        # Process command
        self.process_command(command)
        
        # Clear input
        self.command_input.clear()
        
    def process_command(self, command):
        """Process console command"""
        parts = command.lower().split()
        if not parts:
            return
            
        cmd = parts[0]
        args = parts[1:] if len(parts) > 1 else []
        
        if cmd == "help":
            self.show_help()
        elif cmd == "list":
            self.list_bots()
        elif cmd == "status":
            self.show_status()
        elif cmd == "clear":
            self.clear_console()
        elif cmd == "exit" or cmd == "quit":
            self.add_output("Use the X button to close the console")
        elif cmd == "info":
            if args:
                self.show_bot_info(args[0])
            else:
                self.add_output("Usage: info <bot_id>", color="#e74c3c")
        elif cmd == "shell":
            if len(args) >= 2:
                self.execute_bot_command(args[0], " ".join(args[1:]))
            else:
                self.add_output("Usage: shell <bot_id> <command>", color="#e74c3c")
        else:
            self.add_output(f"Unknown command: {cmd}", color="#e74c3c")
            self.add_output("Type 'help' for available commands")
            
    def show_help(self):
        """Show help information"""
        help_text = """
Available Commands:
═══════════════════════════════════════
help                    - Show this help
list                    - List connected bots
status                  - Show server status
info <bot_id>          - Show bot information
shell <bot_id> <cmd>   - Execute command on bot
clear                   - Clear console
exit/quit              - Exit console

Examples:
═══════════════════════════════════════
list
info BOT001
shell BOT001 whoami
shell BOT001 systeminfo
"""
        self.add_output(help_text, color="#f39c12")
        
    def list_bots(self):
        """List connected bots"""
        self.add_output("Connected Bots:", color="#2ecc71")
        self.add_output("═" * 50)
        
        # Mock data
        bots = [
            ("BOT001", "192.168.1.100", "Windows 10", "Online"),
            ("BOT002", "192.168.1.101", "Ubuntu 20.04", "Online"),
            ("BOT003", "10.0.0.50", "Windows Server", "Idle"),
        ]
        
        for bot_id, ip, os_info, status in bots:
            status_color = "#2ecc71" if status == "Online" else "#f39c12"
            self.add_output(f"{bot_id:<8} {ip:<15} {os_info:<15} {status}", color=status_color)
            
    def show_status(self):
        """Show server status"""
        self.add_output("Server Status:", color="#3498db")
        self.add_output("═" * 30)
        self.add_output("Status: Online", color="#2ecc71")
        self.add_output("Connected Bots: 3")
        self.add_output("Uptime: 2h 45m")
        self.add_output("Port: 4444")
        self.add_output("SSL: Enabled")
        
    def show_bot_info(self, bot_id):
        """Show bot information"""
        self.add_output(f"Bot Information: {bot_id}", color="#9b59b6")
        self.add_output("═" * 40)
        
        # Mock data
        if bot_id.upper() == "BOT001":
            info = {
                "IP Address": "192.168.1.100",
                "Hostname": "WORKSTATION-01",
                "OS": "Windows 10 Pro",
                "CPU": "Intel Core i7-10700K",
                "RAM": "16 GB",
                "Status": "Online",
                "Last Seen": "2 minutes ago"
            }
            
            for key, value in info.items():
                self.add_output(f"{key}: {value}")
        else:
            self.add_output(f"Bot {bot_id} not found", color="#e74c3c")
            
    def execute_bot_command(self, bot_id, command):
        """Execute command on bot"""
        self.add_output(f"Executing on {bot_id}: {command}", color="#e67e22")
        
        # Simulate command execution
        QTimer.singleShot(1000, lambda: self.add_output("Command sent successfully", color="#2ecc71"))
        QTimer.singleShot(2000, lambda: self.add_output("Response: Command executed", color="#95a5a6"))
        
    def clear_console(self):
        """Clear console output"""
        self.output_text.clear()
        self.add_output("Console cleared")
        
    def add_output(self, text, color="#ecf0f1"):
        """Add text to console output"""
        timestamp = time.strftime("[%H:%M:%S]")
        
        # Format with color
        formatted_text = f'<span style="color: #7f8c8d;">{timestamp}</span> <span style="color: {color};">{text}</span>'
        
        # Add to output
        cursor = self.output_text.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertHtml(formatted_text + "<br>")
        
        # Auto-scroll to bottom
        scrollbar = self.output_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        
    def add_error(self, text):
        """Add error message"""
        self.add_output(f"ERROR: {text}", color="#e74c3c")
        
    def add_success(self, text):
        """Add success message"""
        self.add_output(f"SUCCESS: {text}", color="#2ecc71")
        
    def add_warning(self, text):
        """Add warning message"""
        self.add_output(f"WARNING: {text}", color="#f39c12")