import os
import json
import csv
import yaml
import xml.etree.ElementTree as ET
from typing import List, Dict, Optional, Generator, Any, Set
import threading
from functools import lru_cache
import mmap
from collections import deque, defaultdict
import io
import time
import schedule
import psutil
from datetime import datetime

class HostGroup:
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.hosts: Set[str] = set()  # Set of host IDs
        self.tags: Set[str] = set()
        self.created_at = datetime.now()
        self.updated_at = datetime.now()

    def add_host(self, host_id: str) -> None:
        self.hosts.add(host_id)
        self.updated_at = datetime.now()

    def remove_host(self, host_id: str) -> None:
        self.hosts.discard(host_id)
        self.updated_at = datetime.now()

    def add_tag(self, tag: str) -> None:
        self.tags.add(tag)
        self.updated_at = datetime.now()

    def remove_tag(self, tag: str) -> None:
        self.tags.discard(tag)
        self.updated_at = datetime.now()

class ScheduledTask:
    def __init__(self, task_id: str, command: str, schedule_type: str,
                 target_hosts: List[str], parameters: Dict = None):
        self.task_id = task_id
        self.command = command
        self.schedule_type = schedule_type  # once, interval, cron
        self.target_hosts = target_hosts
        self.parameters = parameters or {}
        self.created_at = datetime.now()
        self.last_run = None
        self.next_run = None
        self.status = "pending"  # pending, running, completed, failed
        self.results = []

