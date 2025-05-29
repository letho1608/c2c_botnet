#!/usr/bin/env python3
"""
AI-Powered Security Manager
Advanced security system with machine learning capabilities
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, field
import threading
import queue
import json
import time
import hashlib
import pickle
import os
from pathlib import Path

# ML/AI imports
try:
    import numpy as np
    import tensorflow as tf
    from sklearn.ensemble import IsolationForest, RandomForestClassifier
    from sklearn.preprocessing import StandardScaler
    from sklearn.model_selection import train_test_split
    from sentence_transformers import SentenceTransformer
    import torch
    import torch.nn as nn
    import transformers
    AI_AVAILABLE = True
except ImportError as e:
    logging.warning(f"AI libraries not available: {e}")
    AI_AVAILABLE = False
    # Create mock numpy for basic operations
    class MockNumPy:
        @staticmethod
        def array(data):
            return data
        @staticmethod
        def mean(data):
            return sum(data) / len(data) if data else 0
        @staticmethod
        def std(data):
            if not data:
                return 0
            mean = sum(data) / len(data)
            return (sum((x - mean) ** 2 for x in data) / len(data)) ** 0.5
    np = MockNumPy()
      # Mock sklearn classes
    class MockStandardScaler:
        def fit_transform(self, data):
            return data
        def transform(self, data):
            return data
    StandardScaler = MockStandardScaler
    
    class MockIsolationForest:
        def fit(self, data):
            pass
        def decision_function(self, data):
            return [0.0] * len(data)
    IsolationForest = MockIsolationForest
    
    class MockRandomForestClassifier:
        def fit(self, X, y):
            pass
        def predict_proba(self, X):
            return [[0.5, 0.5] for _ in X]
    RandomForestClassifier = MockRandomForestClassifier
    
    class MockSentenceTransformer:
        def __init__(self, model_name):
            pass
        def encode(self, texts):
            return [[0.0] * 384 for _ in texts]  # Mock 384-dim embeddings    SentenceTransformer = MockSentenceTransformer
    AI_AVAILABLE = False

@dataclass
class SecurityEvent:
    """Security event data structure"""
    timestamp: datetime
    event_type: str
    severity: float  # 0.0 - 1.0
    source_ip: str
    details: Dict[str, Any]
    predicted_threat: bool = False
    confidence: float = 0.0
    ai_analysis: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ThreatProfile:
    """Advanced threat profiling"""
    ip: str
    behavior_vector: Any  # np.ndarray when available
    threat_score: float
    attack_patterns: List[str]
    evasion_techniques: List[str]
    first_seen: datetime
    last_seen: datetime
    total_events: int

class BehaviorAnalysisAI:
    """AI-powered behavior analysis"""
    
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.is_trained = False
        self.feature_dim = 20
        
        if AI_AVAILABLE:
            self._init_models()
    
    def _init_models(self):
        """Initialize ML models"""
        # Anomaly detection model
        self.anomaly_detector = IsolationForest(
            contamination=0.1,
            random_state=42,
            n_jobs=-1
        )
        
        # Classification model for threat types
        self.threat_classifier = RandomForestClassifier(
            n_estimators=100,
            random_state=42,
            n_jobs=-1
        )
        
        # Neural network for advanced pattern recognition
        if torch.cuda.is_available():
            self.device = torch.device("cuda")
        else:
            self.device = torch.device("cpu")
        
        self.neural_detector = self._build_neural_network()
    
    def _build_neural_network(self):
        """Build neural network for pattern detection"""
        class ThreatDetectionNN(nn.Module):
            def __init__(self, input_size=20):
                super(ThreatDetectionNN, self).__init__()
                self.layers = nn.Sequential(
                    nn.Linear(input_size, 128),
                    nn.ReLU(),
                    nn.Dropout(0.3),
                    nn.Linear(128, 64),
                    nn.ReLU(),
                    nn.Dropout(0.2),
                    nn.Linear(64, 32),
                    nn.ReLU(),
                    nn.Linear(32, 1),
                    nn.Sigmoid()
                )
            
            def forward(self, x):
                return self.layers(x)
        
        model = ThreatDetectionNN(self.feature_dim)
        model.to(self.device)
        return model
    
    def extract_features(self, event_data: Dict) -> Any:
        """Extract features from security event"""
        features = []
        
        # Time-based features
        hour = datetime.now().hour
        features.extend([
            hour / 24.0,  # normalized hour
            1 if 22 <= hour or hour <= 6 else 0,  # night activity
        ])
        
        # Connection features
        conn_data = event_data.get('connection', {})
        features.extend([
            conn_data.get('packet_size', 0) / 65535.0,
            conn_data.get('frequency', 0) / 100.0,
            len(conn_data.get('ports', [])) / 100.0,
            1 if conn_data.get('encrypted', False) else 0,
        ])
        
        # Behavioral features
        behavior = event_data.get('behavior', {})
        features.extend([
            behavior.get('command_diversity', 0) / 10.0,
            behavior.get('file_access_rate', 0) / 100.0,
            behavior.get('network_scan_intensity', 0) / 10.0,
            behavior.get('privilege_escalation_attempts', 0) / 5.0,
        ])
        
        # System features
        system = event_data.get('system', {})
        features.extend([
            1 if system.get('vm_detected', False) else 0,
            1 if system.get('debugger_detected', False) else 0,
            1 if system.get('sandbox_detected', False) else 0,
            system.get('cpu_usage', 0) / 100.0,
            system.get('memory_usage', 0) / 100.0,
        ])
        
        # Geo features
        geo = event_data.get('geo', {})
        features.extend([
            1 if geo.get('tor_exit', False) else 0,
            1 if geo.get('vpn_detected', False) else 0,
            geo.get('risk_score', 0) / 100.0,
        ])
        
        # Pad or truncate to fixed size
        features = features[:self.feature_dim]
        while len(features) < self.feature_dim:
            features.append(0.0)
        
        return np.array(features, dtype=np.float32)
    
    def train_on_data(self, training_data: List[Tuple[Dict, bool]]):
        """Train models on labeled data"""
        if not AI_AVAILABLE or not training_data:
            return
        
        try:
            # Prepare data
            X = []
            y = []
            
            for event_data, is_threat in training_data:
                features = self.extract_features(event_data)
                X.append(features)
                y.append(1 if is_threat else 0)
            
            X = np.array(X)
            y = np.array(y)
            
            # Train anomaly detector on normal data
            normal_data = X[y == 0]
            if len(normal_data) > 10:
                self.anomaly_detector.fit(normal_data)
            
            # Train threat classifier
            if len(X) > 20:
                X_scaled = self.scaler.fit_transform(X)
                self.threat_classifier.fit(X_scaled, y)
            
            # Train neural network
            self._train_neural_network(X, y)
            
            self.is_trained = True
            logging.info("AI models trained successfully")
            
        except Exception as e:
            logging.error(f"Training error: {e}")
    
    def _train_neural_network(self, X: Any, y: Any):
        """Train neural network component"""
        if not AI_AVAILABLE:
            return
        
        try:
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )
            
            # Convert to tensors
            X_train_tensor = torch.FloatTensor(X_train).to(self.device)
            y_train_tensor = torch.FloatTensor(y_train).unsqueeze(1).to(self.device)
            
            # Training loop
            optimizer = torch.optim.Adam(self.neural_detector.parameters(), lr=0.001)
            criterion = nn.BCELoss()
            
            self.neural_detector.train()
            for epoch in range(100):
                optimizer.zero_grad()
                outputs = self.neural_detector(X_train_tensor)
                loss = criterion(outputs, y_train_tensor)
                loss.backward()
                optimizer.step()
                
                if epoch % 20 == 0:
                    logging.debug(f"Neural network training epoch {epoch}, loss: {loss.item():.4f}")
        
        except Exception as e:
            logging.error(f"Neural network training error: {e}")
    
    def analyze_event(self, event_data: Dict) -> Tuple[float, Dict]:
        """Analyze security event with AI"""
        if not AI_AVAILABLE or not self.is_trained:
            return 0.5, {"method": "baseline"}
        
        try:
            features = self.extract_features(event_data)
            analysis = {"method": "ai", "models_used": []}
            
            threat_scores = []
            
            # Anomaly detection
            try:
                anomaly_score = self.anomaly_detector.decision_function([features])[0]
                normalized_score = max(0, min(1, (0.5 - anomaly_score) * 2))
                threat_scores.append(normalized_score)
                analysis["models_used"].append("isolation_forest")
                analysis["anomaly_score"] = float(normalized_score)
            except Exception as e:
                logging.debug(f"Anomaly detection error: {e}")
            
            # Classification
            try:
                features_scaled = self.scaler.transform([features])
                threat_prob = self.threat_classifier.predict_proba(features_scaled)[0][1]
                threat_scores.append(threat_prob)
                analysis["models_used"].append("random_forest")
                analysis["classification_score"] = float(threat_prob)
            except Exception as e:
                logging.debug(f"Classification error: {e}")
            
            # Neural network
            try:
                self.neural_detector.eval()
                with torch.no_grad():
                    features_tensor = torch.FloatTensor([features]).to(self.device)
                    nn_score = self.neural_detector(features_tensor).cpu().numpy()[0][0]
                    threat_scores.append(float(nn_score))
                    analysis["models_used"].append("neural_network")
                    analysis["neural_score"] = float(nn_score)
            except Exception as e:
                logging.debug(f"Neural network error: {e}")
            
            # Ensemble scoring
            if threat_scores:
                final_score = np.mean(threat_scores)
                analysis["ensemble_score"] = float(final_score)
                analysis["individual_scores"] = threat_scores
            else:
                final_score = 0.5
                analysis["ensemble_score"] = final_score
            
            return final_score, analysis
            
        except Exception as e:
            logging.error(f"AI analysis error: {e}")
            return 0.5, {"method": "fallback", "error": str(e)}

class AdaptiveEvasionAI:
    """AI-powered adaptive evasion system"""
    
    def __init__(self):
        self.detection_patterns = {}
        self.evasion_strategies = {}
        self.success_rates = {}
        
        if AI_AVAILABLE:
            self._init_nlp_model()
    
    def _init_nlp_model(self):
        """Initialize NLP model for pattern analysis"""
        try:
            self.sentence_model = SentenceTransformer('all-MiniLM-L6-v2')
            self.pattern_embeddings = {}
        except Exception as e:
            logging.warning(f"NLP model initialization error: {e}")
            self.sentence_model = None
    
    def learn_detection_pattern(self, pattern_description: str, detection_method: str):
        """Learn new detection patterns"""
        pattern_id = hashlib.md5(pattern_description.encode()).hexdigest()[:8]
        
        self.detection_patterns[pattern_id] = {
            'description': pattern_description,
            'method': detection_method,
            'first_seen': datetime.now(),
            'frequency': 1
        }
        
        if self.sentence_model:
            try:
                embedding = self.sentence_model.encode(pattern_description)
                self.pattern_embeddings[pattern_id] = embedding
            except Exception as e:
                logging.debug(f"Embedding generation error: {e}")
    
    def generate_evasion_strategy(self, current_environment: Dict) -> Dict:
        """Generate adaptive evasion strategy"""
        strategy = {
            'timestamp': datetime.now(),
            'tactics': [],
            'confidence': 0.0
        }
        
        # Analyze current environment
        env_score = self._analyze_environment(current_environment)
        
        # Select evasion tactics based on environment
        if env_score['vm_risk'] > 0.7:
            strategy['tactics'].extend([
                'delay_execution',
                'check_mouse_movement',
                'verify_user_interaction',
                'multi_stage_deployment'
            ])
        
        if env_score['sandbox_risk'] > 0.6:
            strategy['tactics'].extend([
                'time_based_evasion',
                'resource_exhaustion',
                'anti_emulation'
            ])
        
        if env_score['monitoring_risk'] > 0.5:
            strategy['tactics'].extend([
                'process_hollowing',
                'reflective_dll_loading',
                'encrypted_payloads'
            ])
        
        # Calculate confidence based on historical success
        strategy['confidence'] = self._calculate_strategy_confidence(strategy['tactics'])
        
        return strategy
    
    def _analyze_environment(self, environment: Dict) -> Dict:
        """Analyze environment for threats"""
        analysis = {
            'vm_risk': 0.0,
            'sandbox_risk': 0.0,
            'monitoring_risk': 0.0,
            'overall_risk': 0.0
        }
        
        # VM detection risk
        vm_indicators = environment.get('vm_indicators', {})
        vm_score = sum([
            0.3 if vm_indicators.get('vm_processes') else 0,
            0.2 if vm_indicators.get('vm_files') else 0,
            0.2 if vm_indicators.get('vm_registry') else 0,
            0.2 if vm_indicators.get('vm_hardware') else 0,
            0.1 if vm_indicators.get('vm_network') else 0
        ])
        analysis['vm_risk'] = min(1.0, vm_score)
        
        # Sandbox risk
        sandbox_indicators = environment.get('sandbox_indicators', {})
        sandbox_score = sum([
            0.4 if sandbox_indicators.get('limited_resources') else 0,
            0.3 if sandbox_indicators.get('artificial_activity') else 0,
            0.3 if sandbox_indicators.get('analysis_tools') else 0
        ])
        analysis['sandbox_risk'] = min(1.0, sandbox_score)
        
        # Monitoring risk
        monitoring_indicators = environment.get('monitoring_indicators', {})
        monitoring_score = sum([
            0.3 if monitoring_indicators.get('network_monitoring') else 0,
            0.3 if monitoring_indicators.get('process_monitoring') else 0,
            0.2 if monitoring_indicators.get('file_monitoring') else 0,
            0.2 if monitoring_indicators.get('registry_monitoring') else 0
        ])
        analysis['monitoring_risk'] = min(1.0, monitoring_score)
        
        # Overall risk calculation
        analysis['overall_risk'] = np.mean([
            analysis['vm_risk'],
            analysis['sandbox_risk'],
            analysis['monitoring_risk']
        ])
        
        return analysis
    
    def _calculate_strategy_confidence(self, tactics: List[str]) -> float:
        """Calculate confidence in evasion strategy"""
        if not tactics:
            return 0.0
        
        # Base confidence
        confidence = 0.5
        
        # Adjust based on historical success rates
        for tactic in tactics:
            success_rate = self.success_rates.get(tactic, 0.5)
            confidence = (confidence + success_rate) / 2
        
        # Boost for multiple tactics
        if len(tactics) > 3:
            confidence *= 1.2
        
        return min(1.0, confidence)

class AISecurityManager:
    """Main AI-powered security management system"""
    
    def __init__(self):
        self.logger = logging.getLogger('AISecurityManager')
        self.behavior_ai = BehaviorAnalysisAI()
        self.evasion_ai = AdaptiveEvasionAI()
        
        # Event storage and processing
        self.event_queue = queue.Queue(maxsize=10000)
        self.threat_profiles = {}
        self.security_events = []
        
        # Real-time monitoring
        self.monitoring_active = False
        self.monitoring_thread = None
        
        # Training data
        self.training_data = []
        self.auto_learning = True
        
        # Configuration
        self.config = {
            'threat_threshold': 0.7,
            'auto_response': True,
            'learning_rate': 0.1,
            'max_events_memory': 10000
        }
        
        self._start_monitoring()
    
    def _start_monitoring(self):
        """Start real-time security monitoring"""
        if not self.monitoring_active:
            self.monitoring_active = True
            self.monitoring_thread = threading.Thread(
                target=self._monitoring_worker,
                daemon=True
            )
            self.monitoring_thread.start()
            self.logger.info("AI Security monitoring started")
    
    def _monitoring_worker(self):
        """Background monitoring worker"""
        while self.monitoring_active:
            try:
                # Process events from queue
                try:
                    event_data = self.event_queue.get(timeout=1.0)
                    self._process_security_event(event_data)
                except queue.Empty:
                    continue
                
                # Periodic tasks
                self._periodic_analysis()
                
            except Exception as e:
                self.logger.error(f"Monitoring worker error: {e}")
            
            time.sleep(0.1)
    
    def _process_security_event(self, event_data: Dict):
        """Process individual security event"""
        try:
            # Extract basic info
            event = SecurityEvent(
                timestamp=datetime.now(),
                event_type=event_data.get('type', 'unknown'),
                severity=event_data.get('severity', 0.5),
                source_ip=event_data.get('source_ip', ''),
                details=event_data.get('details', {})
            )
            
            # AI analysis
            threat_score, ai_analysis = self.behavior_ai.analyze_event(event_data)
            event.predicted_threat = threat_score > self.config['threat_threshold']
            event.confidence = threat_score
            event.ai_analysis = ai_analysis
            
            # Update threat profile
            self._update_threat_profile(event)
            
            # Store event
            self.security_events.append(event)
            if len(self.security_events) > self.config['max_events_memory']:
                self.security_events.pop(0)
            
            # Auto-response if needed
            if event.predicted_threat and self.config['auto_response']:
                self._auto_respond_to_threat(event)
            
            # Learning
            if self.auto_learning:
                self._update_learning_data(event_data, event.predicted_threat)
            
        except Exception as e:
            self.logger.error(f"Event processing error: {e}")
    
    def _update_threat_profile(self, event: SecurityEvent):
        """Update threat profile for source IP"""
        ip = event.source_ip
        
        if ip not in self.threat_profiles:
            self.threat_profiles[ip] = ThreatProfile(
                ip=ip,
                behavior_vector=np.zeros(20),
                threat_score=0.0,
                attack_patterns=[],
                evasion_techniques=[],
                first_seen=event.timestamp,
                last_seen=event.timestamp,
                total_events=0
            )
        
        profile = self.threat_profiles[ip]
        profile.last_seen = event.timestamp
        profile.total_events += 1
        
        # Update threat score (exponential moving average)
        alpha = 0.3
        profile.threat_score = alpha * event.confidence + (1 - alpha) * profile.threat_score
        
        # Update behavior vector
        if 'behavior' in event.details:
            new_vector = self.behavior_ai.extract_features(event.details)
            profile.behavior_vector = alpha * new_vector + (1 - alpha) * profile.behavior_vector
    
    def _auto_respond_to_threat(self, event: SecurityEvent):
        """Automatically respond to detected threats"""
        try:
            response_actions = []
            
            # Determine response based on threat type and severity
            if event.confidence > 0.9:
                response_actions.extend([
                    'block_ip',
                    'isolate_connection',
                    'alert_admin'
                ])
            elif event.confidence > 0.7:
                response_actions.extend([
                    'rate_limit_ip',
                    'enhance_monitoring',
                    'log_detailed'
                ])
            
            # Execute responses
            for action in response_actions:
                self._execute_response_action(action, event)
            
            self.logger.warning(f"Auto-response executed for threat: {event.source_ip}")
            
        except Exception as e:
            self.logger.error(f"Auto-response error: {e}")
    
    def _execute_response_action(self, action: str, event: SecurityEvent):
        """Execute specific response action"""
        try:
            if action == 'block_ip':
                # Block IP (placeholder - implement actual blocking)
                self.logger.info(f"Blocking IP: {event.source_ip}")
            
            elif action == 'rate_limit_ip':
                # Rate limit IP
                self.logger.info(f"Rate limiting IP: {event.source_ip}")
            
            elif action == 'isolate_connection':
                # Isolate connection
                self.logger.info(f"Isolating connection from: {event.source_ip}")
            
            elif action == 'alert_admin':
                # Send alert to admin
                self.logger.critical(f"SECURITY ALERT: High threat from {event.source_ip}")
            
            elif action == 'enhance_monitoring':
                # Enhance monitoring for this IP
                self.logger.info(f"Enhanced monitoring for: {event.source_ip}")
            
            elif action == 'log_detailed':
                # Log detailed information
                self.logger.info(f"Detailed logging enabled for: {event.source_ip}")
        
        except Exception as e:
            self.logger.error(f"Response action error ({action}): {e}")
    
    def _update_learning_data(self, event_data: Dict, is_threat: bool):
        """Update learning data for model improvement"""
        self.training_data.append((event_data, is_threat))
        
        # Retrain periodically
        if len(self.training_data) % 100 == 0:
            threading.Thread(
                target=self._retrain_models,
                daemon=True
            ).start()
    
    def _retrain_models(self):
        """Retrain AI models with new data"""
        try:
            if len(self.training_data) > 50:
                self.behavior_ai.train_on_data(self.training_data[-1000:])  # Use last 1000 samples
                self.logger.info("AI models retrained with new data")
        except Exception as e:
            self.logger.error(f"Model retraining error: {e}")
    
    def _periodic_analysis(self):
        """Perform periodic security analysis"""
        try:
            current_time = time.time()
            
            # Run every 60 seconds
            if not hasattr(self, '_last_periodic') or current_time - self._last_periodic > 60:
                self._last_periodic = current_time
                
                # Analyze threat patterns
                self._analyze_threat_patterns()
                
                # Update evasion strategies
                self._update_evasion_strategies()
                
                # Cleanup old data
                self._cleanup_old_data()
        
        except Exception as e:
            self.logger.error(f"Periodic analysis error: {e}")
    
    def _analyze_threat_patterns(self):
        """Analyze patterns in threat data"""
        if not self.threat_profiles:
            return
        
        try:
            # Find most active threats
            active_threats = [
                profile for profile in self.threat_profiles.values()
                if profile.threat_score > 0.5 and profile.total_events > 5
            ]
            
            if active_threats:
                # Sort by threat score
                active_threats.sort(key=lambda x: x.threat_score, reverse=True)
                
                self.logger.info(f"Active threats detected: {len(active_threats)}")
                for threat in active_threats[:5]:  # Top 5
                    self.logger.warning(
                        f"High threat IP: {threat.ip} "
                        f"(score: {threat.threat_score:.3f}, events: {threat.total_events})"
                    )
        
        except Exception as e:
            self.logger.error(f"Threat pattern analysis error: {e}")
    
    def _update_evasion_strategies(self):
        """Update evasion strategies based on current environment"""
        try:
            # Simulate environment analysis
            current_environment = {
                'vm_indicators': {
                    'vm_processes': False,
                    'vm_files': False,
                    'vm_registry': False
                },
                'sandbox_indicators': {
                    'limited_resources': False,
                    'artificial_activity': False
                },
                'monitoring_indicators': {
                    'network_monitoring': True,  # Assume some monitoring
                    'process_monitoring': False
                }
            }
            
            strategy = self.evasion_ai.generate_evasion_strategy(current_environment)
            
            if strategy['confidence'] > 0.7:
                self.logger.info(f"Updated evasion strategy: {len(strategy['tactics'])} tactics")
            
        except Exception as e:
            self.logger.error(f"Evasion strategy update error: {e}")
    
    def _cleanup_old_data(self):
        """Clean up old data to prevent memory issues"""
        try:
            # Remove old threat profiles
            cutoff_time = datetime.now() - timedelta(hours=24)
            
            old_ips = [
                ip for ip, profile in self.threat_profiles.items()
                if profile.last_seen < cutoff_time and profile.threat_score < 0.3
            ]
            
            for ip in old_ips:
                del self.threat_profiles[ip]
            
            if old_ips:
                self.logger.debug(f"Cleaned up {len(old_ips)} old threat profiles")
        
        except Exception as e:
            self.logger.error(f"Data cleanup error: {e}")
    
    # Public API methods
    
    def report_security_event(self, event_data: Dict):
        """Report a security event for AI analysis"""
        try:
            self.event_queue.put(event_data, timeout=1.0)
        except queue.Full:
            self.logger.warning("Security event queue full, dropping event")
    
    def get_threat_assessment(self, ip: str) -> Dict:
        """Get threat assessment for specific IP"""
        if ip in self.threat_profiles:
            profile = self.threat_profiles[ip]
            return {
                'ip': ip,
                'threat_score': profile.threat_score,
                'total_events': profile.total_events,
                'first_seen': profile.first_seen.isoformat(),
                'last_seen': profile.last_seen.isoformat(),
                'attack_patterns': profile.attack_patterns,
                'evasion_techniques': profile.evasion_techniques
            }
        else:
            return {
                'ip': ip,
                'threat_score': 0.0,
                'status': 'unknown'
            }
    
    def get_security_summary(self) -> Dict:
        """Get overall security summary"""
        total_events = len(self.security_events)
        threat_events = sum(1 for event in self.security_events if event.predicted_threat)
        active_threats = len([p for p in self.threat_profiles.values() if p.threat_score > 0.5])
        
        return {
            'total_events': total_events,
            'threat_events': threat_events,
            'threat_rate': threat_events / max(1, total_events),
            'active_threats': active_threats,
            'monitoring_status': 'active' if self.monitoring_active else 'inactive',
            'ai_status': 'available' if AI_AVAILABLE else 'limited',
            'model_trained': self.behavior_ai.is_trained
        }
    
    def export_threat_intelligence(self, filepath: str):
        """Export threat intelligence data"""
        try:
            data = {
                'timestamp': datetime.now().isoformat(),
                'threat_profiles': {},
                'recent_events': [],
                'summary': self.get_security_summary()
            }
            
            # Export threat profiles
            for ip, profile in self.threat_profiles.items():
                data['threat_profiles'][ip] = {
                    'threat_score': profile.threat_score,
                    'total_events': profile.total_events,
                    'first_seen': profile.first_seen.isoformat(),
                    'last_seen': profile.last_seen.isoformat(),
                    'attack_patterns': profile.attack_patterns
                }
            
            # Export recent events
            for event in self.security_events[-100:]:  # Last 100 events
                data['recent_events'].append({
                    'timestamp': event.timestamp.isoformat(),
                    'type': event.event_type,
                    'source_ip': event.source_ip,
                    'threat_score': event.confidence,
                    'predicted_threat': event.predicted_threat
                })
            
            # Save to file
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
            
            self.logger.info(f"Threat intelligence exported to {filepath}")
            
        except Exception as e:
            self.logger.error(f"Export error: {e}")
    
    def stop_monitoring(self):
        """Stop security monitoring"""
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5.0)
        self.logger.info("AI Security monitoring stopped")

# Global instance
ai_security_manager = None

def get_ai_security_manager() -> AISecurityManager:
    """Get global AI security manager instance"""
    global ai_security_manager
    if ai_security_manager is None:
        ai_security_manager = AISecurityManager()
    return ai_security_manager

def initialize_ai_security():
    """Initialize AI security system"""
    try:
        manager = get_ai_security_manager()
        logging.info("AI Security system initialized successfully")
        return manager
    except Exception as e:
        logging.error(f"Failed to initialize AI Security: {e}")
        return None

if __name__ == "__main__":
    # Test the AI security system
    logging.basicConfig(level=logging.INFO)
    
    manager = initialize_ai_security()
    
    if manager:
        # Simulate some security events
        test_events = [
            {
                'type': 'connection',
                'source_ip': '192.168.1.100',
                'severity': 0.3,
                'details': {
                    'connection': {'packet_size': 1024, 'frequency': 10},
                    'behavior': {'command_diversity': 2},
                    'system': {'cpu_usage': 20}
                }
            },
            {
                'type': 'suspicious_activity',
                'source_ip': '10.0.0.5',
                'severity': 0.8,
                'details': {
                    'connection': {'packet_size': 8192, 'frequency': 50},
                    'behavior': {'command_diversity': 8, 'privilege_escalation_attempts': 3},
                    'system': {'vm_detected': True, 'cpu_usage': 80}
                }
            }
        ]
        
        for event in test_events:
            manager.report_security_event(event)
        
        # Wait a bit for processing
        time.sleep(2)
        
        # Print summary
        summary = manager.get_security_summary()
        print(f"Security Summary: {json.dumps(summary, indent=2)}")
        
        # Print threat assessments
        for ip in ['192.168.1.100', '10.0.0.5']:
            assessment = manager.get_threat_assessment(ip)
            print(f"Threat Assessment for {ip}: {json.dumps(assessment, indent=2)}")
