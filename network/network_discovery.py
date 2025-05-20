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