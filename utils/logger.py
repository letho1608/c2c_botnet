import os
import sys
import json
import gzip
import queue
import logging
import threading
from functools import lru_cache
from datetime import datetime
from logging.handlers import RotatingFileHandler
from concurrent.futures import ThreadPoolExecutor

class AdvancedLogger:
    def __init__(self, name, log_dir="logs", max_queue_size=10000):
        self.name = name
        self.log_dir = log_dir
        
        # Tạo thư mục logs nếu chưa có
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
            
        # Queue để xử lý log bất đồng bộ
        self.log_queue = queue.Queue(maxsize=max_queue_size)
        
        # Thread pool cho xử lý bất đồng bộ
        self.thread_pool = ThreadPoolExecutor(max_workers=2)
        
        # Cache cho thống kê
        self._stats_cache = {}
        self._last_stats_update = 0
        
        # Tạo các logger riêng cho từng loại
        self.loggers = {
            'system': self._setup_logger('system'),
            'command': self._setup_logger('command'),
            'exploit': self._setup_logger('exploit'),
            'network': self._setup_logger('network'),
            'bot': self._setup_logger('bot')
        }
        
        # Thread-safe logging
        self.log_lock = threading.Lock()
        
        # Bắt đầu worker thread để xử lý log queue
        self.running = True
        self.worker_thread = threading.Thread(target=self._process_log_queue)
        self.worker_thread.daemon = True
        self.worker_thread.start()
        
    def _setup_logger(self, category):
        """Khởi tạo logger cho một category"""
        logger = logging.getLogger(f"{self.name}.{category}")
        logger.setLevel(logging.DEBUG)
        
        # File handler với rotation
        log_file = os.path.join(self.log_dir, f"{category}.log")
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        
        # Format
        formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        return logger
        
    def _process_log_queue(self):
        """Worker thread để xử lý log queue"""
        while self.running:
            try:
                log_entry = self.log_queue.get(timeout=1)
                category = log_entry.pop('category')
                level = log_entry.pop('level')
                message = log_entry.pop('message')
                
                logger = self.loggers[category]
                log_data = {
                    'timestamp': datetime.now().isoformat(),
                    'category': category,
                    'level': level,
                    'message': message
                }
                log_data.update(log_entry)
                
                # Thread-safe logging
                with self.log_lock:
                    if level == 'DEBUG':
                        logger.debug(json.dumps(log_data))
                    elif level == 'INFO':
                        logger.info(json.dumps(log_data))
                    elif level == 'WARNING':
                        logger.warning(json.dumps(log_data))
                    elif level == 'ERROR':
                        logger.error(json.dumps(log_data))
                    elif level == 'CRITICAL':
                        logger.critical(json.dumps(log_data))
                        
            except queue.Empty:
                continue
            except Exception as e:
                sys.stderr.write(f"Error processing log: {str(e)}\n")
                
    def log(self, category, level, message, **kwargs):
        """Log một message với metadata"""
        if category not in self.loggers:
            return
            
        # Đưa vào queue để xử lý bất đồng bộ
        try:
            log_entry = {
                'category': category,
                'level': level,
                'message': message
            }
            log_entry.update(kwargs)
            self.log_queue.put_nowait(log_entry)
        except queue.Full:
            sys.stderr.write("Log queue is full, dropping message\n")
                
    def system_log(self, level, message, **kwargs):
        """Log system events"""
        self.log('system', level, message, **kwargs)
        
    def command_log(self, level, message, **kwargs):
        """Log command execution"""
        self.log('command', level, message, **kwargs)
        
    def exploit_log(self, level, message, **kwargs):
        """Log exploit execution"""
        self.log('exploit', level, message, **kwargs)
        
    def network_log(self, level, message, **kwargs):
        """Log network events"""
        self.log('network', level, message, **kwargs)
        
    def bot_log(self, level, message, **kwargs):
        """Log bot events"""
        self.log('bot', level, message, **kwargs)
        
    @lru_cache(maxsize=128)
    def get_logs(self, category=None, start_time=None, end_time=None,
                level=None, limit=100):
        """Query logs với các filter"""
        logs = []
        
        try:
            # Xác định các file cần đọc
            if category:
                log_files = [f"{category}.log"]
            else:
                log_files = [f"{cat}.log" for cat in self.loggers.keys()]
                
            # Đọc và parse logs
            for filename in log_files:
                path = os.path.join(self.log_dir, filename)
                if not os.path.exists(path):
                    # Kiểm tra file nén
                    gz_path = path + '.gz'
                    if not os.path.exists(gz_path):
                        continue
                    # Đọc từ file nén
                    with gzip.open(gz_path, 'rt') as f:
                        self._process_log_lines(f, logs, start_time, end_time, level)
                else:
                    # Đọc file thường
                    with open(path, 'r') as f:
                        self._process_log_lines(f, logs, start_time, end_time, level)
                            
            # Sort theo timestamp và giới hạn số lượng
            logs.sort(key=lambda x: x['timestamp'], reverse=True)
            return logs[:limit]
            
        except Exception as e:
            print(f"Error querying logs: {str(e)}")
            return []
            
    def export_logs(self, output_file, **filters):
        """Export logs ra file"""
        try:
            logs = self.get_logs(**filters)
            
            with open(output_file, 'w') as f:
                json.dump(logs, f, indent=2)
                
            return True
            
        except Exception as e:
            print(f"Error exporting logs: {str(e)}")
            return False
            
    def clear_logs(self, category=None):
        """Xóa logs"""
        try:
            if category:
                # Xóa log của một category
                path = os.path.join(self.log_dir, f"{category}.log")
                if os.path.exists(path):
                    os.remove(path)
            else:
                # Xóa tất cả logs
                for filename in os.listdir(self.log_dir):
                    if filename.endswith('.log'):
                        os.remove(os.path.join(self.log_dir, filename))
                        
            return True
            
        except Exception as e:
            print(f"Error clearing logs: {str(e)}")
            return False
            
    def _process_log_lines(self, file, logs, start_time, end_time, level):
        """Helper để xử lý các dòng log"""
        for line in file:
            try:
                entry = json.loads(line.strip())
                
                # Áp dụng các filter
                if start_time and entry['timestamp'] < start_time:
                    continue
                if end_time and entry['timestamp'] > end_time:
                    continue
                if level and entry['level'] != level:
                    continue
                    
                logs.append(entry)
                
            except json.JSONDecodeError:
                continue
                
    def get_stats(self):
        """Thống kê về logs với caching"""
        current_time = time.time()
        # Return cached stats if available and fresh
        if self._stats_cache and current_time - self._last_stats_update < 300:
            return self._stats_cache
            
        stats = {
            'total_entries': 0,
            'categories': {},
            'levels': {
                'DEBUG': 0, 'INFO': 0, 'WARNING': 0,
                'ERROR': 0, 'CRITICAL': 0
            }
        }
        
        try:
            futures = []
            
            # Process each log file in parallel
            for category in self.loggers.keys():
                future = self.thread_pool.submit(
                    self._process_log_stats,
                    category,
                    stats
                )
                futures.append(future)
                
            # Wait for all processing to complete
            for future in futures:
                future.result()
                
            # Update cache
            self._stats_cache = stats
            self._last_stats_update = current_time
            
            return stats
            
        except Exception as e:
            logging.error(f"Error getting log stats: {str(e)}")
            return stats
            
    def _process_log_stats(self, category, stats):
        """Process stats for a single log file"""
        path = os.path.join(self.log_dir, f"{category}.log")
        if not os.path.exists(path):
            return
            
        cat_count = 0
        try:
            with open(path, 'r') as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                        cat_count += 1
                        stats['levels'][entry['level']] += 1
                    except json.JSONDecodeError:
                        continue
                        
            stats['categories'][category] = cat_count
            stats['total_entries'] += cat_count
            
        except Exception as e:
            logging.error(f"Error processing stats for {category}: {str(e)}")
            
    def cleanup(self):
        """Cleanup resources"""
        self.running = False
        self.worker_thread.join()
        self.thread_pool.shutdown()