import os
import sys
import imp
import inspect
import json
import threading
import time
from importlib.machinery import SourceFileLoader
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
from typing import Dict, List, Optional, Any, Tuple
import psutil
import weakref
from datetime import datetime, timedelta
import cachetools
class PluginManager:
    def __init__(self, max_workers: Optional[int] = None):
        # Dynamic thread pool sizing
        cpu_count = psutil.cpu_count() or 1
        self.max_workers = max_workers or (cpu_count * 2)

        # Resource management with TTL
        self.plugins = weakref.WeakValueDictionary()
        self.plugin_threads = {}
        self.plugin_configs = {}
        self.plugin_dir = "plugins"
        self.config_file = "plugin_config.json"
        self.marketplace_url = "https://plugin-marketplace.example.com/api"
        self.installed_plugins = {}  # name -> version
        self.custom_commands = {}  # command_name -> handler

        # Resource pools with limits
        self.thread_pool = ThreadPoolExecutor(
            max_workers=self.max_workers,
            thread_name_prefix="PluginThread"
        )
        self.connection_pools = {
            'db': cachetools.TTLCache(maxsize=100, ttl=300),
            'network': cachetools.TTLCache(maxsize=100, ttl=300)
        }

        # Adaptive performance monitoring
        self.memory_threshold = self._calculate_memory_threshold()
        self.cpu_threshold = 80
        self.last_gc_time = time.time()
        self.gc_interval = 60  # 1 minute
        
        # Metadata caching with TTL
        self.plugin_metadata = cachetools.TTLCache(
            maxsize=1000,
            ttl=3600  # 1 hour
        )
        
        # Create plugin directory if not exists
        if not os.path.exists(self.plugin_dir):
            os.makedirs(self.plugin_dir)
            
        # Load config
        self.load_config()
        
        # Start resource monitor
        self._start_resource_monitor()
        
    def load_config(self):
        """Đọc config của các plugin"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    self.plugin_configs = json.load(f)
        except Exception as e:
            print(f"Error loading plugin config: {str(e)}")
            self.plugin_configs = {}
            
    def save_config(self):
        """Lưu config của các plugin"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.plugin_configs, f, indent=2)
        except Exception as e:
            print(f"Error saving plugin config: {str(e)}")
            
    def load_plugins(self, lazy: bool = True):
        """Load plugins with lazy loading option"""
        try:
            # Scan plugin directory
            for filename in os.listdir(self.plugin_dir):
                if filename.endswith('.py'):
                    plugin_name = filename[:-3]
                    
                    # Load metadata only for lazy loading
                    if lazy:
                        self._load_plugin_metadata(plugin_name)
                    else:
                        self.load_plugin(plugin_name)
                    
        except Exception as e:
            print(f"Error loading plugins: {str(e)}")
            
    def _load_plugin_metadata(self, plugin_name: str) -> Dict:
        """Load plugin metadata without initializing"""
        try:
            plugin_file = os.path.join(self.plugin_dir, f"{plugin_name}.py")
            
            # Parse file for metadata
            metadata = {
                'name': plugin_name,
                'dependencies': [],
                'resources': {}
            }
            
            with open(plugin_file, 'r') as f:
                content = f.read()
                
            # Extract metadata from comments/decorators
            if '"""' in content:
                doc_start = content.index('"""') + 3
                doc_end = content.index('"""', doc_start)
                metadata['description'] = content[doc_start:doc_end].strip()
                
            # Cache metadata
            self.plugin_metadata[plugin_name] = metadata
            return metadata
            
        except Exception as e:
            print(f"Error loading plugin metadata: {str(e)}")
            return {}
            
    def load_plugin(self, plugin_name):
        """Load một plugin cụ thể"""
        try:
            # Đường dẫn file plugin
            plugin_file = os.path.join(self.plugin_dir, f"{plugin_name}.py")
            
            if not os.path.exists(plugin_file):
                raise Exception(f"Plugin file not found: {plugin_file}")
                
            # Load module
            module = SourceFileLoader(plugin_name, plugin_file).load_module()
            
            # Tìm plugin class
            plugin_class = None
            for name, obj in inspect.getmembers(module):
                if inspect.isclass(obj) and hasattr(obj, 'plugin_name'):
                    plugin_class = obj
                    break
                    
            if not plugin_class:
                raise Exception(f"No plugin class found in {plugin_file}")
                
            # Khởi tạo plugin
            config = self.plugin_configs.get(plugin_name, {})
            plugin = plugin_class(config)
            
            # Lưu plugin
            self.plugins[plugin_name] = plugin
            print(f"Loaded plugin: {plugin_name}")
            
            # Khởi động plugin nếu được cấu hình
            if config.get('autostart', False):
                self.start_plugin(plugin_name)
                
        except Exception as e:
            print(f"Error loading plugin {plugin_name}: {str(e)}")
            
    def start_plugin(self, plugin_name):
        """Khởi động một plugin"""
        try:
            if plugin_name not in self.plugins:
                raise Exception(f"Plugin not found: {plugin_name}")
                
            if plugin_name in self.plugin_threads:
                raise Exception(f"Plugin already running: {plugin_name}")
                
            plugin = self.plugins[plugin_name]
            
            # Tạo thread cho plugin
            thread = threading.Thread(
                target=plugin.run,
                name=f"Plugin-{plugin_name}"
            )
            thread.daemon = True
            
            # Lưu và khởi động thread
            self.plugin_threads[plugin_name] = thread
            thread.start()
            
            print(f"Started plugin: {plugin_name}")
            
        except Exception as e:
            print(f"Error starting plugin {plugin_name}: {str(e)}")
            
    def stop_plugin(self, plugin_name):
        """Dừng một plugin"""
        try:
            if plugin_name not in self.plugins:
                raise Exception(f"Plugin not found: {plugin_name}")
                
            if plugin_name not in self.plugin_threads:
                raise Exception(f"Plugin not running: {plugin_name}")
                
            plugin = self.plugins[plugin_name]
            plugin.stop()
            
            # Đợi thread dừng
            thread = self.plugin_threads[plugin_name]
            thread.join(timeout=5)
            
            # Xóa thread
            del self.plugin_threads[plugin_name]
            print(f"Stopped plugin: {plugin_name}")
            
        except Exception as e:
            print(f"Error stopping plugin {plugin_name}: {str(e)}")
            
    def reload_plugin(self, plugin_name):
        """Reload một plugin"""
        try:
            # Dừng plugin nếu đang chạy
            if plugin_name in self.plugin_threads:
                self.stop_plugin(plugin_name)
                
            # Xóa plugin cũ
            if plugin_name in self.plugins:
                del self.plugins[plugin_name]
                
            # Load lại plugin
            self.load_plugin(plugin_name)
            
        except Exception as e:
            print(f"Error reloading plugin {plugin_name}: {str(e)}")
            
    def get_plugin(self, plugin_name):
        """Lấy instance của plugin"""
        return self.plugins.get(plugin_name)

    def list_plugins(self):
        """Liệt kê các plugin đã load"""
        plugins = []
        for name, plugin in self.plugins.items():
            plugins.append({
                'name': name,
                'running': name in self.plugin_threads,
                'config': self.plugin_configs.get(name, {}),
                'description': plugin.__doc__ or 'No description',
                'version': self.installed_plugins.get(name, '0.0.0'),
                'commands': self._get_plugin_commands(name)
            })
        return plugins

    # Marketplace Integration
    def list_marketplace_plugins(self) -> List[Dict]:
        """Get available plugins from marketplace"""
        try:
            import requests
            response = requests.get(f"{self.marketplace_url}/plugins")
            return response.json()
        except Exception as e:
            print(f"Error fetching marketplace plugins: {str(e)}")
            return []

    def install_from_marketplace(self, plugin_name: str, version: str = "latest") -> bool:
        """Install plugin from marketplace"""
        try:
            import requests
            
            # Get plugin info
            response = requests.get(f"{self.marketplace_url}/plugins/{plugin_name}")
            if not response.ok:
                raise Exception(f"Plugin {plugin_name} not found")
            
            plugin_info = response.json()
            
            # Download plugin
            download_url = plugin_info['versions'][version]['download_url']
            response = requests.get(download_url)
            
            # Save plugin file
            plugin_path = os.path.join(self.plugin_dir, f"{plugin_name}.py")
            with open(plugin_path, 'wb') as f:
                f.write(response.content)
                
            # Update installed plugins
            self.installed_plugins[plugin_name] = version
            
            # Load plugin
            self.load_plugin(plugin_name)
            return True
            
        except Exception as e:
            print(f"Error installing plugin {plugin_name}: {str(e)}")
            return False

    def update_plugin(self, plugin_name: str) -> bool:
        """Update plugin to latest version"""
        try:
            import requests
            
            # Get latest version
            response = requests.get(f"{self.marketplace_url}/plugins/{plugin_name}/latest")
            if not response.ok:
                raise Exception(f"Plugin {plugin_name} not found")
                
            latest = response.json()
            current = self.installed_plugins.get(plugin_name)
            
            if not current or latest['version'] > current:
                return self.install_from_marketplace(plugin_name, latest['version'])
            return True
            
        except Exception as e:
            print(f"Error updating plugin {plugin_name}: {str(e)}")
            return False

    # Custom Command Management
    def register_command(self, command: str, handler: callable, plugin_name: str) -> bool:
        """Register a custom command"""
        if command in self.custom_commands:
            return False
            
        self.custom_commands[command] = {
            'handler': handler,
            'plugin': plugin_name
        }
        return True

    def unregister_command(self, command: str, plugin_name: str) -> bool:
        """Unregister a custom command"""
        if command not in self.custom_commands:
            return False
            
        if self.custom_commands[command]['plugin'] != plugin_name:
            return False
            
        del self.custom_commands[command]
        return True

    def execute_command(self, command: str, *args, **kwargs) -> Any:
        """Execute a custom command"""
        if command not in self.custom_commands:
            raise Exception(f"Command {command} not found")
            
        handler = self.custom_commands[command]['handler']
        return handler(*args, **kwargs)

    def _get_plugin_commands(self, plugin_name: str) -> List[str]:
        """Get commands registered by a plugin"""
        return [
            cmd for cmd, info in self.custom_commands.items()
            if info['plugin'] == plugin_name
        ]

    def get_command_help(self, command: str) -> str:
        """Get help text for a command"""
        if command not in self.custom_commands:
            return "Command not found"
            
        handler = self.custom_commands[command]['handler']
        return handler.__doc__ or "No help available"
        
    def update_config(self, plugin_name, config):
        """Cập nhật config của plugin"""
        try:
            if plugin_name not in self.plugins:
                raise Exception(f"Plugin not found: {plugin_name}")
                
            # Cập nhật config
            self.plugin_configs[plugin_name] = config
            self.save_config()
            
            # Reload plugin để áp dụng config mới
            self.reload_plugin(plugin_name)
            
        except Exception as e:
            print(f"Error updating plugin config: {str(e)}")

