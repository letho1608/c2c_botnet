from __future__ import annotations
import os
import sys
import hmac
import hashlib
import logging
import platform
from typing import Dict, Set, Optional
from pathlib import Path
import psutil
import win32api
import win32security

class IntegrityChecker:
    def __init__(self, hash_file: str = "file_hashes.txt") -> None:
        """Initialize integrity checker
        
        Args:
            hash_file (str): File containing file hashes
        """
        self.hash_file = Path(hash_file)
        self.hashes: Dict[str, str] = {}
        self.logger = logging.getLogger('security')
        
        # Files to monitor
        self.critical_files = {
            'client.py',
            'server.py',
            'utils/security_manager.py',
            'utils/cert_pinning.py',  
            'utils/integrity.py'
        }
        
        # Load stored hashes
        self._load_hashes()
        
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
            
    def calculate_file_hash(self, file_path: str) -> Optional[str]:
        """Calculate SHA256 hash of file
        
        Args:
            file_path (str): Path to file
            
        Returns:
            Optional[str]: File hash or None if error
        """
        try:
            sha256 = hashlib.sha256()
            with open(file_path, 'rb') as f:
                while True:
                    data = f.read(65536)  # Read in 64kb chunks
                    if not data:
                        break
                    sha256.update(data)
            return sha256.hexdigest()
        except Exception as e:
            self.logger.error(f"Error calculating hash for {file_path}: {str(e)}")
            return None
            
    def update_hashes(self) -> None:
        """Update stored hashes for all critical files"""
        try:
            for file_path in self.critical_files:
                if Path(file_path).exists():
                    file_hash = self.calculate_file_hash(file_path)
                    if file_hash:
                        self.hashes[file_path] = file_hash
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
            for file_path in self.critical_files:
                if not self.verify_file(file_path):
                    self.logger.warning(f"Modified file detected: {file_path}")
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
        return all([
            self.verify_all(),
            self.check_permissions(),
            self.verify_memory()
        ])