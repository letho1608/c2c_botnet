from __future__ import annotations
import os
import ssl
import base64
import socket
import hashlib
import logging
import threading
import time
import weakref
from functools import lru_cache
from typing import Dict, Optional, Tuple, Any, Union, Set
from pathlib import Path
from datetime import datetime
from contextlib import contextmanager
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.x509.oid import NameOID
from cryptography.fernet import Fernet

# AI Imports for advanced security
import numpy as np
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.neural_network import MLPClassifier
from sklearn.cluster import DBSCAN
import joblib
import psutil
import ipaddress

from .cert_pinning import CertificatePinning
from .integrity import IntegrityChecker
from .memory_protection import MemoryProtection
from .advanced_protection import AdvancedProtection
from .anti_vm import AntiVM
from .code_obfuscation import CodeObfuscator
from .network_protection import NetworkProtection
from .crypto import Crypto, CryptoError

class SecurityError(Exception):
    """Security related errors"""
    pass

class SecurityManager:
    def __init__(self, is_server: bool = False, 
                 cert_dir: str = "certs",
                 verify_cert: bool = False) -> None:
        """Initialize security manager"""
        self.is_server = is_server
        self.cert_dir = Path(cert_dir)
        self.verify_cert = verify_cert
        self.logger = logging.getLogger('security')
        
        # Create cert directory
        self.cert_dir.mkdir(exist_ok=True)
        
        # Initialize components
        self.cert_pinning = CertificatePinning()
        self.integrity_checker = IntegrityChecker()
        self.memory_protection = MemoryProtection()
        self.advanced_protection = AdvancedProtection()
        self.anti_vm = AntiVM()
        self.code_obfuscator = CodeObfuscator()
        self.network_protection = NetworkProtection()
        self.crypto = Crypto()
        
        # AI Security Components
        self.ai_threat_detector = None
        self.ai_anomaly_detector = None
        self.ai_behavior_analyzer = None
        self.ai_scaler = StandardScaler()
        self.threat_history = []
        self.connection_patterns = []
        self.security_events = []
        
        # Security monitoring
        self.active_connections = {}
        self.failed_attempts = {}
        self.suspicious_ips = set()
        self.threat_scores = {}
        
        # Initialize AI models
        self._init_ai_security_models()
        
        # Security state
        self.ssl_context = None
        self.keys = {}
        self.certificates = {}
        self.authenticated_clients = weakref.WeakSet()
        self.access_tokens = {}
        self._lock = threading.RLock()
        self._setup_ssl_context()
        self.integrity = IntegrityChecker()
        self.memory_protection = MemoryProtection()
        self.advanced_protection = AdvancedProtection()
        self.anti_vm = AntiVM()
        self.code_obfuscator = CodeObfuscator()
        self.network_protection = NetworkProtection()
        
        # Initialize crypto
        self.crypto = Crypto()
        
        # Sử dụng weakref để quản lý sessions và protected_data
        self.sessions: weakref.WeakValueDictionary = weakref.WeakValueDictionary()
        self.protected_data: weakref.WeakValueDictionary = weakref.WeakValueDictionary()
        
        # Protection settings
        self.check_interval = 300  # 5 minutes
        self.last_check = 0
        
        # Initialize security
        self._init_security()
        
    def _init_security(self) -> None:
        """Initialize all security components"""
        try:
            # Check for VM
            if self.anti_vm.check_all():
                raise SecurityError("VM environment detected")
                
            # Perform initial integrity check
            if not self.integrity.self_check():
                raise SecurityError("Integrity check failed")
                
            # Start protections
            self.memory_protection.start_protection()
            self.advanced_protection.start_protection()
            self.network_protection.start_protection()
            
            # Initialize SSL
            self._init_ssl()
            
            # Start integrity checking thread
            self._start_integrity_checking()
            
        except Exception as e:
            self.logger.exception("Security initialization error")
            raise SecurityError(f"Failed to initialize security: {e}")
            
    def protect_data(self, data_id: str, data: bytes) -> bool:
        """Protect sensitive data in memory
        
        Args:
            data_id: Unique identifier for data
            data: Data to protect
            
        Returns:
            bool: True if protected successfully
        """
        try:
            # Remove old protected data if exists
            if data_id in self.protected_data:
                self.unprotect_data(data_id)
                
            # Use advanced protection
            address, size = self.advanced_protection.protect_memory(data_id, data)
            
            # Store reference
            self.protected_data[data_id] = (address, size)
            return True
            
        except Exception as e:
            self.logger.error(f"Error protecting data {data_id}: {str(e)}")
            return False
            
    def unprotect_data(self, data_id: str) -> Optional[bytes]:
        """Retrieve and unprotect data
        
        Args:
            data_id: Data identifier
            
        Returns:
            Optional[bytes]: Decrypted data or None if failed
        """
        try:
            if data_id not in self.protected_data:
                return None
                
            address, size = self.protected_data[data_id]
            
            # Decrypt using advanced protection
            data = self.advanced_protection.unprotect_memory(address)
            
            # Remove protection
            del self.protected_data[data_id]
            
            return data
            
        except Exception as e:
            self.logger.error(f"Error unprotecting data {data_id}: {str(e)}")
            return None
            
    @lru_cache(maxsize=1000)
    def verify_connection(self, address: str, port: int) -> bool:
        """Verify if connection should be allowed
        
        Args:
            address: Remote address
            port: Remote port
            
        Returns:
            bool: True if connection allowed
        """
        return self.network_protection.verify_connection(address, port)
        
    def obfuscate_code(self, path: Union[str, Path],
                      exclude: Optional[Set[str]] = None) -> bool:
        """Obfuscate Python source code
        
        Args:
            path: File or directory path
            exclude: Files to exclude
            
        Returns:
            bool: True if obfuscated successfully
        """
        try:
            path = Path(path)
            if path.is_file():
                return self.code_obfuscator.obfuscate_file(str(path))
            else:
                return self.code_obfuscator.obfuscate_directory(
                    str(path),
                    exclude
                )
        except Exception as e:
            self.logger.error(f"Obfuscation error: {str(e)}")
            return False
            
    @contextmanager
    def protection_context(self):
        """Context manager for handling protections"""
        try:
            yield
        finally:
            self.cleanup()

    def cleanup(self) -> None:
        """Clean up all protected resources"""
        try:
            # Stop protections
            for protection in (self.memory_protection,
                             self.advanced_protection,
                             self.network_protection):
                try:
                    protection.stop_protection()
                except Exception as e:
                    self.logger.warning(f"Failed to stop {protection.__class__.__name__}: {e}")
            
            # Clear protected data
            for data_id in list(self.protected_data.keys()):
                self.unprotect_data(data_id)
            
            # Clean up sessions and cache
            self.sessions.clear()
            self.verify_connection.cache_clear()
            
        except Exception as e:
            self.logger.exception("Cleanup error")
            
    def block_ip(self, address: str) -> None:
        """Block IP address
        
        Args:
            address: IP to block
        """
        self.network_protection.block_ip(address)
        
    def block_domain(self, domain: str) -> None:
        """Block domain
        
        Args:
            domain: Domain to block
        """
        self.network_protection.block_domain(domain)
        
    def encrypt_data(self, data: Union[str, bytes], peer_id: Optional[str] = None) -> Union[bytes, str]:
        """Encrypt data using crypto module
        
        Args:
            data: Data to encrypt
            peer_id: Optional peer ID for session encryption
            
        Returns:
            Encrypted data
        """
        return self.crypto.encrypt(data, peer_id)
        
    def decrypt_data(self, encrypted_data: Union[str, bytes], peer_id: Optional[str] = None) -> bytes:
        """Decrypt data using crypto module
        
        Args:
            encrypted_data: Data to decrypt
            peer_id: Optional peer ID for session decryption
            
        Returns:
            Decrypted data
        """
        return self.crypto.decrypt(encrypted_data, peer_id)
        
    def establish_crypto_session(self, peer_id: str, peer_public_key: str) -> str:
        """Establish encrypted session with peer
        
        Args:
            peer_id: Peer identifier
            peer_public_key: Peer's public key
            
        Returns:
            Encrypted session key
        """
        return self.crypto.establish_session(peer_id, peer_public_key)
        
    def receive_crypto_session(self, peer_id: str, encrypted_key: str) -> None:
        """Receive encrypted session from peer
        
        Args:
            peer_id: Peer identifier
            encrypted_key: Encrypted session key
        """
        self.crypto.receive_session_key(peer_id, encrypted_key)
        
    def _init_ai_security_models(self):
        """Initialize AI models for advanced security"""
        try:
            # Threat detection using Random Forest
            self.ai_threat_detector = RandomForestClassifier(
                n_estimators=100,
                max_depth=15,
                random_state=42
            )
            
            # Anomaly detection using Isolation Forest
            self.ai_anomaly_detector = IsolationForest(
                contamination=0.1,
                random_state=42
            )
            
            # Behavior analysis using Neural Network
            self.ai_behavior_analyzer = MLPClassifier(
                hidden_layer_sizes=(100, 50),
                max_iter=1000,
                random_state=42
            )
            
            self.logger.info("AI security models initialized")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize AI security models: {e}")
    
    def ai_analyze_connection(self, ip: str, port: int, data: bytes = b"") -> Dict[str, Any]:
        """Use AI to analyze incoming connection for threats"""
        try:
            # Extract connection features
            features = self._extract_connection_features(ip, port, data)
            
            # Initialize analysis result
            analysis = {
                'ip': ip,
                'port': port,
                'threat_level': 'low',
                'threat_score': 0.0,
                'anomaly_score': 0.0,
                'blocked': False,
                'reasons': []
            }
            
            # Check IP reputation
            if self._is_suspicious_ip(ip):
                analysis['threat_level'] = 'high'
                analysis['threat_score'] += 0.7
                analysis['reasons'].append('Suspicious IP history')
            
            # AI threat detection
            if hasattr(self.ai_threat_detector, 'predict_proba') and len(self.threat_history) > 50:
                try:
                    threat_prob = self.ai_threat_detector.predict_proba([features])[0][1]
                    analysis['threat_score'] += threat_prob * 0.8
                    
                    if threat_prob > 0.7:
                        analysis['threat_level'] = 'high'
                        analysis['reasons'].append(f'AI threat detection: {threat_prob:.2f}')
                except Exception as e:
                    self.logger.error(f"AI threat detection failed: {e}")
            
            # Anomaly detection
            if hasattr(self.ai_anomaly_detector, 'decision_function') and len(self.connection_patterns) > 100:
                try:
                    anomaly_score = self.ai_anomaly_detector.decision_function([features])[0]
                    analysis['anomaly_score'] = anomaly_score
                    
                    if anomaly_score < -0.5:  # Negative scores indicate anomalies
                        analysis['threat_score'] += 0.5
                        analysis['reasons'].append(f'Anomalous connection pattern: {anomaly_score:.2f}')
                except Exception as e:
                    self.logger.error(f"Anomaly detection failed: {e}")
            
            # Rate limiting analysis
            rate_violation = self._check_rate_limiting(ip)
            if rate_violation:
                analysis['threat_score'] += 0.6
                analysis['reasons'].append('Rate limiting violation')
            
            # Determine final threat level and blocking decision
            if analysis['threat_score'] > 0.8:
                analysis['threat_level'] = 'critical'
                analysis['blocked'] = True
            elif analysis['threat_score'] > 0.5:
                analysis['threat_level'] = 'high'
                analysis['blocked'] = True
            elif analysis['threat_score'] > 0.3:
                analysis['threat_level'] = 'medium'
            
            # Record for learning
            self._record_security_event(analysis, features)
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"AI connection analysis failed: {e}")
            return {
                'ip': ip,
                'port': port,
                'threat_level': 'unknown',
                'threat_score': 0.5,
                'blocked': False,
                'reasons': ['Analysis failed']
            }
    
    def _extract_connection_features(self, ip: str, port: int, data: bytes) -> np.ndarray:
        """Extract features from connection for AI analysis"""
        try:
            features = []
            
            # IP-based features
            try:
                ip_obj = ipaddress.ip_address(ip)
                features.extend([
                    int(ip_obj.is_private),
                    int(ip_obj.is_loopback),
                    int(ip_obj.is_multicast),
                    int(ip_obj.is_reserved),
                    hash(ip) % 1000 / 1000.0  # IP hash normalized
                ])
            except:
                features.extend([0.0, 0.0, 0.0, 0.0, 0.0])
            
            # Port features
            features.extend([
                port / 65535.0,  # Normalized port
                int(port < 1024),  # Well-known port
                int(port in [80, 443, 22, 21, 25, 53]),  # Common service ports
                int(port in range(1024, 49152)),  # Registered ports
                int(port >= 49152)  # Dynamic ports
            ])
            
            # Data features
            if data:
                features.extend([
                    len(data) / 1024.0,  # Data size normalized
                    sum(data) / (len(data) * 255.0) if data else 0.0,  # Average byte value
                    len(set(data)) / 256.0 if data else 0.0,  # Entropy approximation
                    int(b'HTTP' in data),
                    int(b'POST' in data),
                    int(b'GET' in data)
                ])
            else:
                features.extend([0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
            
            # Time-based features
            current_time = time.time()
            features.extend([
                (current_time % 86400) / 86400.0,  # Time of day normalized
                (current_time % 604800) / 604800.0,  # Day of week normalized
            ])
            
            # Connection history features
            ip_history = self.active_connections.get(ip, [])
            features.extend([
                len(ip_history),  # Connection count
                len(self.failed_attempts.get(ip, [])),  # Failed attempts
                int(ip in self.suspicious_ips),  # Suspicious IP flag
                self.threat_scores.get(ip, 0.0)  # Historical threat score
            ])
            
            return np.array(features)
            
        except Exception as e:
            self.logger.error(f"Feature extraction failed: {e}")
            return np.zeros(21)  # Default feature vector
    
    def _is_suspicious_ip(self, ip: str) -> bool:
        """Check if IP is in suspicious list"""
        return ip in self.suspicious_ips
    
    def _check_rate_limiting(self, ip: str) -> bool:
        """Check if IP exceeds rate limits"""
        current_time = time.time()
        
        # Clean old entries
        if ip in self.active_connections:
            self.active_connections[ip] = [
                t for t in self.active_connections[ip]
                if current_time - t < 60  # Last 60 seconds
            ]
        
        # Check rate limit (max 10 connections per minute)
        connection_count = len(self.active_connections.get(ip, []))
        return connection_count > 10
    
    def _record_security_event(self, analysis: Dict, features: np.ndarray):
        """Record security event for AI learning"""
        try:
            event = {
                'timestamp': time.time(),
                'features': features.tolist(),
                'threat_score': analysis['threat_score'],
                'threat_level': analysis['threat_level'],
                'blocked': analysis['blocked'],
                'ip': analysis['ip']
            }
            
            self.security_events.append(event)
            
            # Keep only recent events (last 10000)
            if len(self.security_events) > 10000:
                self.security_events = self.security_events[-10000:]
                
        except Exception as e:
            self.logger.error(f"Failed to record security event: {e}")
    
    def ai_adaptive_learning(self):
        """Update AI models with recent security events"""
        try:
            if len(self.security_events) < 100:
                return
            
            # Prepare training data
            X = []
            y_threat = []
            y_anomaly = []
            
            for event in self.security_events[-1000:]:  # Use last 1000 events
                features = event.get('features', [])
                if len(features) > 0:
                    X.append(features)
                    y_threat.append(1 if event['threat_score'] > 0.5 else 0)
                    y_anomaly.append(event['threat_score'])
            
            if len(X) < 50:
                return
            
            X = np.array(X)
            y_threat = np.array(y_threat)
            y_anomaly = np.array(y_anomaly)
            
            # Update threat detector
            try:
                self.ai_threat_detector.fit(X, y_threat)
                self.logger.info("Threat detector model updated")
            except Exception as e:
                self.logger.error(f"Threat detector update failed: {e}")
            
            # Update anomaly detector
            try:
                self.ai_anomaly_detector.fit(X)
                self.logger.info("Anomaly detector model updated")
            except Exception as e:
                self.logger.error(f"Anomaly detector update failed: {e}")
            
        except Exception as e:
            self.logger.error(f"AI adaptive learning failed: {e}")
    
    def ai_predict_attack_vector(self, connection_data: Dict) -> Dict[str, Any]:
        """Use AI to predict potential attack vectors"""
        try:
            ip = connection_data.get('ip', '')
            features = self._extract_connection_features(
                ip, 
                connection_data.get('port', 0),
                connection_data.get('data', b'')
            )
            
            prediction = {
                'attack_types': [],
                'confidence_scores': {},
                'recommended_actions': []
            }
            
            # Analyze connection patterns for attack vector prediction
            if hasattr(self.ai_behavior_analyzer, 'predict_proba') and len(self.threat_history) > 100:
                try:
                    # This would need to be trained with labeled attack data
                    # For now, use heuristic analysis
                    port = connection_data.get('port', 0)
                    data = connection_data.get('data', b'')
                    
                    # Port-based attack vector analysis
                    if port == 22:
                        prediction['attack_types'].append('ssh_bruteforce')
                        prediction['confidence_scores']['ssh_bruteforce'] = 0.7
                    elif port == 80 or port == 443:
                        if b'sqlmap' in data or b'union' in data.lower():
                            prediction['attack_types'].append('sql_injection')
                            prediction['confidence_scores']['sql_injection'] = 0.8
                        if b'<script>' in data.lower():
                            prediction['attack_types'].append('xss_attempt')
                            prediction['confidence_scores']['xss_attempt'] = 0.6
                    elif port == 3389:
                        prediction['attack_types'].append('rdp_attack')
                        prediction['confidence_scores']['rdp_attack'] = 0.5
                    
                    # Generate recommendations
                    for attack_type in prediction['attack_types']:
                        if attack_type == 'ssh_bruteforce':
                            prediction['recommended_actions'].append('Enable fail2ban for SSH')
                        elif attack_type == 'sql_injection':
                            prediction['recommended_actions'].append('Enable WAF rules for SQL injection')
                        elif attack_type == 'xss_attempt':
                            prediction['recommended_actions'].append('Enable XSS protection headers')
                        elif attack_type == 'rdp_attack':
                            prediction['recommended_actions'].append('Restrict RDP access by IP')
                    
                except Exception as e:
                    self.logger.error(f"Attack vector prediction failed: {e}")
            
            return prediction
            
        except Exception as e:
            self.logger.error(f"AI attack vector prediction failed: {e}")
            return {'attack_types': [], 'confidence_scores': {}, 'recommended_actions': []}
    
    def ai_security_health_check(self) -> Dict[str, Any]:
        """Perform AI-powered security health assessment"""
        try:
            health_report = {
                'overall_score': 100,
                'vulnerabilities': [],
                'recommendations': [],
                'threat_trends': {},
                'system_metrics': {}
            }
            
            # Analyze recent security events
            recent_events = [
                e for e in self.security_events
                if time.time() - e['timestamp'] < 3600  # Last hour
            ]
            
            if recent_events:
                # Calculate threat trend
                threat_scores = [e['threat_score'] for e in recent_events]
                avg_threat = np.mean(threat_scores)
                max_threat = np.max(threat_scores)
                
                health_report['threat_trends'] = {
                    'average_threat_level': avg_threat,
                    'maximum_threat_level': max_threat,
                    'total_events': len(recent_events),
                    'blocked_events': sum(1 for e in recent_events if e['blocked'])
                }
                
                # Adjust overall score based on threats
                if avg_threat > 0.7:
                    health_report['overall_score'] -= 30
                    health_report['vulnerabilities'].append('High average threat level detected')
                elif avg_threat > 0.5:
                    health_report['overall_score'] -= 15
                    health_report['vulnerabilities'].append('Elevated threat level detected')
            
            # System resource analysis
            try:
                cpu_percent = psutil.cpu_percent()
                memory_percent = psutil.virtual_memory().percent
                
                health_report['system_metrics'] = {
                    'cpu_usage': cpu_percent,
                    'memory_usage': memory_percent
                }
                
                if cpu_percent > 80:
                    health_report['overall_score'] -= 10
                    health_report['vulnerabilities'].append('High CPU usage may affect security monitoring')
                
                if memory_percent > 85:
                    health_report['overall_score'] -= 10
                    health_report['vulnerabilities'].append('High memory usage may affect security operations')
                    
            except Exception as e:
                self.logger.error(f"System metrics analysis failed: {e}")
            
            # Generate recommendations
            if health_report['overall_score'] < 70:
                health_report['recommendations'].extend([
                    'Immediate security review required',
                    'Consider increasing monitoring sensitivity',
                    'Review and update security policies'
                ])
            elif health_report['overall_score'] < 85:
                health_report['recommendations'].extend([
                    'Security improvements recommended',
                    'Monitor threat trends closely'
                ])
            
            return health_report
            
        except Exception as e:
            self.logger.error(f"Security health check failed: {e}")
            return {
                'overall_score': 0,
                'vulnerabilities': ['Health check failed'],
                'recommendations': ['Manual security review required'],
                'threat_trends': {},
                'system_metrics': {}
            }