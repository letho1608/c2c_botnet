from __future__ import annotations
import nmap
import socket
import netifaces
from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass, field
import threading
import time
import concurrent.futures
from scapy.all import ARP, Ether, srp
import logging
import requests
import json
from functools import lru_cache
import paramiko
import ftplib
import smtplib
import yaml
import os

@dataclass
class Vulnerability:
    cve_id: str
    description: str
    severity: str
    cvss_score: float
    affected_versions: List[str]
    confidence: float = 0.0  # Độ tin cậy của phát hiện
    
@dataclass 
class Service:
    port: int
    name: str
    version: Optional[str] = None
    product: Optional[str] = None
    vulnerabilities: List[Vulnerability] = field(default_factory=list)
    banner: Optional[str] = None

@dataclass
class Host:
    ip: str
    mac: Optional[str] = None
    hostname: Optional[str] = None
    os: Optional[str] = None
    os_version: Optional[str] = None 
    os_confidence: Optional[int] = None
    open_ports: Set[int] = field(default_factory=set)
    services: Dict[int, Service] = field(default_factory=dict)
    vulnerabilities: List[Vulnerability] = field(default_factory=list)

class ServiceScanner:
    def __init__(self, timeout: int = 5):
        self.timeout = timeout
        self.logger = logging.getLogger(__name__)
        
    def scan(self, ip: str, port: int) -> Optional[Dict]:
        raise NotImplementedError

class SSHScanner(ServiceScanner):
    def scan(self, ip: str, port: int) -> Optional[Dict]:
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # Thử kết nối để lấy banner
            transport = paramiko.Transport((ip, port))
            transport.start_client(timeout=self.timeout)
            banner = transport.get_banner().decode()
            remote_version = transport.remote_version.decode()
            
            # Kiểm tra các thuật toán mã hóa được hỗ trợ
            kex_algs = transport.get_security_options().kex
            ciphers = transport.get_security_options().ciphers
            
            transport.close()
            
            return {
                'banner': banner,
                'version': remote_version,
                'kex_algorithms': kex_algs,
                'ciphers': ciphers
            }
            
        except Exception as e:
            self.logger.debug(f"SSH scan error on {ip}:{port}: {str(e)}")
            return None

class FTPScanner(ServiceScanner):
    def scan(self, ip: str, port: int) -> Optional[Dict]:
        try:
            ftp = ftplib.FTP()
            ftp.connect(ip, port, timeout=self.timeout)
            banner = ftp.getwelcome()
            
            # Thử login ẩn danh
            try:
                ftp.login()
                anon_login = True
                ftp.quit()
            except:
                anon_login = False
                
            return {
                'banner': banner,
                'anon_login': anon_login
            }
            
        except Exception as e:
            self.logger.debug(f"FTP scan error on {ip}:{port}: {str(e)}")
            return None

class SMTPScanner(ServiceScanner):
    def scan(self, ip: str, port: int) -> Optional[Dict]:
        try:
            smtp = smtplib.SMTP(timeout=self.timeout)
            smtp.connect(ip, port)
            banner = smtp.ehlo()[1].decode()
            
            # Lấy danh sách lệnh được hỗ trợ
            commands = smtp.esmtp_features
            
            smtp.quit()
            
            return {
                'banner': banner,
                'commands': commands
            }
            
        except Exception as e:
            self.logger.debug(f"SMTP scan error on {ip}:{port}: {str(e)}")
            return None

