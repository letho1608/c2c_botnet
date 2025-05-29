from __future__ import annotations
import os
import sys
import time
import uuid
import ctypes
import logging
import platform 
import win32api
import wmi
import psutil
import winreg
from typing import List, Set, Dict, Optional
from pathlib import Path
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
import joblib
import hashlib
import threading

class AntiVM:
    def __init__(self) -> None:
        """Initialize advanced anti-analysis system with AI"""
        self.logger = logging.getLogger('security')
        self.wmi = wmi.WMI()
        self._init_timing_baseline()
        self._setup_hardware_fingerprint()
        
        # AI-Enhanced Detection System
        self.ai_detector = self._init_ai_detector()
        self.feature_cache = {}
        self.detection_history = []
        self._detection_lock = threading.Lock()
        
        # Dynamic learning system
        self.learning_enabled = True
        self.confidence_threshold = 0.7
        self.false_positive_tolerance = 0.05
        
        # Extended VM signatures
        self.vm_services = {
            'vboxservice',
            'vmtoolsd',
            'vmwaretray',
            'vmwareuser',
            'vgauthservice',
            'vmacthlp',
            'vboxtray',
            'sandboxie',
            'wireshark',
            'fiddler',
            'processhacker',
            'ollydbg',
            'x64dbg',
            'windbg',
            'ida64',
            'radare2'
        }
        
        self.vm_processes = {
            'vmsrvc.exe',
            'authd.exe',
            'vm3dservice.exe',
            'vmtoolsd.exe',
            'dumpcap.exe',
            'tcpdump.exe',
            'windump.exe',
            'apimonitor-x64.exe',
            'apimonitor-x86.exe',
            'regmon.exe',
            'filemon.exe',
            'immunitydebugger.exe',
            'reshacker.exe',
            'pestudio.exe',
            'dnspy.exe',
            'scylla_x64.exe',
            'protection_id.exe'
        }

        self.debugger_processes = {
            'ollydbg.exe',
            'x64dbg.exe', 
            'windbg.exe',
            'ida64.exe',
            'radare2.exe',
            'immunity debugger.exe',
            'cheatengine-x86_64.exe'
        }

        self.monitoring_tools = {
            'procmon.exe',
            'procmon64.exe',
            'processmonitor.exe', 
            'wireshark.exe',
            'fiddler.exe',
            'charles.exe',
            'tcpview.exe',
            'autoruns.exe',
            'autorunsc.exe',
            'filemon.exe',
            'regmon.exe'
        }

    def check_debugger(self) -> bool:
        """Enhanced debugger detection with anti-attach"""
        try:
            kernel32 = ctypes.windll.kernel32
            ntdll = ctypes.windll.ntdll
            
            # Basic debugger checks
            if kernel32.IsDebuggerPresent():
                return True
                
            # Anti-attach mechanisms
            self._prevent_debugger_attach()
            
            # Thread start address verification
            if self._check_thread_start():
                return True
                
            # Advanced timing checks
            if self._detect_timing_anomalies():
                return True
                
            # Exception handler verification
            if self._verify_exception_handlers():
                return True
                
            # Hardware breakpoints
            if self._check_hardware_breakpoints():
                return True
                
            # Memory breakpoints
            if self._scan_memory_breakpoints():
                return True
                
            # Code integrity verification
            if self._verify_code_integrity():
                return True
                
            return False

        except Exception:
            return False

    def check_sandbox_behavior(self) -> bool:
        """Advanced sandbox behavior detection"""
        try:
            # Check for artificial delays
            start_time = time.time()
            time.sleep(0.5)  
            if time.time() - start_time > 0.6:
                return True

            # Check number of running processes
            if len(psutil.pids()) < 50:  # Too few processes
                return True

            # Check disk size and memory
            disk = psutil.disk_usage('/')
            memory = psutil.virtual_memory()
            if disk.total < 60 * 1024 * 1024 * 1024 or memory.total < 2 * 1024 * 1024 * 1024:
                return True

            # Check for sandbox-specific environment variables
            sandbox_vars = {'SANDBOX', 'ANALYSIS', 'MALWARE', 'VIRUS'}
            if any(var in os.environ for var in sandbox_vars):
                return True

            return False

        except Exception:
            return False

    def detect_monitoring(self) -> bool:
        """Enhanced monitoring tool detection"""
        try:
            # Process scanning
            if self._scan_monitoring_processes():
                return True
                
            # Driver detection
            if self._detect_monitoring_drivers():
                return True
                
            # Registry monitoring
            if self._check_registry_monitors():
                return True
                
            # Network monitoring
            if self._detect_network_monitors():
                return True
                
            # Hook detection
            if self._check_api_hooks():
                return True
                
            # EDR detection
            if self._detect_edr_presence():
                return True
                
            # Hidden threads
            if self._find_monitoring_threads():
                return True
                
            return False

        except Exception:
            return False

    def anti_dump(self) -> None:
        """Advanced anti-dump protection"""
        try:
            # PE header manipulation
            self._corrupt_pe_header()
            
            # Memory protection
            self._protect_critical_memory()
            
            # Import table encryption
            self._encrypt_import_table()
            
            # TLS callback installation
            self._install_tls_callbacks()
            
            # Stack trace manipulation
            self._manipulate_stack_trace()
            
            # Section scrambling
            self._scramble_sections()

        except Exception:
            pass

    def _get_memory_regions(self) -> List[tuple]:
        """Get memory regions to protect"""
        regions = []
        try:
            mbi = ctypes.c_void_p()
            length = ctypes.c_ulong(0)
            while ctypes.windll.kernel32.VirtualQueryEx(
                ctypes.windll.kernel32.GetCurrentProcess(),
                mbi, ctypes.sizeof(mbi), ctypes.byref(length)
            ):
                if mbi.State == 0x1000 and mbi.Type == 0x20000:
                    regions.append((mbi.BaseAddress, mbi.RegionSize))
                mbi.BaseAddress += mbi.RegionSize
        except Exception:
            pass
        return regions

    def run_all_checks(self) -> bool:
        """Run all anti-analysis checks"""
        checks = [
            self.check_debugger,
            self.check_sandbox_behavior, 
            self.detect_monitoring,
            self._check_system_info,
            self._check_processes,
            self._check_services,
            self._check_files,
            self._check_registry,
            self._check_hardware,
            self._check_mac_address,
            self._check_memory,
            self._check_timing,
            self._check_artifacts,
            self._check_process_behavior,
            self._check_sandbox_artifacts,
            self._check_hardware_consistency
        ]

        # Apply anti-dump protection
        self.anti_dump()
        
        detected_by = []
        for check in checks:
            try:
                if check():
                    detected_by.append(check.__name__)
            except Exception as e:
                self.logger.error(f"Error in {check.__name__}: {str(e)}")
                
        if detected_by:
            self.logger.warning(f"Analysis environment detected by: {', '.join(detected_by)}")
            return True
            
        return False

    def _init_ai_detector(self):
        """Initialize AI-based VM detection system"""
        try:
            # Load pre-trained model or create new one
            model_path = "models/vm_detector.pkl"
            if os.path.exists(model_path):
                return joblib.load(model_path)
            else:
                # Create new AI model
                model = {
                    'classifier': RandomForestClassifier(
                        n_estimators=100,
                        max_depth=10,
                        random_state=42
                    ),
                    'scaler': StandardScaler(),
                    'is_trained': False,
                    'training_data': [],
                    'labels': []
                }
                return model
        except Exception as e:
            self.logger.warning(f"AI detector initialization failed: {e}")
            return None
    
    def _extract_ai_features(self) -> np.ndarray:
        """Extract comprehensive features for AI analysis"""
        try:
            features = []
            
            # Hardware features
            features.extend(self._get_hardware_features())
            
            # Process features
            features.extend(self._get_process_features())
            
            # System features
            features.extend(self._get_system_features())
            
            # Network features
            features.extend(self._get_network_features())
            
            # Timing features
            features.extend(self._get_timing_features())
            
            # Registry features
            features.extend(self._get_registry_features())
            
            return np.array(features)
            
        except Exception as e:
            self.logger.error(f"Feature extraction failed: {e}")
            return np.zeros(50)  # Return default features
    
    def _get_hardware_features(self) -> List[float]:
        """Extract hardware-based features"""
        features = []
        try:
            # CPU features
            cpu_count = psutil.cpu_count(logical=False)
            cpu_count_logical = psutil.cpu_count(logical=True)
            features.extend([cpu_count, cpu_count_logical, cpu_count_logical/cpu_count])
            
            # Memory features
            memory = psutil.virtual_memory()
            features.extend([
                memory.total / (1024**3),  # GB
                memory.available / memory.total,
                memory.percent
            ])
            
            # Disk features
            disk = psutil.disk_usage('/')
            features.extend([
                disk.total / (1024**3),  # GB
                disk.free / disk.total,
                disk.used / disk.total
            ])
            
            # Hardware IDs
            mac_address = ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff) for elements in range(0,2*6,2)][::-1])
            mac_hash = int(hashlib.md5(mac_address.encode()).hexdigest()[:8], 16) / 0xffffffff
            features.append(mac_hash)
            
        except Exception:
            features.extend([0] * 11)
        
        return features
    
    def _get_process_features(self) -> List[float]:
        """Extract process-based features"""
        features = []
        try:
            processes = list(psutil.process_iter(['name', 'cpu_percent', 'memory_percent']))
            
            # Process count
            features.append(len(processes))
            
            # VM/Analysis tool detection
            vm_processes = sum(1 for p in processes if p.info['name'].lower() in 
                             [proc.lower() for proc in self.vm_processes])
            features.append(vm_processes)
            
            # System process analysis
            system_processes = sum(1 for p in processes if 'system' in p.info['name'].lower())
            features.append(system_processes)
            
            # CPU and memory distribution
            if processes:
                cpu_values = [p.info['cpu_percent'] or 0 for p in processes]
                memory_values = [p.info['memory_percent'] or 0 for p in processes]
                
                features.extend([
                    np.mean(cpu_values),
                    np.std(cpu_values),
                    np.mean(memory_values),
                    np.std(memory_values)
                ])
            else:
                features.extend([0, 0, 0, 0])
                
        except Exception:
            features.extend([0] * 8)
        
        return features
    
    def _get_system_features(self) -> List[float]:
        """Extract system-based features"""
        features = []
        try:
            # Boot time analysis
            boot_time = psutil.boot_time()
            uptime = time.time() - boot_time
            features.extend([
                uptime / 3600,  # Hours
                1 if uptime < 300 else 0  # Recent boot indicator
            ])
            
            # User session analysis
            users = psutil.users()
            features.extend([
                len(users),
                1 if any('console' in u.terminal.lower() for u in users) else 0
            ])
            
            # File system analysis
            temp_files = len(list(Path(os.environ.get('TEMP', '/tmp')).glob('*')))
            features.append(min(temp_files / 100, 1))  # Normalized
            
        except Exception:
            features.extend([0] * 5)
        
        return features
    
    def _get_network_features(self) -> List[float]:
        """Extract network-based features"""
        features = []
        try:
            # Network interface analysis
            interfaces = psutil.net_if_addrs()
            features.append(len(interfaces))
            
            # Connection analysis
            connections = psutil.net_connections()
            features.extend([
                len(connections),
                sum(1 for c in connections if c.status == 'ESTABLISHED')
            ])
            
            # Network statistics
            net_io = psutil.net_io_counters()
            features.extend([
                net_io.bytes_sent / (1024**2),  # MB
                net_io.bytes_recv / (1024**2),  # MB
                net_io.packets_sent,
                net_io.packets_recv
            ])
            
        except Exception:
            features.extend([0] * 7)
        
        return features
    
    def _get_timing_features(self) -> List[float]:
        """Extract timing-based features"""
        features = []
        try:
            # Measure various timing operations
            timings = []
            
            # Sleep timing test
            start = time.perf_counter()
            time.sleep(0.001)
            sleep_time = time.perf_counter() - start
            timings.append(sleep_time)
            
            # CPU intensive operation timing
            start = time.perf_counter()
            sum(i*i for i in range(1000))
            cpu_time = time.perf_counter() - start
            timings.append(cpu_time)
            
            # Memory allocation timing
            start = time.perf_counter()
            temp_data = [0] * 10000
            memory_time = time.perf_counter() - start
            timings.append(memory_time)
            
            features.extend(timings)
            
            # Timing consistency analysis
            if len(timings) > 1:
                features.append(np.std(timings))
            else:
                features.append(0)
                
        except Exception:
            features.extend([0] * 4)
        
        return features
    
    def _get_registry_features(self) -> List[float]:
        """Extract Windows registry-based features"""
        features = []
        try:
            if sys.platform != 'win32':
                return [0] * 5
            
            # Check VM-related registry keys
            vm_keys = [
                r"HARDWARE\DEVICEMAP\Scsi\Scsi Port 0\Scsi Bus 0\Target Id 0\Logical Unit Id 0",
                r"SOFTWARE\Oracle\VirtualBox Guest Additions",
                r"SOFTWARE\VMware, Inc.\VMware Tools",
                r"SYSTEM\ControlSet001\Services\VBoxGuest",
                r"SYSTEM\ControlSet001\Services\VMTools"
            ]
            
            vm_registry_count = 0
            for key_path in vm_keys:
                try:
                    winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path)
                    vm_registry_count += 1
                except:
                    pass
            
            features.append(vm_registry_count)
            
            # System info from registry
            try:
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"HARDWARE\DESCRIPTION\System") as key:
                    bios_vendor = winreg.QueryValueEx(key, "SystemBiosVersion")[0]
                    features.append(1 if any(vm in bios_vendor.lower() for vm in ['vmware', 'virtualbox', 'qemu']) else 0)
            except:
                features.append(0)
            
            # Add more registry-based features
            features.extend([0, 0, 0])  # Placeholder for additional features
            
        except Exception:
            features.extend([0] * 5)
        
        return features
    
    def ai_check_vm_environment(self) -> Dict[str, any]:
        """AI-powered VM environment detection"""
        try:
            if not self.ai_detector or not self.ai_detector['is_trained']:
                # Fallback to traditional detection
                return {
                    'is_vm': self.run_all_checks(),
                    'confidence': 0.5,
                    'method': 'traditional',
                    'ai_available': False
                }
            
            # Extract features
            features = self._extract_ai_features()
            
            # Scale features
            features_scaled = self.ai_detector['scaler'].transform(features.reshape(1, -1))
            
            # Predict
            prediction = self.ai_detector['classifier'].predict(features_scaled)[0]
            confidence = max(self.ai_detector['classifier'].predict_proba(features_scaled)[0])
            
            # Store detection result for learning
            with self._detection_lock:
                self.detection_history.append({
                    'timestamp': time.time(),
                    'features': features,
                    'prediction': prediction,
                    'confidence': confidence
                })
                
                # Keep only recent history
                if len(self.detection_history) > 1000:
                    self.detection_history = self.detection_history[-500:]
            
            return {
                'is_vm': bool(prediction),
                'confidence': float(confidence),
                'method': 'ai_enhanced',
                'ai_available': True,
                'feature_count': len(features)
            }
            
        except Exception as e:
            self.logger.error(f"AI VM detection failed: {e}")
            return {
                'is_vm': self.run_all_checks(),
                'confidence': 0.3,
                'method': 'fallback',
                'ai_available': False,
                'error': str(e)
            }
    
    def train_ai_detector(self, labeled_data: List[Dict]):
        """Train the AI detector with labeled data"""
        try:
            if not self.ai_detector:
                return False
            
            if len(labeled_data) < 10:
                self.logger.warning("Insufficient training data")
                return False
            
            # Prepare training data
            X = []
            y = []
            
            for sample in labeled_data:
                if 'features' in sample and 'label' in sample:
                    X.append(sample['features'])
                    y.append(sample['label'])
            
            if len(X) < 10:
                return False
            
            X = np.array(X)
            y = np.array(y)
            
            # Scale features
            X_scaled = self.ai_detector['scaler'].fit_transform(X)
            
            # Train classifier
            self.ai_detector['classifier'].fit(X_scaled, y)
            self.ai_detector['is_trained'] = True
            
            # Save model
            os.makedirs("models", exist_ok=True)
            joblib.dump(self.ai_detector, "models/vm_detector.pkl")
            
            self.logger.info(f"AI detector trained with {len(X)} samples")
            return True
            
        except Exception as e:
            self.logger.error(f"AI training failed: {e}")
            return False
    
    def adaptive_learning_update(self):
        """Update AI model based on detection history"""
        try:
            if not self.learning_enabled or not self.ai_detector:
                return
            
            with self._detection_lock:
                if len(self.detection_history) < 50:
                    return
                
                # Analyze recent predictions for potential false positives
                recent_detections = self.detection_history[-50:]
                
                # Simple heuristic: if too many high-confidence VM detections,
                # might be false positives in a real environment
                vm_detections = sum(1 for d in recent_detections if d['prediction'])
                avg_confidence = np.mean([d['confidence'] for d in recent_detections])
                
                if vm_detections > 40 and avg_confidence > 0.9:
                    # Possible false positive scenario - retrain with lower sensitivity
                    self.confidence_threshold = min(0.9, self.confidence_threshold + 0.05)
                    self.logger.info(f"Adjusted confidence threshold to {self.confidence_threshold}")
                
        except Exception as e:
            self.logger.error(f"Adaptive learning update failed: {e}")