from __future__ import annotations
import os
import sys
import time
import uuid
import ctypes
import logging
import platform 
import win32api
import wmi
import psutil
import winreg
from typing import List, Set, Dict, Optional
from pathlib import Path

class AntiVM:
    def __init__(self) -> None:
        """Initialize advanced anti-analysis system"""
        self.logger = logging.getLogger('security')
        self.wmi = wmi.WMI()
        self._init_timing_baseline()
        self._setup_hardware_fingerprint()
        
        # Extended VM signatures
        self.vm_services = {
            'vboxservice',
            'vmtoolsd',
            'vmwaretray',
            'vmwareuser',
            'vgauthservice',
            'vmacthlp',
            'vboxtray',
            'sandboxie',
            'wireshark',
            'fiddler',
            'processhacker',
            'ollydbg',
            'x64dbg',
            'windbg',
            'ida64',
            'radare2'
        }
        
        self.vm_processes.update({
            'vmsrvc.exe',
            'authd.exe',
            'vm3dservice.exe',
            'vmtoolsd.exe',
            'dumpcap.exe',
            'tcpdump.exe',
            'windump.exe',
            'apimonitor-x64.exe',
            'apimonitor-x86.exe',
            'regmon.exe',
            'filemon.exe',
            'immunitydebugger.exe',
            'reshacker.exe',
            'pestudio.exe',
            'dnspy.exe',
            'scylla_x64.exe',
            'protection_id.exe'
        })

        self.debugger_processes = {
            'ollydbg.exe',
            'x64dbg.exe', 
            'windbg.exe',
            'ida64.exe',
            'radare2.exe',
            'immunity debugger.exe',
            'cheatengine-x86_64.exe'
        }

        self.monitoring_tools = {
            'procmon.exe',
            'procmon64.exe',
            'processmonitor.exe', 
            'wireshark.exe',
            'fiddler.exe',
            'charles.exe',
            'tcpview.exe',
            'autoruns.exe',
            'autorunsc.exe',
            'filemon.exe',
            'regmon.exe'
        }

    def check_debugger(self) -> bool:
        """Enhanced debugger detection with anti-attach"""
        try:
            kernel32 = ctypes.windll.kernel32
            ntdll = ctypes.windll.ntdll
            
            # Basic debugger checks
            if kernel32.IsDebuggerPresent():
                return True
                
            # Anti-attach mechanisms
            self._prevent_debugger_attach()
            
            # Thread start address verification
            if self._check_thread_start():
                return True
                
            # Advanced timing checks
            if self._detect_timing_anomalies():
                return True
                
            # Exception handler verification
            if self._verify_exception_handlers():
                return True
                
            # Hardware breakpoints
            if self._check_hardware_breakpoints():
                return True
                
            # Memory breakpoints
            if self._scan_memory_breakpoints():
                return True
                
            # Code integrity verification
            if self._verify_code_integrity():
                return True
                
            return False

        except Exception:
            return False

    def check_sandbox_behavior(self) -> bool:
        """Advanced sandbox behavior detection"""
        try:
            # Check for artificial delays
            start_time = time.time()
            time.sleep(0.5)  
            if time.time() - start_time > 0.6:
                return True

            # Check number of running processes
            if len(psutil.pids()) < 50:  # Too few processes
                return True

            # Check disk size and memory
            disk = psutil.disk_usage('/')
            memory = psutil.virtual_memory()
            if disk.total < 60 * 1024 * 1024 * 1024 or memory.total < 2 * 1024 * 1024 * 1024:
                return True

            # Check for sandbox-specific environment variables
            sandbox_vars = {'SANDBOX', 'ANALYSIS', 'MALWARE', 'VIRUS'}
            if any(var in os.environ for var in sandbox_vars):
                return True

            return False

        except Exception:
            return False

    def detect_monitoring(self) -> bool:
        """Enhanced monitoring tool detection"""
        try:
            # Process scanning
            if self._scan_monitoring_processes():
                return True
                
            # Driver detection
            if self._detect_monitoring_drivers():
                return True
                
            # Registry monitoring
            if self._check_registry_monitors():
                return True
                
            # Network monitoring
            if self._detect_network_monitors():
                return True
                
            # Hook detection
            if self._check_api_hooks():
                return True
                
            # EDR detection
            if self._detect_edr_presence():
                return True
                
            # Hidden threads
            if self._find_monitoring_threads():
                return True
                
            return False

        except Exception:
            return False

    def anti_dump(self) -> None:
        """Advanced anti-dump protection"""
        try:
            # PE header manipulation
            self._corrupt_pe_header()
            
            # Memory protection
            self._protect_critical_memory()
            
            # Import table encryption
            self._encrypt_import_table()
            
            # TLS callback installation
            self._install_tls_callbacks()
            
            # Stack trace manipulation
            self._manipulate_stack_trace()
            
            # Section scrambling
            self._scramble_sections()

        except Exception:
            pass

    def _get_memory_regions(self) -> List[tuple]:
        """Get memory regions to protect"""
        regions = []
        try:
            mbi = ctypes.c_void_p()
            length = ctypes.c_ulong(0)
            while ctypes.windll.kernel32.VirtualQueryEx(
                ctypes.windll.kernel32.GetCurrentProcess(),
                mbi, ctypes.sizeof(mbi), ctypes.byref(length)
            ):
                if mbi.State == 0x1000 and mbi.Type == 0x20000:
                    regions.append((mbi.BaseAddress, mbi.RegionSize))
                mbi.BaseAddress += mbi.RegionSize
        except Exception:
            pass
        return regions

    def run_all_checks(self) -> bool:
        """Run all anti-analysis checks"""
        checks = [
            self.check_debugger,
            self.check_sandbox_behavior, 
            self.detect_monitoring,
            self._check_system_info,
            self._check_processes,
            self._check_services,
            self._check_files,
            self._check_registry,
            self._check_hardware,
            self._check_mac_address,
            self._check_memory,
            self._check_timing,
            self._check_artifacts,
            self._check_process_behavior,
            self._check_sandbox_artifacts,
            self._check_hardware_consistency
        ]

        # Apply anti-dump protection
        self.anti_dump()
        
        detected_by = []
        for check in checks:
            try:
                if check():
                    detected_by.append(check.__name__)
            except Exception as e:
                self.logger.error(f"Error in {check.__name__}: {str(e)}")
                
        if detected_by:
            self.logger.warning(f"Analysis environment detected by: {', '.join(detected_by)}")
            return True
            
        return False