class NetworkScanner:
    def __init__(self, workers: int = 20) -> None:
        self.nmap = nmap.PortScanner()
        self.hosts: Dict[str, Host] = {}
        self.scanning = False
        self.logger = logging.getLogger(__name__)
        self.workers = workers
        
        # Khởi tạo service scanners
        self.service_scanners = {
            'ssh': SSHScanner(),
            'ftp': FTPScanner(),
            'smtp': SMTPScanner()
        }
        
        # Load signature database
        self.signatures = self._load_signatures()
        
        # Common ports to scan
        self.ports = {
            'basic': '21-23,25,53,80,110,139,443,445,3306,3389',
            'extended': '1-1024,1433,1521,3306,3389,5432,5900,6379,8080,8443,27017',
            'all': '1-65535',
            'ssh': '22',
            'ftp': '21',
            'smtp': '25,465,587',
            'common_services': '21-23,25,80,110,143,443,465,587,993,995,3306'
        }
        
        # Service-specific scan scripts 
        self.service_scripts = {
            'ssh': '--script ssh-auth-methods,ssh-hostkey,ssh-brute',
            'ftp': '--script ftp-anon,ftp-brute,ftp-vuln*',
            'smtp': '--script smtp-commands,smtp-enum-users,smtp-vuln*'
        }

    def _load_signatures(self) -> Dict:
        """Load vulnerability signatures từ file YAML"""
        try:
            signature_file = os.path.join(os.path.dirname(__file__), 'signatures.yaml')
            if os.path.exists(signature_file):
                with open(signature_file) as f:
                    return yaml.safe_load(f)
        except Exception as e:
            self.logger.error(f"Error loading signatures: {str(e)}")
        return {}

    def scan(self, subnet: Optional[str] = None, scan_type: str = 'basic') -> List[Dict]:
        if subnet is None:
            subnet = self._get_local_network()
            
        self.scanning = True
        self.logger.info(f"Starting {scan_type} scan of {subnet}")
        start_time = time.time()
        
        try:
            # ARP scan to find active hosts
            answered, _ = srp(
                Ether(dst="ff:ff:ff:ff:ff:ff") / ARP(pdst=subnet),
                timeout=2,
                verbose=False
            )
            
            # Quét hosts với thread pool
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.workers) as executor:
                future_to_ip = {
                    executor.submit(
                        self._scan_host, 
                        pkt[1].psrc, 
                        pkt[1].hwsrc,
                        scan_type
                    ): pkt[1].psrc 
                    for pkt in answered
                }
                
                for future in concurrent.futures.as_completed(future_to_ip):
                    ip = future_to_ip[future]
                    try:
                        host = future.result()
                        if host:
                            self.hosts[ip] = host
                            # Quét service và vulnerability trong thread pool
                            self._scan_services_and_vulns(host, executor)
                    except Exception as e:
                        self.logger.error(f"Error scanning {ip}: {str(e)}")
                        
            scan_time = time.time() - start_time
            self.logger.info(f"Scan completed in {scan_time:.2f} seconds")
            
            self.scanning = False
            return [self._host_to_dict(host) for host in self.hosts.values()]
            
        except Exception as e:
            self.logger.error(f"Error scanning network: {str(e)}")
            self.scanning = False
            return []

    def _scan_services_and_vulns(self, host: Host, executor: concurrent.futures.ThreadPoolExecutor) -> None:
        """Quét services và vulnerabilities song song"""
        futures = []
        
        # Submit service scans
        for port, service in host.services.items():
            if service.name in self.service_scanners:
                futures.append(
                    executor.submit(
                        self._scan_service,
                        host.ip,
                        port,
                        service
                    )
                )
                
        # Submit vulnerability checks
        futures.append(
            executor.submit(
                self._check_vulnerabilities,
                host
            )
        )
        
        # Wait for completion
        concurrent.futures.wait(futures)

    def _scan_service(self, ip: str, port: int, service: Service) -> None:
        """Quét chi tiết một service"""
        try:
            scanner = self.service_scanners[service.name]
            result = scanner.scan(ip, port)
            
            if result:
                service.banner = result.get('banner')
                # Cập nhật thêm thông tin service từ kết quả quét
                self._update_service_info(service, result)
                
        except Exception as e:
            self.logger.error(f"Error scanning service {service.name} on {ip}:{port}: {str(e)}")

    def _update_service_info(self, service: Service, scan_result: Dict) -> None:
        """Cập nhật thông tin service từ kết quả quét"""
        if service.name == 'ssh':
            if 'version' in scan_result:
                service.version = scan_result['version']
            # Validate SSH settings
            weak_kex = set(['diffie-hellman-group1-sha1'])
            weak_ciphers = set(['aes128-cbc', 'aes192-cbc', 'aes256-cbc'])
            
            if scan_result.get('kex_algorithms'):
                if weak_kex & set(scan_result['kex_algorithms']):
                    self._add_vulnerability(service, 'weak-ssh-kex')
                    
            if scan_result.get('ciphers'):
                if weak_ciphers & set(scan_result['ciphers']):
                    self._add_vulnerability(service, 'weak-ssh-ciphers')
                    
        elif service.name == 'ftp':
            if scan_result.get('anon_login'):
                self._add_vulnerability(service, 'ftp-anon')
                
        elif service.name == 'smtp':
            if scan_result.get('commands'):
                if 'VRFY' in scan_result['commands']:
                    self._add_vulnerability(service, 'smtp-vrfy')

    def _add_vulnerability(self, service: Service, signature_id: str) -> None:
        """Thêm vulnerability từ signature database"""
        if signature_id in self.signatures:
            sig = self.signatures[signature_id]
            vuln = Vulnerability(
                cve_id=sig['cve_id'],
                description=sig['description'],
                severity=sig['severity'],
                cvss_score=sig['cvss_score'],
                affected_versions=sig.get('affected_versions', []),
                confidence=sig.get('confidence', 0.8)
            )
            service.vulnerabilities.append(vuln)

    def _validate_vulnerability(self, vuln: Vulnerability, context: Dict) -> bool:
        """Validate một vulnerability dựa trên context"""
        # Kiểm tra version
        if vuln.affected_versions and context.get('version'):
            if not any(v in context['version'] for v in vuln.affected_versions):
                return False
                
        # Kiểm tra độ tin cậy
        if vuln.confidence < 0.7:  # Threshold cho false positives
            return False
            
        return True

    # Giữ nguyên các phương thức còn lại
    def _scan_host(self, ip: str, mac: str, scan_type: str = 'basic') -> Optional[Host]:
        """Quét chi tiết một host"""
        try:
            # Basic host info
            host = Host(ip=ip, mac=mac)
            scan_ports = self.ports[scan_type]
            
            # Try to get hostname
            try:
                host.hostname = socket.gethostbyaddr(ip)[0]
            except socket.herror:
                pass
                
            # Prepare scan arguments
            scan_args = ['-sS', '-sV', '-O', f'-p {scan_ports}', '--version-intensity 5']
            
            # Add service-specific scripts
            for service, script in self.service_scripts.items():
                if any(str(p) in scan_ports.split(',') for p in self.ports[service].split(',')):
                    scan_args.append(script)
            
            # Nmap scan with service detection
            self.nmap.scan(
                ip,
                arguments=' '.join(scan_args)
            )
            
            if ip in self.nmap.all_hosts():
                host_data = self.nmap[ip]
                
                # Enhanced OS detection
                if 'osmatch' in host_data and host_data['osmatch']:
                    os_data = host_data['osmatch'][0]
                    host.os = os_data['name']
                    host.os_confidence = int(os_data['accuracy'])
                    if 'osclass' in os_data:
                        host.os_version = os_data['osclass'][0].get('version')
                        
                # Enhanced service detection
                if 'tcp' in host_data:
                    for port, port_data in host_data['tcp'].items():
                        if port_data['state'] == 'open':
                            port = int(port)
                            host.open_ports.add(port)
                            
                            # Create service object
                            service = Service(
                                port=port,
                                name=port_data.get('name', 'unknown'),
                                version=port_data.get('version'),
                                product=port_data.get('product')
                            )
                            host.services[port] = service
                            
            return host
            
        except Exception as e:
            self.logger.error(f"Error scanning host {ip}: {str(e)}")
            return None

    @lru_cache(maxsize=100)
    def _get_cve_info(self, product: str, version: str) -> List[Dict[str, Any]]:
        """Lấy thông tin CVE cho một product/version"""
        try:
            url = f"https://services.nvd.nist.gov/rest/json/cves/2.0"
            params = {
                'keywordSearch': f"{product} {version}",
                'resultsPerPage': 20
            }
            response = requests.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                return data.get('vulnerabilities', [])
        except Exception as e:
            self.logger.error(f"Error fetching CVE info: {str(e)}")
        return []

    def _check_vulnerabilities(self, host: Host) -> None:
        """Kiểm tra vulnerabilities cho một host"""
        try:
            # Check OS vulnerabilities
            if host.os and host.os_version:
                cves = self._get_cve_info(host.os, host.os_version)
                for cve_data in cves:
                    vuln = self._create_vulnerability(cve_data)
                    if vuln and self._validate_vulnerability(vuln, {'version': host.os_version}):
                        host.vulnerabilities.append(vuln)
                        
            # Check service vulnerabilities
            for service in host.services.values():
                if service.product and service.version:
                    cves = self._get_cve_info(service.product, service.version)
                    for cve_data in cves:
                        vuln = self._create_vulnerability(cve_data)
                        if vuln and self._validate_vulnerability(vuln, {'version': service.version}):
                            service.vulnerabilities.append(vuln)
                            
        except Exception as e:
            self.logger.error(f"Error checking vulnerabilities: {str(e)}")

    def _create_vulnerability(self, cve_data: Dict) -> Optional[Vulnerability]:
        """Tạo vulnerability object từ CVE data"""
        try:
            cve = cve_data['cve']
            metrics = cve['metrics']['cvssMetricV31'][0]['cvssData']
            
            return Vulnerability(
                cve_id=cve['id'],
                description=cve['descriptions'][0]['value'],
                severity=metrics['baseSeverity'],
                cvss_score=float(metrics['baseScore']),
                affected_versions=[],  # TODO: Parse from configurations
                confidence=0.9 if float(metrics['baseScore']) >= 7.0 else 0.7
            )
        except Exception:
            return None

    def _host_to_dict(self, host: Host) -> Dict:
        """Convert Host object to dictionary"""
        services = {}
        for port, service in host.services.items():
            services[port] = {
                'name': service.name,
                'version': service.version,
                'product': service.product,
                'banner': service.banner,
                'vulnerabilities': [
                    {
                        'cve_id': v.cve_id,
                        'description': v.description,
                        'severity': v.severity,
                        'cvss_score': v.cvss_score,
                        'confidence': v.confidence
                    }
                    for v in service.vulnerabilities
                ]
            }
            
        return {
            'ip': host.ip,
            'mac': host.mac,
            'hostname': host.hostname,
            'os': host.os,
            'os_version': host.os_version,
            'os_confidence': host.os_confidence,
            'open_ports': sorted(list(host.open_ports)),
            'services': services,
            'vulnerabilities': [
                {
                    'cve_id': v.cve_id,
                    'description': v.description,
                    'severity': v.severity,
                    'cvss_score': v.cvss_score,
                    'confidence': v.confidence
                }
                for v in host.vulnerabilities
            ]
        }

    def _get_local_network(self) -> str:
        """Get the local network subnet"""
        try:
            # Get default gateway interface
            gateways = netifaces.gateways()
            if 'default' in gateways and netifaces.AF_INET in gateways['default']:
                interface = gateways['default'][netifaces.AF_INET][1]
                
                # Get interface addresses
                addrs = netifaces.ifaddresses(interface)
                if netifaces.AF_INET in addrs:
                    ip = addrs[netifaces.AF_INET][0]['addr']
                    netmask = addrs[netifaces.AF_INET][0]['netmask']
                    
                    # Calculate network address
                    ip_parts = [int(part) for part in ip.split('.')]
                    mask_parts = [int(part) for part in netmask.split('.')]
                    network = [ip_parts[i] & mask_parts[i] for i in range(4)]
                    
                    # Calculate CIDR notation
                    cidr = sum(bin(int(x)).count('1') for x in netmask.split('.'))
                    return f"{'.'.join(map(str, network))}/{cidr}"
                    
        except Exception as e:
            self.logger.error(f"Error getting local network: {str(e)}")
            
        # Fallback to common private network
        return "192.168.1.0/24"

    def stop(self) -> None:
        """Stop ongoing scan"""
        self.scanning = False

    def get_scan_progress(self) -> float:
        """Get scan progress percentage"""
        if not self.scanning:
            return 100.0
        # Calculate based on completed hosts vs total
        total = len(self.hosts)
        if total == 0:
            return 0.0
        completed = sum(1 for host in self.hosts.values() if host.services)
        return (completed / total) * 100