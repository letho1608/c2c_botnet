from __future__ import annotations
import os
import sys
import platform
import socket
import psutil
import ctypes
import time
import logging
import winreg
import subprocess
from typing import Dict, List, Optional, Set, Any
from ctypes import windll, Structure, c_long, byref, c_ulong
from pathlib import Path

class AntiAnalysis:
    def __init__(self) -> None:
        """Initialize anti-analysis module"""
        self.logger = logging.getLogger(__name__)
        
        # Lists of suspicious indicators
        self.suspicious_processes: Set[str] = {
            "wireshark.exe", "procexp.exe", "procmon.exe", "tcpview.exe",
            "processhacker.exe", "regmon.exe", "filemon.exe", "ida.exe", 
            "ida64.exe", "ollydbg.exe", "x32dbg.exe", "x64dbg.exe",
            "windbg.exe", "dnspy.exe", "pestudio.exe", "process explorer.exe",
            "process monitor.exe", "autoruns.exe", "autorunsc.exe",
            "dumpcap.exe", "fiddler.exe"
        }
        
        self.suspicious_files: Set[str] = {
            r"C:\windows\system32\drivers\vmmouse.sys",
            r"C:\windows\system32\drivers\vmhgfs.sys",
            r"C:\windows\system32\drivers\vboxsf.sys",
            r"C:\windows\system32\drivers\vboxguest.sys"
        }
        
        self.suspicious_reg_keys: Set[str] = {
            r"HARDWARE\DEVICEMAP\Scsi\Scsi Port 0\Scsi Bus 0\Target Id 0\Logical Unit Id 0",
            r"HARDWARE\Description\System",
            r"SOFTWARE\Oracle\VirtualBox Guest Additions",
            r"SOFTWARE\VMware, Inc.\VMware Tools",
            r"SOFTWARE\Microsoft\Virtual Machine\Guest\Parameters"
        }
        
    def check_all(self) -> bool:
        """Run all detection checks

        Returns:
            bool: True if analysis environment detected
        """
        checks = [
            self.check_processes,
            self.check_vm,
            self.check_debugger,
            self.check_sandbox,
            self.check_analysis_tools
        ]
        
        for check in checks:
            try:
                if check():
                    self.logger.warning(f"Analysis environment detected by {check.__name__}")
                    return True
            except Exception as e:
                self.logger.error(f"Error in {check.__name__}: {str(e)}")
                
        return False
        
    def check_processes(self) -> bool:
        """Check for analysis-related processes

        Returns:
            bool: True if suspicious processes found
        """
        try:
            for proc in psutil.process_iter(['name', 'cmdline']):
                try:
                    # Check process name
                    if proc.info['name'].lower() in self.suspicious_processes:
                        self.logger.warning(f"Suspicious process found: {proc.info['name']}")
                        return True
                        
                    # Check command line
                    if proc.info['cmdline']:
                        cmdline = ' '.join(proc.info['cmdline']).lower()
                        if any(p in cmdline for p in self.suspicious_processes):
                            self.logger.warning(f"Suspicious cmdline: {cmdline}")
                            return True
                            
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
                    
            return False
            
        except Exception as e:
            self.logger.error(f"Process check error: {str(e)}")
            return False
            
    def check_vm(self) -> bool:
        """Check for virtual machine indicators

        Returns:
            bool: True if VM detected
        """
        try:
            # Check system firmware tables
            try:
                firmware = subprocess.check_output(
                    'wmic bios get serialnumber',
                    shell=True,
                    text=True
                ).lower()
                
                vm_strings = ['vmware', 'virtualbox', 'xen', 'qemu']
                if any(x in firmware for x in vm_strings):
                    return True
            except:
                pass
                
            # Check MAC address
            try:
                mac = ':'.join([
                    '{:02x}'.format((uuid.getnode() >> elements) & 0xff)
                    for elements in range(0,2*6,2)
                ][::-1])
                
                vm_macs = [
                    '08:00:27',  # VirtualBox
                    '00:05:69',  # VMware
                    '00:0C:29',  # VMware
                    '00:1C:14',  # VMware
                    '00:50:56',  # VMware
                ]
                
                if any(mac.startswith(vm_mac) for vm_mac in vm_macs):
                    return True
            except:
                pass
                
            # Check registry
            try:
                for key_path in self.suspicious_reg_keys:
                    try:
                        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path)
                        winreg.CloseKey(key)
                        return True
                    except:
                        continue
            except:
                pass
                
            # Check files
            for path in self.suspicious_files:
                if Path(path).exists():
                    return True
                    
            return False
            
        except Exception as e:
            self.logger.error(f"VM check error: {str(e)}")
            return False
            
    def check_debugger(self) -> bool:
        """Check for debugger presence

        Returns:
            bool: True if debugger detected
        """
        try:
            # IsDebuggerPresent
            if windll.kernel32.IsDebuggerPresent():
                return True
                
            # CheckRemoteDebuggerPresent
            debugger_present = c_long()
            if windll.kernel32.CheckRemoteDebuggerPresent(
                windll.kernel32.GetCurrentProcess(),
                byref(debugger_present)
            ):
                if debugger_present.value:
                    return True
                    
            # NtGlobalFlag check
            try:
                class PEB(Structure):
                    _fields_ = [
                        ("InheritedAddressSpace", c_ulong),
                        ("ReadImageFileExecOptions", c_ulong),
                        ("BeingDebugged", c_ulong),
                        ("BitField", c_ulong),
                        ("Mutant", c_ulong),
                        ("ImageBaseAddress", c_ulong),
                        ("Ldr", c_ulong),
                        ("ProcessParameters", c_ulong),
                        ("SubSystemData", c_ulong),
                        ("ProcessHeap", c_ulong),
                        ("FastPebLock", c_ulong),
                        ("AtlThunkSListPtr", c_ulong),
                        ("IFEOKey", c_ulong),
                        ("CrossProcessFlags", c_ulong),
                        ("UserSharedInfoPtr", c_ulong),
                        ("SystemReserved", c_ulong),
                        ("AtlThunkSListPtr32", c_ulong),
                        ("ApiSetMap", c_ulong),
                        ("TlsExpansionCounter", c_ulong),
                        ("TlsBitmap", c_ulong),
                        ("TlsBitmapBits", c_ulong * 2),
                        ("ReadOnlySharedMemoryBase", c_ulong),
                        ("SharedData", c_ulong),
                        ("ReadOnlyStaticServerData", c_ulong),
                        ("AnsiCodePageData", c_ulong),
                        ("OemCodePageData", c_ulong),
                        ("UnicodeCaseTableData", c_ulong),
                        ("NumberOfProcessors", c_ulong),
                        ("NtGlobalFlag", c_ulong),
                    ]
                    
                process_env = c_long()
                windll.ntdll.NtQueryInformationProcess(
                    windll.kernel32.GetCurrentProcess(),
                    0,
                    byref(process_env),
                    ctypes.sizeof(process_env),
                    None
                )
                
                peb = PEB.from_address(process_env.value)
                if peb.NtGlobalFlag & 0x70:
                    return True
                    
            except:
                pass
                
            # Hardware breakpoints
            try:
                class CONTEXT(Structure):
                    _fields_ = [
                        ("ContextFlags", c_ulong),
                        ("Dr0", c_ulong),
                        ("Dr1", c_ulong),
                        ("Dr2", c_ulong),
                        ("Dr3", c_ulong),
                        ("Dr6", c_ulong),
                        ("Dr7", c_ulong),
                    ]
                    
                context = CONTEXT()
                context.ContextFlags = 0x00100010  # CONTEXT_DEBUG_REGISTERS
                
                thread = windll.kernel32.GetCurrentThread()
                if windll.kernel32.GetThreadContext(thread, byref(context)):
                    if (context.Dr0 or context.Dr1 or 
                        context.Dr2 or context.Dr3):
                        return True
                        
            except:
                pass
                
            return False
            
        except Exception as e:
            self.logger.error(f"Debugger check error: {str(e)}")
            return False
            
    def check_sandbox(self) -> bool:
        """Check for sandbox environment

        Returns:
            bool: True if sandbox detected
        """
        try:
            # Check user/computer name
            sandbox_names = ['sandbox', 'malware', 'virus', 'sample']
            username = os.getlogin().lower()
            hostname = socket.gethostname().lower()
            
            if any(name in username for name in sandbox_names):
                return True
            if any(name in hostname for name in sandbox_names):
                return True
                
            # Check disk size
            try:
                total, used, free = psutil.disk_usage('/')
                if total < (60 * 1024 * 1024 * 1024):  # Less than 60GB
                    return True
            except:
                pass
                
            # Check memory size
            try:
                if psutil.virtual_memory().total < (2 * 1024 * 1024 * 1024):  # Less than 2GB
                    return True
            except:
                pass
                
            # Check CPU cores
            try:
                if psutil.cpu_count() < 2:
                    return True
            except:
                pass
                
            # Check uptime
            try:
                boot_time = psutil.boot_time()
                if time.time() - boot_time < 300:  # Less than 5 minutes
                    return True
            except:
                pass
                
            # Check process count
            try:
                if len(psutil.pids()) < 50:
                    return True
            except:
                pass
                
            return False
            
        except Exception as e:
            self.logger.error(f"Sandbox check error: {str(e)}")
            return False
            
    def check_analysis_tools(self) -> bool:
        """Check for analysis tools

        Returns:
            bool: True if analysis tools detected
        """
        try:
            # Check Wireshark
            try:
                capture_devices = subprocess.check_output(
                    'ipconfig /all',
                    shell=True,
                    text=True
                ).lower()
                if 'npcap' in capture_devices or 'winpcap' in capture_devices:
                    return True
            except:
                pass
                
            # Check debug ports
            debug_ports = [1337, 2552, 31337, 9100]
            
            for port in debug_ports:
                try:
                    sock = socket.socket()
                    sock.settimeout(1)
                    result = sock.connect_ex(('127.0.0.1', port))
                    sock.close()
                    if result == 0:
                        return True
                except:
                    continue
                    
            # Check registry monitoring
            try:
                test_key = "Software\\Test"
                key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, test_key)
                winreg.SetValueEx(key, "test", 0, winreg.REG_SZ, "test")
                winreg.DeleteValue(key, "test")
                winreg.DeleteKey(key, "")
                
                time.sleep(0.1)
                for proc in psutil.process_iter(['name']):
                    if proc.info['name'].lower() in ['regmon.exe', 'procmon.exe']:
                        return True
            except:
                pass
                
            # Check file monitoring
            try:
                test_file = "test.tmp"
                Path(test_file).write_text("test")
                Path(test_file).unlink()
                
                time.sleep(0.1)
                for proc in psutil.process_iter(['name']):
                    if proc.info['name'].lower() in ['filemon.exe', 'procmon.exe']:
                        return True
            except:
                pass
                
            return False
            
        except Exception as e:
            self.logger.error(f"Analysis tools check error: {str(e)}")
            return False