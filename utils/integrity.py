from __future__ import annotations
import os
import sys
import hmac
import hashlib
import logging
import platform
import threading
import time
from typing import Dict, Set, Optional, List
from pathlib import Path
from functools import lru_cache
from concurrent.futures import ThreadPoolExecutor
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import psutil
import win32api
import win32security

class FileChangeHandler(FileSystemEventHandler):
    def __init__(self, checker: 'IntegrityChecker'):
        self.checker = checker
        
    def on_modified(self, event):
        if not event.is_directory:
            path = Path(event.src_path).as_posix()
            if path in self.checker.critical_files:
                self.checker.logger.warning(f"File modified: {path}")
                self.checker.file_changed.add(path)

class IntegrityChecker:
    def __init__(self, hash_file: str = "file_hashes.txt",
                max_workers: int = 4) -> None:
        """Initialize integrity checker
        
        Args:
            hash_file (str): File containing file hashes
            max_workers (int): Maximum number of worker threads
        """
        self.hash_file = Path(hash_file)
        self.hashes: Dict[str, str] = {}
        self.logger = logging.getLogger('security')
        self.thread_pool = ThreadPoolExecutor(max_workers=max_workers)
        
        # Files to monitor
        self.critical_files = {
            'client.py',
            'server.py',
            'utils/security_manager.py',
            'utils/cert_pinning.py',
            'utils/integrity.py'
        }
        
        # Track modified files
        self.file_changed: Set[str] = set()
        
        # Setup file watching
        self.observer = Observer()
        self.observer.schedule(
            FileChangeHandler(self),
            path='.',
            recursive=True
        )
        self.observer.start()
        
        # Load stored hashes
        self._load_hashes()
        
        # Calculate initial hashes
        self.update_hashes()
        
    def _load_hashes(self) -> None:
        """Load stored file hashes"""
        try:
            if self.hash_file.exists():
                content = self.hash_file.read_text()
                for line in content.splitlines():
                    if ':' in line:
                        path, hash_value = line.split(':', 1)
                        self.hashes[path] = hash_value
        except Exception as e:
            self.logger.error(f"Error loading hashes: {str(e)}")
            
    def save_hashes(self) -> None:
        """Save current file hashes"""
        try:
            content = '\n'.join(f"{path}:{hash_value}" 
                              for path, hash_value in self.hashes.items())
            self.hash_file.write_text(content)
        except Exception as e:
            self.logger.error(f"Error saving hashes: {str(e)}")
            
    @lru_cache(maxsize=128)
    def calculate_file_hash(self, file_path: str) -> Optional[str]:
        """Calculate SHA256 hash of file
        
        Args:
            file_path (str): Path to file
            
        Returns:
            Optional[str]: File hash or None if error
        """
        try:
            if not os.path.exists(file_path):
                return None
                
            # Get file stats for cache invalidation
            stats = os.stat(file_path)
            cache_key = f"{file_path}:{stats.st_mtime}:{stats.st_size}"
            
            # Calculate hash in chunks
            sha256 = hashlib.sha256()
            with open(file_path, 'rb') as f:
                # Use memoryview for efficient chunk processing
                for chunk in iter(lambda: f.read(65536), b''):
                    sha256.update(chunk)
                    
            return sha256.hexdigest()
            
        except Exception as e:
            self.logger.error(f"Error calculating hash for {file_path}: {str(e)}")
            return None
            
    def update_hashes(self) -> None:
        """Update stored hashes for all critical files"""
        try:
            # Clear cache
            self.calculate_file_hash.cache_clear()
            
            # Calculate hashes in parallel
            futures = []
            for file_path in self.critical_files:
                if Path(file_path).exists():
                    future = self.thread_pool.submit(
                        self.calculate_file_hash,
                        file_path
                    )
                    futures.append((file_path, future))
                    
            # Collect results
            for file_path, future in futures:
                try:
                    file_hash = future.result()
                    if file_hash:
                        self.hashes[file_path] = file_hash
                except Exception as e:
                    self.logger.error(
                        f"Error calculating hash for {file_path}: {str(e)}"
                    )
                    
            self.save_hashes()
            
        except Exception as e:
            self.logger.error(f"Error updating hashes: {str(e)}")
            
    def verify_file(self, file_path: str) -> bool:
        """Verify integrity of file
        
        Args:
            file_path (str): Path to file to verify
            
        Returns:
            bool: True if file is unmodified
        """
        try:
            if file_path not in self.hashes:
                return False
                
            current_hash = self.calculate_file_hash(file_path)
            if not current_hash:
                return False
                
            return current_hash == self.hashes[file_path]
            
        except Exception as e:
            self.logger.error(f"Error verifying file {file_path}: {str(e)}")
            return False
            
    def verify_all(self) -> bool:
        """Verify all critical files
        
        Returns:
            bool: True if all files are unmodified
        """
        try:
            # Check for files modified since last check
            if self.file_changed:
                for path in self.file_changed:
                    self.logger.warning(f"File modified: {path}")
                self.file_changed.clear()
                return False
                
            # Verify files in parallel
            futures = []
            for file_path in self.critical_files:
                future = self.thread_pool.submit(self.verify_file, file_path)
                futures.append((file_path, future))
                
            # Check results
            for file_path, future in futures:
                try:
                    if not future.result():
                        self.logger.warning(f"Modified file detected: {file_path}")
                        return False
                except Exception as e:
                    self.logger.error(
                        f"Error verifying {file_path}: {str(e)}"
                    )
                    return False
                    
            return True
            
        except Exception as e:
            self.logger.error(f"Error verifying files: {str(e)}")
            return False
            
    def check_permissions(self) -> bool:
        """Check file permissions
        
        Returns:
            bool: True if permissions are correct
        """
        try:
            for file_path in self.critical_files:
                path = Path(file_path)
                if not path.exists():
                    continue
                    
                # Get file security descriptor
                sd = win32security.GetFileSecurity(
                    str(path), 
                    win32security.DACL_SECURITY_INFORMATION
                )
                
                # Get DACL
                dacl = sd.GetSecurityDescriptorDacl()
                if not dacl:
                    self.logger.warning(f"No DACL for {file_path}")
                    return False
                    
                # Check for unauthorized permissions
                for i in range(dacl.GetAceCount()):
                    ace = dacl.GetAce(i)
                    if not self._check_ace_permissions(ace):
                        self.logger.warning(
                            f"Invalid permissions on {file_path}: {ace}"
                        )
                        return False
                        
            return True
            
        except Exception as e:
            self.logger.error(f"Error checking permissions: {str(e)}")
            return False
            
    def _check_ace_permissions(self, ace: Any) -> bool:
        """Check if ACE permissions are valid
        
        Args:
            ace: Access control entry to check
            
        Returns:
            bool: True if permissions are valid
        """
        try:
            # Get ACE components
            flags, access, sid = ace
            
            # Get account info
            name, domain, type = win32security.LookupAccountSid(None, sid)
            
            # Only allow administrators full control
            if type != win32security.SidTypeUser:
                return True  # Allow non-user SIDs
                
            admin_sid = win32security.CreateWellKnownSid(
                win32security.WinBuiltinAdministratorsSid
            )
            
            if sid == admin_sid:
                return True
                
            # Others should only have read access
            full_access = (
                win32security.GENERIC_ALL |
                win32security.GENERIC_WRITE |
                win32security.GENERIC_EXECUTE
            )
            
            return not (access & full_access)
            
        except Exception as e:
            self.logger.error(f"Error checking ACE: {str(e)}")
            return False
            
    def verify_memory(self) -> bool:
        """Check for memory modifications
        
        Returns:
            bool: True if memory is unmodified
        """
        try:
            # Get own process
            process = psutil.Process()
            
            # Check for debugger
            if process.is_running() and process.status() == psutil.STATUS_TRACED:
                self.logger.warning("Debugger detected")
                return False
                
            # Check loaded modules
            dangerous_dlls = {
                'spy.dll',
                'inject.dll',
                'hook.dll'
            }
            
            for module in process.memory_maps():
                path = Path(module.path).name.lower()
                if path in dangerous_dlls:
                    self.logger.warning(f"Suspicious DLL loaded: {path}")
                    return False
                    
            return True
            
        except Exception as e:
            self.logger.error(f"Error checking memory: {str(e)}")
            return False
            
    def self_check(self) -> bool:
        """Perform self integrity check
        
        Returns:
            bool: True if all checks pass
        """
        try:
            # Run checks in parallel
            with ThreadPoolExecutor(max_workers=3) as executor:
                futures = [
                    executor.submit(self.verify_all),
                    executor.submit(self.check_permissions),
                    executor.submit(self.verify_memory)
                ]
                
                results = [future.result() for future in futures]
                return all(results)
                
        except Exception as e:
            self.logger.error(f"Self check error: {str(e)}")
            return False
            
    def cleanup(self):
        """Cleanup resources"""
        self.observer.stop()
        self.observer.join()
        self.thread_pool.shutdown()