class Plugin:
    """Base class for plugins with resource management"""
    
    plugin_name = None  # Override in subclass
    version = "0.0.1"  # Plugin version
    required_permissions = []  # Required permissions
    dependencies = []  # Required dependencies
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.running = False
        self.resources = {}  # Track resource usage
        self.last_usage = 0  # Last resource usage check
        self.usage_threshold = 0.8  # 80% threshold
        
        # Command registration
        self.commands = {}  # command_name -> method_name
        self.command_permissions = {}  # command_name -> required_permissions
        
        # Performance monitoring
        self.execution_times = deque(maxlen=100)  # Track command execution times
        self.error_count = 0
        self.last_error = None
        self.last_execution = None
        
        # Setup plugin
        self._register_commands()
        self._verify_dependencies()

    def _register_commands(self):
        """Auto-register commands from decorated methods"""
        for name, method in inspect.getmembers(self, inspect.ismethod):
            if hasattr(method, '_command'):
                command_name = method._command
                self.commands[command_name] = name
                if hasattr(method, '_permissions'):
                    self.command_permissions[command_name] = method._permissions

    def _verify_dependencies(self):
        """Verify required dependencies are available"""
        missing = []
        for dep in self.dependencies:
            try:
                __import__(dep)
            except ImportError:
                missing.append(dep)
        if missing:
            raise ImportError(f"Missing dependencies: {', '.join(missing)}")

    @staticmethod
    def command(name: str):
        """Decorator to register plugin commands"""
        def decorator(method):
            method._command = name
            return method
        return decorator

    @staticmethod
    def requires_permissions(*permissions: str):
        """Decorator to specify required permissions for commands"""
        def decorator(method):
            method._permissions = permissions
            return method
        return decorator

    def register_command(self, name: str, method: str, permissions: Optional[List[str]] = None):
        """Manually register a command"""
        if hasattr(self, method):
            self.commands[name] = method
            if permissions:
                self.command_permissions[name] = permissions
            return True
        return False

    def execute_command(self, command: str, *args, **kwargs) -> Any:
        """Execute a registered command"""
        if command not in self.commands:
            raise Exception(f"Command {command} not found")

        # Check permissions if specified
        if command in self.command_permissions:
            required = self.command_permissions[command]
            if not self._check_permissions(required):
                raise Exception(f"Missing permissions: {required}")

        # Get method
        method_name = self.commands[command]
        method = getattr(self, method_name)

        # Track execution
        start_time = time.time()
        try:
            result = method(*args, **kwargs)
            execution_time = time.time() - start_time
            self.execution_times.append(execution_time)
            self.last_execution = {
                'command': command,
                'time': execution_time,
                'success': True
            }
            return result
        except Exception as e:
            self.error_count += 1
            self.last_error = str(e)
            self.last_execution = {
                'command': command,
                'error': str(e),
                'success': False
            }
            raise

    def _check_permissions(self, required_permissions: List[str]) -> bool:
        """Check if plugin has required permissions"""
        # TODO: Implement actual permission checking
        return True

    def get_status(self) -> Dict:
        """Get plugin status information"""
        return {
            'name': self.plugin_name,
            'version': self.version,
            'running': self.running,
            'commands': list(self.commands.keys()),
            'execution_stats': {
                'total_executions': len(self.execution_times),
                'avg_execution_time': sum(self.execution_times)/len(self.execution_times) if self.execution_times else 0,
                'error_count': self.error_count,
                'last_error': self.last_error,
                'last_execution': self.last_execution
            },
            'resource_usage': {
                'memory': self._get_memory_usage(),
                'cpu': self._get_cpu_usage()
            }
        }

    def _get_memory_usage(self) -> float:
        """Get plugin's memory usage"""
        try:
            process = psutil.Process()
            return process.memory_percent()
        except:
            return 0.0

    def _get_cpu_usage(self) -> float:
        """Get plugin's CPU usage"""
        try:
            process = psutil.Process()
            return process.cpu_percent()
        except:
            return 0.0
        
    def run(self):
        """Main plugin execution with resource management"""
        self.running = True
        while self.running:
            try:
                # Check resource usage
                if self._check_resources():
                    self.execute()
                else:
                    # Sleep if resources exceeded
                    time.sleep(1)
            except Exception as e:
                print(f"Plugin {self.plugin_name} error: {str(e)}")
                break
                
    def stop(self):
        """Stop plugin and cleanup resources"""
        self.running = False
        self._cleanup_resources()
        
    def execute(self):
        """Override in subclass"""
        raise NotImplementedError
        
    def _check_resources(self) -> bool:
        """Check if resource usage is within limits"""
        try:
            current_time = time.time()
            
            # Only check every second
            if current_time - self.last_usage < 1:
                return True
                
            self.last_usage = current_time
            
            # Get process stats
            process = psutil.Process()
            
            # Check memory usage
            memory_percent = process.memory_percent()
            if memory_percent > self.usage_threshold * 100:
                return False
                
            # Check CPU usage
            cpu_percent = process.cpu_percent()
            if cpu_percent > self.usage_threshold * 100:
                return False
                
            return True
            
        except:
            return True  # Continue on error
            
    def _cleanup_resources(self):
        """Cleanup plugin resources"""
        try:
            # Close connections
            for conn in self.resources.get('connections', []):
                try:
                    conn.close()
                except:
                    pass
                    
            # Release memory
            self.resources.clear()
            
        except Exception as e:
            print(f"Error cleaning up resources: {str(e)}")
            
    def _start_resource_monitor(self):
        """Monitoring tài nguyên với adaptive thresholds"""
        def monitor():
            while True:
                try:
                    # Kiểm tra tài nguyên
                    memory = psutil.virtual_memory()
                    cpu = psutil.cpu_percent(interval=1)
                    
                    # Điều chỉnh ngưỡng dựa trên usage
                    self.memory_threshold = self._calculate_memory_threshold()
                    
                    # Cleanup aggressively nếu vượt ngưỡng
                    if memory.percent > self.memory_threshold:
                        self._cleanup_unused_resources(aggressive=True)
                    elif cpu > self.cpu_threshold:
                        self._cleanup_unused_resources(aggressive=False)
                    else:
                        # Normal cleanup interval
                        current_time = time.time()
                        if current_time - self.last_gc_time >= self.gc_interval:
                            self._cleanup_unused_resources(aggressive=False)
                            
                    time.sleep(10)  # Check more frequently
                    
                except Exception as e:
                    print(f"Resource monitor error: {str(e)}")
                    time.sleep(30)
                    
        thread = threading.Thread(
            target=monitor,
            name="ResourceMonitor",
            daemon=True
        )
        thread.start()
        
    def _calculate_memory_threshold(self) -> float:
        """Tính toán ngưỡng memory dựa trên system memory"""
        total_memory = psutil.virtual_memory().total
        if total_memory >= 16 * 1024 * 1024 * 1024:  # >= 16GB
            return 85.0
        elif total_memory >= 8 * 1024 * 1024 * 1024:  # >= 8GB
            return 80.0
        elif total_memory >= 4 * 1024 * 1024 * 1024:  # >= 4GB
            return 75.0
        else:
            return 70.0
        
    def _cleanup_unused_resources(self, aggressive: bool = False):
        """Dọn dẹp tài nguyên không sử dụng"""
        try:
            current_time = time.time()
            self.last_gc_time = current_time
            
            # Clear expired metadata
            expired = []
            for key, value in self.plugin_metadata.items():
                if value.get('last_used', 0) < current_time - 3600:
                    expired.append(key)
            for key in expired:
                del self.plugin_metadata[key]
                
            # Clear connection pools
            for pool in self.connection_pools.values():
                pool.expire()
                
            # Clear inactive plugins
            for name in list(self.plugins.keys()):
                plugin = self.plugins.get(name)
                if plugin:
                    if not plugin.running or \
                       (aggressive and not plugin.is_active()):
                        self._unload_plugin(name)
                        
            if aggressive:
                # Reduce thread pool
                self.thread_pool._max_workers = max(
                    2,
                    self.thread_pool._max_workers // 2
                )
                
                # Force garbage collection
                import gc
                gc.collect(generation=2)
            else:
                # Normal garbage collection
                gc.collect(generation=0)
                
            # Compact memory if aggressive
            if aggressive and hasattr(psutil.Process(), 'memory_full_info'):
                import ctypes
                try:
                    ctypes.CDLL('libc.so.6').malloc_trim(0)
                except:
                    pass
            
        except Exception as e:
            print(f"Error cleaning up resources: {str(e)}")