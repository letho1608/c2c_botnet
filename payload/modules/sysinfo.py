from __future__ import annotations
import os
import sys
import platform
import socket
import psutil
import json
import uuid
import requests
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
import logging
import winreg

class SystemInfo:
    def __init__(self) -> None:
        self.info: Dict[str, Any] = {}
        self.logger = logging.getLogger(__name__)
        
    def collect_all(self) -> Dict[str, Any]:
        """Thu thập tất cả thông tin hệ thống

        Returns:
            Dict[str, Any]: Dictionary chứa thông tin hệ thống
        """
        self.get_system_info()
        self.get_network_info()
        self.get_hardware_info()
        self.get_running_processes()
        self.get_installed_software()
        self.get_geolocation()
        return self.info
        
    def get_system_info(self) -> Dict[str, str]:
        """Thu thập thông tin hệ thống cơ bản

        Returns:
            Dict[str, str]: Basic system information
        """
        try:
            self.info['system'] = {
                'os': platform.system(),
                'release': platform.release(),
                'version': platform.version(),
                'machine': platform.machine(),
                'processor': platform.processor(),
                'hostname': socket.gethostname(),
                'username': os.getlogin(),
                'boot_time': datetime.fromtimestamp(psutil.boot_time()).isoformat()
            }
            return self.info['system']
            
        except Exception as e:
            self.logger.error(f"Error getting system info: {str(e)}")
            return {}
            
    def get_network_info(self) -> Dict[str, List[Dict[str, Any]]]:
        """Thu thập thông tin mạng

        Returns:
            Dict[str, List[Dict[str, Any]]]: Network information
        """
        try:
            interfaces = []
            for iface, addrs in psutil.net_if_addrs().items():
                iface_info: Dict[str, Any] = {'name': iface}
                for addr in addrs:
                    if addr.family == socket.AF_INET:
                        iface_info['ipv4'] = addr.address
                    elif addr.family == socket.AF_INET6:
                        iface_info['ipv6'] = addr.address
                    elif addr.family == psutil.AF_LINK:
                        iface_info['mac'] = addr.address
                interfaces.append(iface_info)
                
            connections = [
                {
                    'local_addr': f"{conn.laddr.ip}:{conn.laddr.port}",
                    'remote_addr': f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else None,
                    'status': conn.status,
                    'pid': conn.pid
                }
                for conn in psutil.net_connections()
            ]
            
            self.info['network'] = {
                'interfaces': interfaces,
                'connections': connections
            }
            return self.info['network']
            
        except Exception as e:
            self.logger.error(f"Error getting network info: {str(e)}")
            return {'interfaces': [], 'connections': []}
            
    def get_hardware_info(self) -> Dict[str, Any]:
        """Thu thập thông tin phần cứng

        Returns:
            Dict[str, Any]: Hardware information
        """
        try:
            self.info['hardware'] = {
                'cpu': {
                    'cores': psutil.cpu_count(),
                    'freq': psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None,
                    'usage': psutil.cpu_percent(interval=1)
                },
                'memory': {
                    'total': psutil.virtual_memory().total,
                    'available': psutil.virtual_memory().available,
                    'used': psutil.virtual_memory().used,
                    'percent': psutil.virtual_memory().percent
                },
                'disk': [
                    {
                        'device': part.device,
                        'mountpoint': part.mountpoint,
                        'fstype': part.fstype,
                        'total': psutil.disk_usage(part.mountpoint).total,
                        'used': psutil.disk_usage(part.mountpoint).used,
                        'free': psutil.disk_usage(part.mountpoint).free
                    }
                    for part in psutil.disk_partitions()
                ]
            }
            return self.info['hardware']
            
        except Exception as e:
            self.logger.error(f"Error getting hardware info: {str(e)}")
            return {}
            
    def get_running_processes(self) -> List[Dict[str, Any]]:
        """Thu thập thông tin về các tiến trình đang chạy

        Returns:
            List[Dict[str, Any]]: List of running processes
        """
        processes = []
        try:
            for proc in psutil.process_iter(['pid', 'name', 'username', 'status']):
                try:
                    pinfo = proc.as_dict()
                    processes.append({
                        'pid': pinfo['pid'],
                        'name': pinfo['name'],
                        'user': pinfo['username'],
                        'status': pinfo['status'],
                        'cpu_percent': proc.cpu_percent(),
                        'memory_percent': proc.memory_percent()
                    })
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass
                    
            self.info['processes'] = processes
            return processes
            
        except Exception as e:
            self.logger.error(f"Error getting process info: {str(e)}")
            return []
            
    def get_installed_software(self) -> List[Dict[str, str]]:
        """Thu thập thông tin về phần mềm đã cài đặt

        Returns:
            List[Dict[str, str]]: List of installed software
        """
        software_list = []
        
        if platform.system() == 'Windows':
            try:
                for hive in [winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER]:
                    for key_path in [
                        r"Software\Microsoft\Windows\CurrentVersion\Uninstall",
                        r"Software\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall"
                    ]:
                        try:
                            key = winreg.OpenKey(hive, key_path)
                            for i in range(winreg.QueryInfoKey(key)[0]):
                                try:
                                    subkey_name = winreg.EnumKey(key, i)
                                    subkey = winreg.OpenKey(key, subkey_name)
                                    try:
                                        software_list.append({
                                            'name': winreg.QueryValueEx(subkey, "DisplayName")[0],
                                            'version': winreg.QueryValueEx(subkey, "DisplayVersion")[0],
                                            'publisher': winreg.QueryValueEx(subkey, "Publisher")[0]
                                        })
                                    except:
                                        pass
                                    finally:
                                        winreg.CloseKey(subkey)
                                except:
                                    continue
                            winreg.CloseKey(key)
                        except:
                            continue
                            
            except Exception as e:
                self.logger.error(f"Error getting software info: {str(e)}")
                
        self.info['software'] = software_list
        return software_list
        
    def get_geolocation(self) -> Optional[Dict[str, Any]]:
        """Lấy vị trí địa lý dựa trên IP

        Returns:
            Optional[Dict[str, Any]]: Geolocation data if available
        """
        try:
            response = requests.get('https://ipapi.co/json/', timeout=5)
            if response.status_code == 200:
                self.info['geolocation'] = response.json()
                return self.info['geolocation']
        except Exception as e:
            self.logger.error(f"Error getting geolocation: {str(e)}")
            
        self.info['geolocation'] = None
        return None
        
    def to_json(self) -> str:
        """Convert info to JSON string

        Returns:
            str: JSON formatted system information
        """
        return json.dumps(self.info, indent=2)
        
    def save_to_file(self, filename: str) -> bool:
        """Save system information to file

        Args:
            filename (str): Output filename

        Returns:
            bool: True if saved successfully
        """
        try:
            with open(filename, 'w') as f:
                json.dump(self.info, f, indent=2)
            return True
        except Exception as e:
            self.logger.error(f"Error saving to file: {str(e)}")
            return False