class HostManager:
    def __init__(self, max_hosts: int = 10000):
        self.hosts = deque(maxlen=max_hosts)
        self.config_dir = "config"
        self.supported_formats = ['txt', 'json', 'csv', 'yaml', 'xml']
        self.file_cache = {}
        self.cache_lock = threading.Lock()
        self.cache_timeout = 300

        # Bot management
        self.groups: Dict[str, HostGroup] = {}
        self.tags: Dict[str, Set[str]] = defaultdict(set)  # tag -> host_ids
        self.host_tags: Dict[str, Set[str]] = defaultdict(set)  # host_id -> tags

        # Task scheduling
        self.scheduled_tasks: Dict[str, ScheduledTask] = {}
        self.task_scheduler = schedule.Scheduler()
        self.scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.scheduler_thread.start()

        # Resource monitoring
        self.resource_stats: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        self.monitoring_interval = 60  # seconds
        self.monitoring_thread = threading.Thread(target=self._monitor_resources, daemon=True)
        self.monitoring_thread.start()

        # Health checking
        self.health_status: Dict[str, Dict] = {}
        self.health_check_interval = 300  # seconds
        self.health_check_thread = threading.Thread(target=self._health_check_loop, daemon=True)
        self.health_check_thread.start()

        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir)
            
    # Group Management
    def create_group(self, name: str, description: str = "") -> bool:
        """Create a new host group"""
        if name in self.groups:
            return False
        self.groups[name] = HostGroup(name, description)
        return True

    def delete_group(self, name: str) -> bool:
        """Delete a host group"""
        if name not in self.groups:
            return False
        del self.groups[name]
        return True

    def add_to_group(self, group_name: str, host_ids: List[str]) -> bool:
        """Add hosts to a group"""
        if group_name not in self.groups:
            return False
        for host_id in host_ids:
            self.groups[group_name].add_host(host_id)
        return True

    def remove_from_group(self, group_name: str, host_ids: List[str]) -> bool:
        """Remove hosts from a group"""
        if group_name not in self.groups:
            return False
        for host_id in host_ids:
            self.groups[group_name].remove_host(host_id)
        return True

    # Tag Management
    def add_tags(self, host_id: str, tags: List[str]) -> None:
        """Add tags to a host"""
        for tag in tags:
            self.tags[tag].add(host_id)
            self.host_tags[host_id].add(tag)

    def remove_tags(self, host_id: str, tags: List[str]) -> None:
        """Remove tags from a host"""
        for tag in tags:
            self.tags[tag].discard(host_id)
            self.host_tags[host_id].discard(tag)

    def get_hosts_by_tag(self, tag: str) -> List[str]:
        """Get hosts with specific tag"""
        return list(self.tags.get(tag, set()))

    def get_host_tags(self, host_id: str) -> List[str]:
        """Get tags for a specific host"""
        return list(self.host_tags.get(host_id, set()))

    # Batch Command Execution
    def execute_batch_command(self, command: str, target: str, parameters: Dict = None) -> str:
        """Execute command on multiple hosts based on target (group/tag/list)"""
        task_id = f"batch_{int(time.time())}"
        target_hosts = []

        if target.startswith("group:"):
            group_name = target[6:]
            if group_name in self.groups:
                target_hosts = list(self.groups[group_name].hosts)
        elif target.startswith("tag:"):
            tag = target[4:]
            target_hosts = self.get_hosts_by_tag(tag)
        else:
            target_hosts = target.split(",")

        task = ScheduledTask(task_id, command, "once", target_hosts, parameters)
        self.scheduled_tasks[task_id] = task
        self._execute_task(task)
        return task_id

    # Task Scheduling
    def schedule_task(self, command: str, schedule_type: str, target_hosts: List[str],
                     parameters: Dict = None) -> str:
        """Schedule a task for execution"""
        task_id = f"scheduled_{int(time.time())}"
        task = ScheduledTask(task_id, command, schedule_type, target_hosts, parameters)
        self.scheduled_tasks[task_id] = task

        if schedule_type == "interval":
            interval = parameters.get("interval", 3600)  # default 1 hour
            self.task_scheduler.every(interval).seconds.do(
                self._execute_task, task
            )
        elif schedule_type == "cron":
            cron = parameters.get("cron", "0 * * * *")  # default every hour
            self.task_scheduler.every().cron(cron).do(
                self._execute_task, task
            )

        return task_id

    def _execute_task(self, task: ScheduledTask) -> None:
        """Execute a scheduled task"""
        task.status = "running"
        task.last_run = datetime.now()
        try:
            # Execute command on each target host
            for host_id in task.target_hosts:
                host = self.get_host(host_id)
                if host:
                    # TODO: Implement actual command execution
                    result = {"host_id": host_id, "status": "success"}
                    task.results.append(result)
            task.status = "completed"
        except Exception as e:
            task.status = "failed"
            task.results.append({"error": str(e)})

    def _run_scheduler(self) -> None:
        """Run the task scheduler"""
        while True:
            self.task_scheduler.run_pending()
            time.sleep(1)

    # Resource Monitoring
    def _monitor_resources(self) -> None:
        """Monitor system resources of hosts"""
        while True:
            try:
                for host in self.hosts:
                    host_id = host['id']
                    # TODO: Implement actual resource monitoring
                    stats = {
                        'cpu': psutil.cpu_percent(),
                        'memory': psutil.virtual_memory().percent,
                        'disk': psutil.disk_usage('/').percent,
                        'timestamp': datetime.now()
                    }
                    self.resource_stats[host_id].append(stats)
            except Exception as e:
                print(f"Error monitoring resources: {str(e)}")
            time.sleep(self.monitoring_interval)

    def get_resource_stats(self, host_id: str, timeframe: str = "1h") -> List[Dict]:
        """Get resource statistics for a host"""
        if host_id not in self.resource_stats:
            return []
        return list(self.resource_stats[host_id])

    # Health Checks
    def _health_check_loop(self) -> None:
        """Perform periodic health checks"""
        while True:
            try:
                for host in self.hosts:
                    host_id = host['id']
                    status = self._check_host_health(host)
                    self.health_status[host_id] = {
                        'status': status,
                        'last_check': datetime.now()
                    }
            except Exception as e:
                print(f"Error in health check: {str(e)}")
            time.sleep(self.health_check_interval)

    def _check_host_health(self, host: Dict) -> str:
        """Check health of a single host"""
        # TODO: Implement actual health checks
        return "healthy"

    def get_health_status(self, host_id: str) -> Dict:
        """Get health status for a host"""
        return self.health_status.get(host_id, {
            'status': 'unknown',
            'last_check': None
        })

    def add_host(self, host: Dict):
        """Thêm host mới"""
        if self._validate_host(host):
            self.hosts.append(host)
            return True
        return False
        
    def remove_host(self, host_id: str):
        """Xóa host"""
        self.hosts = [h for h in self.hosts if h['id'] != host_id]
        
    def get_host(self, host_id: str) -> Dict:
        """Lấy thông tin host"""
        return next((h for h in self.hosts if h['id'] == host_id), None)
        
    def get_hosts(self) -> Generator[Dict, None, None]:
        """Lấy danh sách host dạng generator để tiết kiệm memory"""
        return (host for host in self.hosts)
        
    def load_hosts(self, filename: str):
        """Load hosts từ file với caching"""
        if not os.path.exists(filename):
            return False
            
        file_ext = filename.split('.')[-1].lower()
        if file_ext not in self.supported_formats:
            return False
            
        try:
            # Check cache first
            with self.cache_lock:
                cache_key = f"{filename}_{os.path.getmtime(filename)}"
                if cache_key in self.file_cache:
                    self.hosts = deque(self.file_cache[cache_key], maxlen=self.hosts.maxlen)
                    return True
                    
            # Load file with memory mapping for large files
            with open(filename, 'rb') as f:
                mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
                if file_ext == 'txt':
                    self._load_from_txt(mm)
                elif file_ext == 'json':
                    self._load_from_json(mm)
                elif file_ext == 'csv':
                    self._load_from_csv(mm)
                elif file_ext == 'yaml':
                    self._load_from_yaml(mm)
                elif file_ext == 'xml':
                    self._load_from_xml(mm)
                    
            # Update cache
            with self.cache_lock:
                self.file_cache[cache_key] = list(self.hosts)
                
            return True
            
        except Exception as e:
            print(f"Error loading hosts: {str(e)}")
            return False
            
    def save_hosts(self, filename: str):
        """Lưu hosts ra file"""
        file_ext = filename.split('.')[-1].lower()
        if file_ext not in self.supported_formats:
            return False
            
        try:
            if file_ext == 'txt':
                self._save_to_txt(filename)
            elif file_ext == 'json':
                self._save_to_json(filename)
            elif file_ext == 'csv':
                self._save_to_csv(filename)
            elif file_ext == 'yaml':
                self._save_to_yaml(filename)
            elif file_ext == 'xml':
                self._save_to_xml(filename)
                
            return True
            
        except Exception as e:
            print(f"Error saving hosts: {str(e)}")
            return False
            
    def _load_from_txt(self, mm: mmap.mmap):
        """Load từ text file với memory mapping"""
        for line in iter(mm.readline, b''):
            try:
                line = line.decode('utf-8')
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                    
                if '@' in line:
                    # Format: user@host:port password
                    try:
                        auth, password = line.split(' ', 1)
                        if ':' in auth:
                            userhost, port = auth.rsplit(':', 1)
                        else:
                            userhost, port = auth, '22'
                            
                        if '@' in userhost:
                            username, hostname = userhost.split('@', 1)
                        else:
                            username, hostname = None, userhost
                            
                        host = {
                            'id': f"{hostname}:{port}",
                            'hostname': hostname,
                            'port': int(port),
                            'username': username,
                            'password': password if password else None
                        }
                        self.add_host(host)
                    except Exception:
                        continue
            except UnicodeDecodeError:
                continue
                    
    def _load_from_json(self, mm: mmap.mmap):
        """Load từ JSON file với streaming parser"""
        data = json.loads(mm.read().decode('utf-8'))
        for host in data:
            self.add_host(host)
                
    def _load_from_csv(self, mm: mmap.mmap):
        """Load từ CSV file với chunk processing"""
        text = io.TextIOWrapper(io.BytesIO(mm.read()))
        reader = csv.DictReader(text)
        chunk_size = 1000
        chunk = []
        
        for row in reader:
            chunk.append(row)
            if len(chunk) >= chunk_size:
                for host in chunk:
                    self.add_host(host)
                chunk = []
                
        # Process remaining
        for host in chunk:
            self.add_host(host)
                
    def _load_from_yaml(self, mm: mmap.mmap):
        """Load từ YAML file với streaming"""
        data = yaml.safe_load(mm)
        for host in data:
            self.add_host(host)
                
    def _load_from_xml(self, mm: mmap.mmap):
        """Load từ XML file với iterative parsing"""
        context = ET.iterparse(io.BytesIO(mm.read()), events=('end',))
        
        # Clear root element to save memory
        context = iter(context)
        _, root = next(context)
        
        for event, elem in context:
            if elem.tag == 'host':
                host = {}
                for child in elem:
                    host[child.tag] = child.text
                self.add_host(host)
                
                # Clear element
                elem.clear()
                root.clear()
            
    def _save_to_txt(self, filename: str):
        """Lưu ra text file"""
        with open(filename, 'w') as f:
            for host in self.hosts:
                auth = f"{host['username']}@{host['hostname']}:{host['port']}"
                pwd = host.get('password', '')
                f.write(f"{auth} {pwd}\n")
                
    def _save_to_json(self, filename: str):
        """Lưu ra JSON file"""
        with open(filename, 'w') as f:
            json.dump(self.hosts, f, indent=2)
            
    def _save_to_csv(self, filename: str):
        """Lưu ra CSV file"""
        if not self.hosts:
            return
            
        fieldnames = self.hosts[0].keys()
        with open(filename, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.hosts)
            
    def _save_to_yaml(self, filename: str):
        """Lưu ra YAML file"""
        with open(filename, 'w') as f:
            yaml.safe_dump(self.hosts, f)
            
    def _save_to_xml(self, filename: str):
        """Lưu ra XML file"""
        root = ET.Element('hosts')
        
        for host in self.hosts:
            host_elem = ET.SubElement(root, 'host')
            for key, value in host.items():
                child = ET.SubElement(host_elem, key)
                child.text = str(value)
                
        tree = ET.ElementTree(root)
        tree.write(filename)
        
    def _validate_host(self, host: Dict) -> bool:
        """Validate thông tin host"""
        required = ['hostname', 'port']
        return all(key in host for key in required)
        
    def import_from_nmap(self, xml_file: str):
        """Import hosts từ nmap XML output với iterative parsing"""
        try:
            context = ET.iterparse(xml_file, events=('end',))
            context = iter(context)
            _, root = next(context)
            
            for host in root.findall('.//host'):
                addr = host.find('.//address').get('addr')
                ports = host.findall('.//port')
                
                for port in ports:
                    if port.find('.//service').get('name') == 'ssh':
                        port_num = port.get('portid')
                        self.add_host({
                            'id': f"{addr}:{port_num}",
                            'hostname': addr,
                            'port': int(port_num)
                        })
                        break
                        
            return True
            
        except Exception as e:
            print(f"Error importing nmap data: {str(e)}")
            return False