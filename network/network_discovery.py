from __future__ import annotations
import os
import netifaces
import netaddr
import nmap
import scapy.all as scapy
import threading
import time
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Set, Any, Tuple
from pathlib import Path
from dataclasses import dataclass, field
import socket
import struct
import hashlib
from collections import defaultdict

# AI imports for intelligent network analysis
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.cluster import KMeans, DBSCAN
from sklearn.preprocessing import StandardScaler
from sklearn.neural_network import MLPClassifier
import joblib

@dataclass
class Service:
    """Thông tin về service"""
    name: str
    version: Optional[str] = None
    product: Optional[str] = None
    extra_info: Optional[str] = None
    tunnel: Optional[str] = None
    protocol: str = "tcp"
    confidence: int = 0

@dataclass
class DeviceFingerprint:
    """Thông tin fingerprint của thiết bị"""
    os_match: Optional[str] = None
    os_accuracy: int = 0
    os_family: Optional[str] = None
    os_generation: Optional[str] = None
    device_type: Optional[str] = None
    vendor: Optional[str] = None
    ttl: Optional[int] = None
    mtu: Optional[int] = None
    uptime: Optional[float] = None

@dataclass
class HostChange:
    """Thay đổi của host theo thời gian"""
    timestamp: datetime
    change_type: str  # new, modified, offline
    old_state: Optional[Dict] = None
    new_state: Optional[Dict] = None

@dataclass
class Host:
    """Thông tin chi tiết về host"""
    ip: str
    mac: Optional[str] = None
    hostname: Optional[str] = None
    fingerprint: DeviceFingerprint = field(default_factory=DeviceFingerprint)
    open_ports: Set[int] = field(default_factory=set)
    services: Dict[int, Service] = field(default_factory=dict)
    last_seen: Optional[float] = None
    first_seen: Optional[float] = None
    changes: List[HostChange] = field(default_factory=list)
    importance_score: int = 0
    tags: Set[str] = field(default_factory=set)
    
    def update_from_scan(self, scan_data: Dict) -> bool:
        """Cập nhật thông tin từ scan mới

        Returns:
            bool: True if host was modified
        """
        modified = False
        old_state = self.to_dict()
        
        # Update basic info
        if 'mac' in scan_data and scan_data['mac'] != self.mac:
            self.mac = scan_data['mac']
            modified = True
            
        if 'hostname' in scan_data and scan_data['hostname'] != self.hostname:
            self.hostname = scan_data['hostname']
            modified = True
            
        # Update fingerprint
        if 'fingerprint' in scan_data:
            fp_data = scan_data['fingerprint']
            fp = self.fingerprint
            
            if fp_data.get('os_match') and fp_data['os_match'] != fp.os_match:
                fp.os_match = fp_data['os_match']
                fp.os_accuracy = fp_data.get('os_accuracy', 0)
                modified = True
                
            if fp_data.get('os_family') and fp_data['os_family'] != fp.os_family:
                fp.os_family = fp_data['os_family']
                modified = True
                
            if fp_data.get('device_type') and fp_data['device_type'] != fp.device_type:
                fp.device_type = fp_data['device_type']
                modified = True
                
        # Update ports and services
        new_ports = set(scan_data.get('open_ports', []))
        if new_ports != self.open_ports:
            self.open_ports = new_ports
            modified = True
            
        for port, service_data in scan_data.get('services', {}).items():
            port = int(port)
            if port not in self.services or self.services[port].version != service_data.get('version'):
                self.services[port] = Service(**service_data)
                modified = True
                
        # Record change if modified
        if modified:
            self.changes.append(HostChange(
                timestamp=datetime.now(),
                change_type='modified',
                old_state=old_state,
                new_state=self.to_dict()
            ))
            
        return modified
        
    def calculate_importance(self) -> int:
        """Tính điểm importance của host"""
        score = 0
        
        # OS type
        if self.fingerprint.os_match:
            if 'server' in self.fingerprint.os_match.lower():
                score += 50
            elif 'controller' in self.fingerprint.os_match.lower():
                score += 40
                
        # Services
        for port, service in self.services.items():
            if service.name in ['http', 'https']:
                score += 30
            elif service.name in ['mysql', 'mssql', 'oracle']:
                score += 40
            elif service.name in ['domain', 'dns']:
                score += 35
            elif service.name in ['smb', 'netbios']:
                score += 25
                
        # Uptime
        if self.fingerprint.uptime and self.fingerprint.uptime > 30 * 24 * 3600:  # 30 days
            score += 20
            
        # Activity
        if len(self.changes) > 10:
            score += 15
            
        self.importance_score = score
        return score
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'ip': self.ip,
            'mac': self.mac,
            'hostname': self.hostname,
            'fingerprint': {
                'os_match': self.fingerprint.os_match,
                'os_accuracy': self.fingerprint.os_accuracy,
                'os_family': self.fingerprint.os_family,
                'os_generation': self.fingerprint.os_generation,
                'device_type': self.fingerprint.device_type,
                'vendor': self.fingerprint.vendor,
                'ttl': self.fingerprint.ttl,
                'mtu': self.fingerprint.mtu,
                'uptime': self.fingerprint.uptime
            },
            'open_ports': sorted(list(self.open_ports)),
            'services': {
                port: {
                    'name': svc.name,
                    'version': svc.version,
                    'product': svc.product,
                    'extra_info': svc.extra_info,
                    'protocol': svc.protocol,
                    'confidence': svc.confidence
                }
                for port, svc in self.services.items()
            },
            'first_seen': self.first_seen,
            'last_seen': self.last_seen,
            'importance_score': self.importance_score,
            'tags': sorted(list(self.tags))
        }

