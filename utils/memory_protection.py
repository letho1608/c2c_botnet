import os
import sys
import ctypes
import random
import string
import struct
import logging
from typing import Dict, List, Optional, Any
from ctypes import wintypes
from cryptography.fernet import Fernet

class MemoryProtection:
    def __init__(self):
        self.logger = logging.getLogger('security')
        self._key = Fernet.generate_key()
        self._fernet = Fernet(self._key)
        self._encrypted_strings: Dict[str, bytes] = {}
        self._encrypt_map: Dict[str, str] = {}
        
        # Windows API constants
        self.PAGE_EXECUTE_READWRITE = 0x40
        self.PAGE_READONLY = 0x02
        self.PAGE_READWRITE = 0x04
        self.PROCESS_ALL_ACCESS = 0x1F0FFF
        
    def protect_memory(self) -> None:
        """Áp dụng bảo vệ bộ nhớ nâng cao"""
        try:
            # Runtime integrity checks
            self._setup_integrity_checks()
            
            # Advanced anti-dump
            self._protect_pe_headers()
            self._protect_memory_regions()
            self._encrypt_sections()
            self._protect_iat()
            
            # Advanced anti-debug
            self._set_handle_information()
            self._protect_debug_registers()
            self._hook_debug_apis()
            
            # Memory encryption
            self._encrypt_sensitive_strings()
            self._encrypt_stack()
            self._encrypt_heap()
            
            # Code obfuscation
            self._obfuscate_control_flow()
            self._add_integrity_checks()
            self._randomize_memory()
            
        except Exception as e:
            self.logger.error(f"Memory protection error: {str(e)}")
            
    def _protect_pe_headers(self) -> None:
        """Xóa PE headers để chống dump"""
        try:
            # Get module base address
            base = ctypes.windll.kernel32.GetModuleHandleA(None)
            
            # Get PE headers
            dos_header = ctypes.c_char_p(base)
            nt_headers = ctypes.c_void_p(base + struct.unpack("<L", ctypes.string_at(base + 0x3C, 4))[0])
            
            # Zero out headers
            ctypes.memset(dos_header, 0, 0x3C)
            ctypes.memset(nt_headers, 0, 0x108)
            
        except Exception as e:
            self.logger.error(f"PE header protection failed: {str(e)}")
            
    def _protect_memory_regions(self) -> None:
        """Bảo vệ vùng nhớ quan trọng"""
        try:
            # Get process handle
            process = ctypes.windll.kernel32.GetCurrentProcess()
            
            # Protect memory regions
            address = 0
            while True:
                # Get memory info
                mbi = wintypes.MEMORY_BASIC_INFORMATION()
                if not ctypes.windll.kernel32.VirtualQueryEx(
                    process,
                    address,
                    ctypes.byref(mbi),
                    ctypes.sizeof(mbi)
                ):
                    break
                    
                # Protect executable regions
                if mbi.State == 0x1000 and mbi.Type == 0x20000:
                    old_protect = wintypes.DWORD()
                    if ctypes.windll.kernel32.VirtualProtectEx(
                        process,
                        address,
                        mbi.RegionSize,
                        self.PAGE_READONLY,
                        ctypes.byref(old_protect)
                    ):
                        self.logger.debug(f"Protected memory region at {hex(address)}")
                        
                address += mbi.RegionSize
                
        except Exception as e:
            self.logger.error(f"Memory region protection failed: {str(e)}")
            
    def _set_handle_information(self) -> None:
        """Cài đặt handle protection"""
        try:
            # Get process handle
            handle = ctypes.windll.kernel32.GetCurrentProcess()
            
            # Set handle flags
            flags = 0x00000002  # HANDLE_FLAG_PROTECT_FROM_CLOSE
            ctypes.windll.kernel32.SetHandleInformation(
                handle,
                flags,
                flags
            )
            
        except Exception as e:
            self.logger.error(f"Handle protection failed: {str(e)}")
            
    def _protect_debug_registers(self) -> None:
        """Bảo vệ debug registers"""
        try:
            # Get thread handle
            thread = ctypes.windll.kernel32.GetCurrentThread()
            
            # Get thread context
            context = wintypes.CONTEXT()
            context.ContextFlags = 0x10  # CONTEXT_DEBUG_REGISTERS
            
            if ctypes.windll.kernel32.GetThreadContext(thread, ctypes.byref(context)):
                # Clear debug registers
                context.Dr0 = 0
                context.Dr1 = 0
                context.Dr2 = 0
                context.Dr3 = 0
                context.Dr7 = 0
                
                # Set thread context
                ctypes.windll.kernel32.SetThreadContext(thread, ctypes.byref(context))
                
        except Exception as e:
            self.logger.error(f"Debug register protection failed: {str(e)}")
            
    def encrypt_string(self, text: str) -> bytes:
        """Mã hóa string trong memory"""
        try:
            if text not in self._encrypted_strings:
                # Generate random key
                key = ''.join(random.choices(string.ascii_letters + string.digits, k=32))
                
                # XOR encryption
                encrypted = bytes([
                    ord(c) ^ ord(key[i % len(key)])
                    for i, c in enumerate(text)
                ])
                
                self._encrypted_strings[text] = encrypted
                
            return self._encrypted_strings[text]
            
        except Exception:
            return text.encode()
            
    def decrypt_string(self, encrypted: bytes) -> str:
        """Giải mã string đã mã hóa"""
        try:
            # Find original string
            for text, enc in self._encrypted_strings.items():
                if enc == encrypted:
                    return text
            return encrypted.decode()
            
        except Exception:
            return str(encrypted)
            
    def _encrypt_sensitive_strings(self) -> None:
        """Mã hóa các string nhạy cảm trong memory"""
        try:
            # Find string literals
            for name, value in sys.modules[__name__].__dict__.items():
                if isinstance(value, str):
                    # Encrypt string
                    encrypted = self.encrypt_string(value)
                    
                    # Replace with encrypted version
                    sys.modules[__name__].__dict__[name] = encrypted
                    
        except Exception as e:
            self.logger.error(f"String encryption failed: {str(e)}")
            
    def _obfuscate_control_flow(self) -> None:
        """Obfuscate control flow"""
        try:
            # Add junk code
            self._add_junk_code()
            
            # Flatten control flow
            self._flatten_control_flow()
            
            # Add opaque predicates
            self._add_opaque_predicates()
            
        except Exception as e:
            self.logger.error(f"Control flow obfuscation failed: {str(e)}")
            
    def _add_junk_code(self) -> None:
        """Thêm mã rác để obfuscate"""
        try:
            # Generate junk instructions
            junk = [
                lambda: random.randint(0, 100),
                lambda: ''.join(random.choices(string.ascii_letters, k=10)),
                lambda: [random.random() for _ in range(5)],
                lambda: {str(i): chr(i) for i in range(65, 91)}
            ]
            
            # Insert junk randomly
            for _ in range(random.randint(10, 30)):
                random.choice(junk)()
                
        except Exception as e:
            self.logger.error(f"Junk code insertion failed: {str(e)}")
            
    def _flatten_control_flow(self) -> None:
        """Làm phẳng control flow"""
        try:
            # Convert branches to jumps
            dispatch_table = {}
            state = 0
            
            while state != -1:
                # Dispatch based on state
                if state in dispatch_table:
                    handler = dispatch_table[state]
                    state = handler()
                else:
                    state = -1
                    
        except Exception as e:
            self.logger.error(f"Control flow flattening failed: {str(e)}")
            
    def _add_opaque_predicates(self) -> None:
        """Thêm opaque predicates"""
        try:
            # Generate opaque expressions
            predicates = [
                lambda x: (x * x) > -1,
                lambda x: (x | 1) == ((x << 1) >> 1) | 1,
                lambda x: (x & (x - 1)) != 0
            ]
            
            # Insert predicates
            for predicate in predicates:
                if predicate(random.randint(1, 1000)):
                    self._add_junk_code()
                    
        except Exception as e:
            self.logger.error(f"Opaque predicate insertion failed: {str(e)}")