class NetworkDiscovery:
    def __init__(self, save_dir: str = "network_data") -> None:
        self.nmap = nmap.PortScanner()
        self.hosts: Dict[str, Host] = {}
        self.running = False
        self.save_dir = Path(save_dir)
        self.logger = logging.getLogger(__name__)
        
        # Scan configuration
        self.scan_config = {
            'quick': {
                'ports': '21-23,25,53,80,110,139,443,445,3306,3389',
                'arguments': '-sS -sV -O --version-intensity 5'
            },
            'thorough': {
                'ports': '1-1024,1433,1521,3306,3389,5432,5900,6379,8080,8443,27017',
                'arguments': '-sS -sV -O -A --version-intensity 7'
            }
        }
        
        # Network structure
        self.subnets: Dict[str, Set[str]] = defaultdict(set)
        self.gateways: Set[str] = set()
        self.domains: Dict[str, Set[str]] = defaultdict(set)
        
        # AI Components for intelligent network analysis
        self.ai_target_classifier = None
        self.ai_vulnerability_predictor = None
        self.ai_network_clusterer = None
        self.ai_scaler = StandardScaler()
        self.target_history = []
        self.vulnerability_history = []
        self.network_patterns = []
        
        # Initialize AI models
        self._init_ai_models()
        
        # Create save directory
        self.save_dir.mkdir(parents=True, exist_ok=True)
        
    def start_discovery(self, scan_type: str = 'quick') -> bool:
        """Bắt đầu quá trình discovery"""
        if self.running:
            return False
            
        try:
            if scan_type not in self.scan_config:
                scan_type = 'quick'
                
            self.running = True
            self.discovery_thread = threading.Thread(
                target=self._discovery_loop,
                args=(scan_type,)
            )
            self.discovery_thread.daemon = True
            self.discovery_thread.start()
            
            self.logger.info(f"Network discovery started with {scan_type} scan")
            return True
            
        except Exception as e:
            self.logger.error(f"Error starting discovery: {str(e)}")
            self.running = False
            return False
            
    def stop_discovery(self) -> None:
        """Dừng quá trình discovery"""
        self.running = False
        self.save_network_data()
        
    def _discovery_loop(self, scan_type: str) -> None:
        """Vòng lặp chính của discovery"""
        while self.running:
            try:
                start_time = time.time()
                
                # Get network interfaces
                interfaces = self._get_interfaces()
                
                # Scan each subnet
                for interface in interfaces:
                    network = interface['network']
                    self._scan_network(network, scan_type)
                    
                # Update network structure
                self._analyze_topology()
                
                # Update host scores
                self._update_host_scores()
                
                # Cleanup old hosts
                self._cleanup_old_hosts()
                
                # Save results
                self.save_network_data()
                
                # Calculate next scan delay
                scan_time = time.time() - start_time
                wait_time = max(300 - scan_time, 60)  # At least 1 minute, at most 5 minutes
                
                time.sleep(wait_time)
                
            except Exception as e:
                self.logger.error(f"Discovery loop error: {str(e)}")
                time.sleep(60)
                
    def _get_interfaces(self) -> List[Dict[str, str]]:
        """Lấy thông tin các interface mạng"""
        interfaces = []
        try:
            for interface in netifaces.interfaces():
                try:
                    addrs = netifaces.ifaddresses(interface)
                    if netifaces.AF_INET not in addrs:
                        continue
                        
                    ip = addrs[netifaces.AF_INET][0]['addr']
                    netmask = addrs[netifaces.AF_INET][0]['netmask']
                    
                    # Skip loopback
                    if ip.startswith('127.'):
                        continue
                        
                    # Calculate network
                    network = netaddr.IPNetwork(f"{ip}/{netmask}")
                    
                    interfaces.append({
                        'name': interface,
                        'ip': ip,
                        'netmask': netmask,
                        'network': str(network.network) + '/' + str(network.prefixlen),
                        'broadcast': str(network.broadcast)
                    })
                    
                except Exception as e:
                    self.logger.error(f"Error processing interface {interface}: {str(e)}")
                    continue
                    
            return interfaces
            
        except Exception as e:
            self.logger.error(f"Error getting interfaces: {str(e)}")
            return []
            
    def _scan_network(self, network: str, scan_type: str) -> None:
        """Quét một subnet"""
        try:
            current_time = time.time()
            
            # ARP scan for live hosts
            ans, _ = scapy.arping(network, timeout=2, verbose=False)
            
            # Process responses
            for sent, recv in ans:
                ip = recv.psrc
                mac = recv.hwsrc
                
                # Create or update host
                if ip not in self.hosts:
                    host = Host(ip=ip, mac=mac)
                    host.first_seen = current_time
                    host.changes.append(HostChange(
                        timestamp=datetime.now(),
                        change_type='new'
                    ))
                    self.hosts[ip] = host
                else:
                    host = self.hosts[ip]
                    host.mac = mac
                    
                host.last_seen = current_time
                
                # Detailed scan
                self._scan_host(host, scan_type)
                
            # Add subnet to topology
            subnet = str(netaddr.IPNetwork(network).network)
            for ip in [h.ip for h in self.hosts.values()]:
                if netaddr.IPAddress(ip) in netaddr.IPNetwork(network):
                    self.subnets[subnet].add(ip)
                    
        except Exception as e:
            self.logger.error(f"Error scanning network {network}: {str(e)}")
            
    def _scan_host(self, host: Host, scan_type: str) -> None:
        """Quét chi tiết một host"""
        try:
            config = self.scan_config[scan_type]
            
            # Nmap scan
            self.nmap.scan(
                host.ip,
                ports=config['ports'],
                arguments=config['arguments']
            )
            
            if host.ip in self.nmap.all_hosts():
                host_data = self.nmap[host.ip]
                scan_data = {}
                
                # Get hostname
                if 'hostnames' in host_data and host_data['hostnames']:
                    scan_data['hostname'] = host_data['hostnames'][0]['name']
                    
                # OS detection
                if 'osmatch' in host_data and host_data['osmatch']:
                    os_data = host_data['osmatch'][0]
                    scan_data['fingerprint'] = {
                        'os_match': os_data['name'],
                        'os_accuracy': int(os_data['accuracy']),
                        'os_family': os_data.get('osclass', [{}])[0].get('osfamily'),
                        'os_generation': os_data.get('osclass', [{}])[0].get('osgen'),
                        'device_type': os_data.get('osclass', [{}])[0].get('type')
                    }
                      # Ports and services
                scan_data['open_ports'] = []
                scan_data['services'] = {}
                if 'tcp' in host_data:
                    for port, data in host_data['tcp'].items():
                        if data['state'] == 'open':
                            port = int(port)
                            scan_data['open_ports'].append(port)
                            
                            scan_data['services'][port] = {
                                'name': data['name'],
                                'product': data.get('product'),
                                'version': data.get('version'),
                                'extra_info': data.get('extrainfo'),
                                'protocol': 'tcp',
                                'confidence': int(data.get('conf', 0))
                            }
                            
                # Update host
                host.update_from_scan(scan_data)
                
                # Special tag detection
                if any(s.name == 'domain' for s in host.services.values()):
                    host.tags.add('dns-server')
                if any(s.name in ['http', 'https'] for s in host.services.values()):
                    host.tags.add('web-server')
                    
        except Exception as e:
            self.logger.error(f"Error scanning host {host.ip}: {str(e)}")
            
    def _analyze_topology(self) -> None:
        """Phân tích topology mạng"""
        try:
            # Reset network structure
            self.gateways.clear()
            self.domains.clear()
            
            # Detect gateways
            gateways = netifaces.gateways()
            if 'default' in gateways and netifaces.AF_INET in gateways['default']:
                gateway_ip = gateways['default'][netifaces.AF_INET][0]
                if gateway_ip in self.hosts:
                    self.gateways.add(gateway_ip)
                    self.hosts[gateway_ip].tags.add('gateway')
                    
            # Group hosts by domain
            for host in self.hosts.values():
                if host.hostname:
                    domain = '.'.join(host.hostname.split('.')[-2:])
                    self.domains[domain].add(host.ip)
                    
            # Detect key infrastructure
            for host in self.hosts.values():
                services = {s.name for s in host.services.values()}
                
                if 'domain' in services:
                    self.hosts[host.ip].tags.add('dns-server')
                if {'netbios-ssn', 'microsoft-ds'} & services:
                    self.hosts[host.ip].tags.add('file-server')
                if {'ms-sql', 'oracle', 'mysql'} & services:
                    self.hosts[host.ip].tags.add('database')
                if {'ldap', 'kerberos'} & services:
                    self.hosts[host.ip].tags.add('directory-service')
                    
        except Exception as e:
            self.logger.error(f"Error analyzing topology: {str(e)}")
            
    def _update_host_scores(self) -> None:
        """Cập nhật importance scores"""
        for host in self.hosts.values():
            host.calculate_importance()
            
    def _cleanup_old_hosts(self, max_age: float = 3600) -> None:
        """Xóa hosts không hoạt động"""
        current_time = time.time()
        
        for ip in list(self.hosts.keys()):
            host = self.hosts[ip]
            if current_time - host.last_seen > max_age:
                # Record offline status
                host.changes.append(HostChange(
                    timestamp=datetime.now(),
                    change_type='offline'
                ))
                # Remove host
                del self.hosts[ip]
                
    def get_network_map(self) -> Dict[str, Any]:
        """Lấy network map hiện tại"""
        return {
            'hosts': {ip: host.to_dict() for ip, host in self.hosts.items()},
            'subnets': {subnet: list(hosts) for subnet, hosts in self.subnets.items()},
            'gateways': list(self.gateways),
            'domains': {domain: list(hosts) for domain, hosts in self.domains.items()},
            'timestamp': datetime.now().isoformat()
        }
        
    def save_network_data(self) -> Optional[str]:
        """Lưu network data ra file"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = self.save_dir / f"network_map_{timestamp}.json"
            
            with open(filename, 'w') as f:
                json.dump(self.get_network_map(), f, indent=2)
                
            self.logger.info(f"Saved network data to {filename}")
            return str(filename)
            
        except Exception as e:
            self.logger.error(f"Error saving network data: {str(e)}")
            return None
            
    def get_statistics(self) -> Dict[str, Any]:
        """Lấy thống kê về mạng"""
        stats = {
            'total_hosts': len(self.hosts),
            'active_hosts': sum(1 for h in self.hosts.values() 
                              if time.time() - h.last_seen < 300),
            'os_distribution': defaultdict(int),
            'device_types': defaultdict(int),
            'services': defaultdict(int),
            'subnets': len(self.subnets),
            'domains': len(self.domains),
            'tagged_hosts': {
                tag: sum(1 for h in self.hosts.values() if tag in h.tags)
                for tag in {'gateway', 'dns-server', 'web-server', 
                          'file-server', 'database', 'directory-service'}
            },
            'top_hosts': sorted(
                [h.to_dict() for h in self.hosts.values()],
                key=lambda x: x['importance_score'],
                reverse=True
            )[:10]
        }
        
        try:
            for host in self.hosts.values():
                if host.fingerprint.os_family:
                    stats['os_distribution'][host.fingerprint.os_family] += 1
                if host.fingerprint.device_type:
                    stats['device_types'][host.fingerprint.device_type] += 1
                    
                for service in host.services.values():
                    stats['services'][service.name] += 1
                    
            return stats
            
        except Exception as e:
            self.logger.error(f"Error calculating statistics: {str(e)}")
            return stats
    
    def _init_ai_models(self):
        """Initialize AI models for network analysis"""
        try:
            # Target classification AI
            self.ai_target_classifier = RandomForestClassifier(
                n_estimators=100,
                max_depth=12,
                random_state=42
            )
            
            # Vulnerability prediction AI
            self.ai_vulnerability_predictor = MLPClassifier(
                hidden_layer_sizes=(80, 40),
                max_iter=1000,
                random_state=42
            )
            
            # Network clustering AI
            self.ai_network_clusterer = KMeans(
                n_clusters=5,
                random_state=42
            )
            
            self.logger.info("AI network analysis models initialized")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize AI models: {e}")
    
    def ai_analyze_target_value(self, host: Host) -> Dict[str, Any]:
        """Use AI to analyze target value and potential"""
        try:
            features = self._extract_host_features(host)
            
            analysis = {
                'value_score': 0.0,
                'attack_potential': 'low',
                'recommended_attacks': [],
                'vulnerability_score': 0.0,
                'priority_level': 1
            }
            
            # Calculate base value score
            value_score = self._calculate_traditional_value(host)
            
            # AI enhancement if model is trained
            if hasattr(self.ai_target_classifier, 'predict_proba') and len(self.target_history) > 50:
                try:
                    ai_score = self.ai_target_classifier.predict_proba([features])[0][1]
                    value_score = (value_score + ai_score * 100) / 2
                except Exception as e:
                    self.logger.error(f"AI target classification failed: {e}")
            
            analysis['value_score'] = value_score
            
            # Determine attack potential
            if value_score > 80:
                analysis['attack_potential'] = 'critical'
                analysis['priority_level'] = 5
            elif value_score > 60:
                analysis['attack_potential'] = 'high'
                analysis['priority_level'] = 4
            elif value_score > 40:
                analysis['attack_potential'] = 'medium'
                analysis['priority_level'] = 3
            elif value_score > 20:
                analysis['attack_potential'] = 'low'
                analysis['priority_level'] = 2
            
            # AI-powered vulnerability assessment
            vuln_score = self._ai_assess_vulnerabilities(host, features)
            analysis['vulnerability_score'] = vuln_score
            
            # Recommend attack vectors
            analysis['recommended_attacks'] = self._ai_recommend_attacks(host, features)
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"AI target analysis failed: {e}")
            return {
                'value_score': 0.0,
                'attack_potential': 'unknown',
                'recommended_attacks': [],
                'vulnerability_score': 0.0,
                'priority_level': 1
            }
    
    def _extract_host_features(self, host: Host) -> np.ndarray:
        """Extract features from host for AI analysis"""
        try:
            features = []
            
            # Basic host features
            features.extend([
                len(host.open_ports),
                len(host.services),
                host.importance_score / 100.0,
                int('gateway' in host.tags),
                int('dns-server' in host.tags),
                int('web-server' in host.tags),
                int('file-server' in host.tags),
                int('database' in host.tags),
                int('directory-service' in host.tags)
            ])
            
            # OS features
            os_features = [0.0, 0.0, 0.0, 0.0]  # windows, linux, other, unknown
            if host.fingerprint.os_family:
                os_family = host.fingerprint.os_family.lower()
                if 'windows' in os_family:
                    os_features[0] = 1.0
                elif 'linux' in os_family:
                    os_features[1] = 1.0
                else:
                    os_features[2] = 1.0
            else:
                os_features[3] = 1.0
            features.extend(os_features)
            
            # Service features
            critical_services = ['http', 'https', 'ssh', 'telnet', 'ftp', 'smtp', 'dns', 'mysql', 'mssql', 'rdp']
            service_features = []
            for service_name in critical_services:
                has_service = any(s.name == service_name for s in host.services.values())
                service_features.append(int(has_service))
            features.extend(service_features)
            
            # Version information features
            outdated_count = 0
            for service in host.services.values():
                if service.version and self._is_potentially_outdated(service):
                    outdated_count += 1
            features.append(outdated_count / max(len(host.services), 1))
            
            # Network position features
            subnet_count = sum(1 for hosts in self.subnets.values() if host.ip in hosts)
            features.extend([
                subnet_count,
                int(host.ip in self.gateways),
                len([h for h in self.hosts.values() if h.fingerprint.os_family == host.fingerprint.os_family])
            ])
            
            # Time-based features
            if host.last_seen and host.first_seen:
                uptime = host.last_seen - host.first_seen
                features.append(uptime / 86400.0)  # Days
            else:
                features.append(0.0)
            
            return np.array(features)
            
        except Exception as e:
            self.logger.error(f"Feature extraction failed: {e}")
            return np.zeros(28)  # Default feature vector
    
    def _calculate_traditional_value(self, host: Host) -> float:
        """Traditional target value calculation"""
        score = host.importance_score
        
        # Service-based scoring
        for service in host.services.values():
            if service.name in ['mysql', 'mssql', 'oracle']:
                score += 20
            elif service.name in ['ldap', 'kerberos']:
                score += 25
            elif service.name in ['http', 'https']:
                score += 15
            elif service.name in ['ssh', 'rdp']:
                score += 10
        
        # Tag-based scoring
        if 'gateway' in host.tags:
            score += 30
        if 'dns-server' in host.tags:
            score += 20
        if 'database' in host.tags:
            score += 35
        if 'directory-service' in host.tags:
            score += 40
        
        return min(100, score)
    
    def _ai_assess_vulnerabilities(self, host: Host, features: np.ndarray) -> float:
        """AI-powered vulnerability assessment"""
        try:
            base_vuln_score = 0.0
            
            # Check for known vulnerable services
            for service in host.services.values():
                if self._is_potentially_vulnerable(service):
                    base_vuln_score += 15
            
            # OS-based vulnerability assessment
            if host.fingerprint.os_match:
                os_match = host.fingerprint.os_match.lower()
                if 'windows xp' in os_match or 'windows 2003' in os_match:
                    base_vuln_score += 40
                elif 'windows 7' in os_match or 'windows 2008' in os_match:
                    base_vuln_score += 25
                elif 'windows 10' in os_match or 'windows 2016' in os_match:
                    base_vuln_score += 10
            
            # AI enhancement if model is trained
            if hasattr(self.ai_vulnerability_predictor, 'predict') and len(self.vulnerability_history) > 50:
                try:
                    ai_vuln_score = self.ai_vulnerability_predictor.predict([features])[0]
                    base_vuln_score = (base_vuln_score + ai_vuln_score * 100) / 2
                except Exception as e:
                    self.logger.error(f"AI vulnerability prediction failed: {e}")
            
            return min(100, base_vuln_score)
            
        except Exception as e:
            self.logger.error(f"Vulnerability assessment failed: {e}")
            return 0.0
    
    def _is_potentially_vulnerable(self, service: Service) -> bool:
        """Check if service is potentially vulnerable"""
        vulnerable_services = {
            'ftp': ['vsftpd 2.3.4', 'proftpd 1.3.3'],
            'ssh': ['openssh 2.', 'openssh 3.', 'openssh 4.'],
            'http': ['apache 2.2', 'iis 6.0', 'nginx 1.0'],
            'mysql': ['mysql 5.0', 'mysql 5.1'],
            'rdp': ['terminal services']
        }
        
        service_name = service.name.lower()
        if service_name in vulnerable_services and service.version:
            version = service.version.lower()
            return any(vuln_version in version for vuln_version in vulnerable_services[service_name])
        
        return False
    
    def _is_potentially_outdated(self, service: Service) -> bool:
        """Check if service version appears outdated"""
        if not service.version:
            return False
        
        version = service.version.lower()
        # Simple heuristic for outdated versions
        outdated_indicators = ['2.0', '2.1', '2.2', '3.0', '3.1', '4.0', '5.0', '5.1', '6.0']
        return any(indicator in version for indicator in outdated_indicators)
    
    def _ai_recommend_attacks(self, host: Host, features: np.ndarray) -> List[str]:
        """AI-powered attack recommendation"""
        try:
            recommendations = []
            
            # Service-based recommendations
            for service in host.services.values():
                service_name = service.name.lower()
                
                if service_name in ['http', 'https']:
                    recommendations.extend(['web_crawling', 'directory_bruteforce', 'sql_injection_test'])
                elif service_name == 'ssh':
                    recommendations.extend(['ssh_bruteforce', 'ssh_key_extraction'])
                elif service_name == 'ftp':
                    recommendations.extend(['ftp_bruteforce', 'anonymous_ftp_access'])
                elif service_name in ['mysql', 'mssql']:
                    recommendations.extend(['db_bruteforce', 'sql_injection'])
                elif service_name == 'rdp':
                    recommendations.extend(['rdp_bruteforce', 'rdp_exploit'])
                elif service_name in ['smb', 'netbios-ssn']:
                    recommendations.extend(['smb_enumeration', 'eternal_blue'])
            
            # OS-based recommendations
            if host.fingerprint.os_family:
                os_family = host.fingerprint.os_family.lower()
                if 'windows' in os_family:
                    recommendations.extend(['windows_exploit', 'privilege_escalation_windows'])
                elif 'linux' in os_family:
                    recommendations.extend(['linux_exploit', 'privilege_escalation_linux'])
            
            # Vulnerability-based recommendations
            vuln_score = self._ai_assess_vulnerabilities(host, features)
            if vuln_score > 70:
                recommendations.extend(['exploit_scan', 'metasploit_modules'])
            
            # Remove duplicates and return
            return list(set(recommendations))
            
        except Exception as e:
            self.logger.error(f"Attack recommendation failed: {e}")
            return []
    
    def ai_cluster_network_targets(self) -> Dict[str, List[str]]:
        """Use AI to cluster network targets by similarity"""
        try:
            if len(self.hosts) < 3:
                return {'default': list(self.hosts.keys())}
            
            # Extract features for all hosts
            host_features = []
            host_ips = []
            
            for host_ip, host in self.hosts.items():
                features = self._extract_host_features(host)
                host_features.append(features)
                host_ips.append(host_ip)
            
            if len(host_features) < 3:
                return {'default': host_ips}
            
            host_features = np.array(host_features)
            
            # Perform clustering
            try:
                clusters = self.ai_network_clusterer.fit_predict(host_features)
                
                # Group hosts by cluster
                clustered_targets = defaultdict(list)
                for host_ip, cluster_id in zip(host_ips, clusters):
                    cluster_name = f'cluster_{cluster_id}'
                    clustered_targets[cluster_name].append(host_ip)
                
                # Assign cluster types based on characteristics
                typed_clusters = {}
                for cluster_name, hosts in clustered_targets.items():
                    cluster_type = self._determine_cluster_type(hosts)
                    typed_clusters[cluster_type] = hosts
                
                return typed_clusters
                
            except Exception as e:
                self.logger.error(f"Network clustering failed: {e}")
                return {'default': host_ips}
            
        except Exception as e:
            self.logger.error(f"AI network clustering failed: {e}")
            return {'default': list(self.hosts.keys())}
    
    def _determine_cluster_type(self, host_ips: List[str]) -> str:
        """Determine cluster type based on host characteristics"""
        try:
            hosts = [self.hosts[ip] for ip in host_ips if ip in self.hosts]
            
            # Count characteristics
            server_count = sum(1 for h in hosts if any(tag in h.tags for tag in ['web-server', 'database', 'dns-server']))
            workstation_count = len(hosts) - server_count
            windows_count = sum(1 for h in hosts if h.fingerprint.os_family and 'windows' in h.fingerprint.os_family.lower())
            linux_count = sum(1 for h in hosts if h.fingerprint.os_family and 'linux' in h.fingerprint.os_family.lower())
            
            # Determine type
            if server_count > workstation_count:
                return 'servers'
            elif windows_count > linux_count:
                return 'windows_workstations'
            elif linux_count > 0:
                return 'linux_systems'
            else:
                return 'mixed_systems'
                
        except Exception as e:
            self.logger.error(f"Cluster type determination failed: {e}")
            return 'unknown'
    
    def ai_prioritize_scanning_order(self) -> List[str]:
        """Use AI to prioritize scanning order for maximum efficiency"""
        try:
            if not self.hosts:
                return []
            
            # Calculate priority scores for all hosts
            host_priorities = []
            
            for host_ip, host in self.hosts.items():
                analysis = self.ai_analyze_target_value(host)
                priority_score = (
                    analysis['value_score'] * 0.4 +
                    analysis['vulnerability_score'] * 0.3 +
                    analysis['priority_level'] * 20 * 0.3
                )
                host_priorities.append((host_ip, priority_score))
            
            # Sort by priority score (descending)
            host_priorities.sort(key=lambda x: x[1], reverse=True)
            
            return [host_ip for host_ip, _ in host_priorities]
            
        except Exception as e:
            self.logger.error(f"AI scan prioritization failed: {e}")
            return list(self.hosts.keys())
    
    def ai_train_models(self):
        """Train AI models with collected network data"""
        try:
            if len(self.target_history) < 30:
                return  # Need more data
            
            # Prepare training data for target classification
            X_target = []
            y_target = []
            
            for record in self.target_history:
                features = record.get('features', [])
                value_score = record.get('value_score', 0.0)
                
                if len(features) > 0:
                    X_target.append(features)
                    y_target.append(1 if value_score > 50 else 0)  # Binary classification
            
            if len(X_target) >= 20:
                try:
                    X_target = np.array(X_target)
                    y_target = np.array(y_target)
                    self.ai_target_classifier.fit(X_target, y_target)
                    self.logger.info("Target classifier model trained")
                except Exception as e:
                    self.logger.error(f"Target classifier training failed: {e}")
            
            # Prepare training data for vulnerability prediction
            if len(self.vulnerability_history) >= 20:
                X_vuln = []
                y_vuln = []
                
                for record in self.vulnerability_history:
                    features = record.get('features', [])
                    vuln_score = record.get('vulnerability_score', 0.0)
                    
                    if len(features) > 0:
                        X_vuln.append(features)
                        y_vuln.append(vuln_score / 100.0)  # Normalize to 0-1
                
                try:
                    X_vuln = np.array(X_vuln)
                    y_vuln = np.array(y_vuln)
                    self.ai_vulnerability_predictor.fit(X_vuln, y_vuln)
                    self.logger.info("Vulnerability predictor model trained")
                except Exception as e:
                    self.logger.error(f"Vulnerability predictor training failed: {e}")
            
        except Exception as e:
            self.logger.error(f"AI model training failed: {e}")