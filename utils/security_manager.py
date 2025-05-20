from __future__ import annotations
import os
import ssl
import base64
import socket
import hashlib
import logging
import threading
import time
from typing import Dict, Optional, Tuple, Any, Union
from pathlib import Path
from datetime import datetime
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.x509.oid import NameOID
from cryptography.fernet import Fernet

from .cert_pinning import CertificatePinning
from .integrity import IntegrityChecker
from .memory_protection import MemoryProtection
from .advanced_protection import AdvancedProtection
from .anti_vm import AntiVM
from .code_obfuscation import CodeObfuscator
from .network_protection import NetworkProtection
from .crypto import Crypto, CryptoError

class SecurityError(Exception):
    """Security related errors"""
    pass

class SecurityManager:
    def __init__(self, is_server: bool = False, 
                 cert_dir: str = "certs",
                 verify_cert: bool = False) -> None:
        """Initialize security manager"""
        self.is_server = is_server
        self.cert_dir = Path(cert_dir)
        self.verify_cert = verify_cert
        self.logger = logging.getLogger('security')
        
        # Create cert directory
        self.cert_dir.mkdir(exist_ok=True)
        
        # Initialize components
        self.cert_pinning = CertificatePinning()
        self.integrity = IntegrityChecker()
        self.memory_protection = MemoryProtection()
        self.advanced_protection = AdvancedProtection()
        self.anti_vm = AntiVM()
        self.code_obfuscator = CodeObfuscator()
        self.network_protection = NetworkProtection()
        
        # Initialize crypto
        self.crypto = Crypto()
        
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.protected_data: Dict[str, Tuple[int, int]] = {}  # id: (address, size)
        
        # Protection settings
        self.check_interval = 300  # 5 minutes
        self.last_check = 0
        
        # Initialize security
        self._init_security()
        
    def _init_security(self) -> None:
        """Initialize all security components"""
        try:
            # Check for VM
            if self.anti_vm.check_all():
                raise SecurityError("VM environment detected")
                
            # Perform initial integrity check
            if not self.integrity.self_check():
                raise SecurityError("Integrity check failed")
                
            # Start protections
            self.memory_protection.start_protection()
            self.advanced_protection.start_protection()
            self.network_protection.start_protection()
            
            # Initialize SSL
            self._init_ssl()
            
            # Start integrity checking thread
            self._start_integrity_checking()
            
        except Exception as e:
            self.logger.error(f"Security initialization error: {str(e)}")
            raise
            
    def protect_data(self, data_id: str, data: bytes) -> bool:
        """Protect sensitive data in memory
        
        Args:
            data_id: Unique identifier for data
            data: Data to protect
            
        Returns:
            bool: True if protected successfully
        """
        try:
            # Remove old protected data if exists
            if data_id in self.protected_data:
                self.unprotect_data(data_id)
                
            # Use advanced protection
            address, size = self.advanced_protection.protect_memory(data_id, data)
            
            # Store reference
            self.protected_data[data_id] = (address, size)
            return True
            
        except Exception as e:
            self.logger.error(f"Error protecting data {data_id}: {str(e)}")
            return False
            
    def unprotect_data(self, data_id: str) -> Optional[bytes]:
        """Retrieve and unprotect data
        
        Args:
            data_id: Data identifier
            
        Returns:
            Optional[bytes]: Decrypted data or None if failed
        """
        try:
            if data_id not in self.protected_data:
                return None
                
            address, size = self.protected_data[data_id]
            
            # Decrypt using advanced protection
            data = self.advanced_protection.unprotect_memory(address)
            
            # Remove protection
            del self.protected_data[data_id]
            
            return data
            
        except Exception as e:
            self.logger.error(f"Error unprotecting data {data_id}: {str(e)}")
            return None
            
    def verify_connection(self, address: str, port: int) -> bool:
        """Verify if connection should be allowed
        
        Args:
            address: Remote address
            port: Remote port
            
        Returns:
            bool: True if connection allowed
        """
        return self.network_protection.verify_connection(address, port)
        
    def obfuscate_code(self, path: Union[str, Path],
                      exclude: Optional[Set[str]] = None) -> bool:
        """Obfuscate Python source code
        
        Args:
            path: File or directory path
            exclude: Files to exclude
            
        Returns:
            bool: True if obfuscated successfully
        """
        try:
            path = Path(path)
            if path.is_file():
                return self.code_obfuscator.obfuscate_file(str(path))
            else:
                return self.code_obfuscator.obfuscate_directory(
                    str(path),
                    exclude
                )
        except Exception as e:
            self.logger.error(f"Obfuscation error: {str(e)}")
            return False
            
    def cleanup(self) -> None:
        """Clean up all protected resources"""
        try:
            # Stop protections
            self.memory_protection.stop_protection()
            self.advanced_protection.stop_protection()
            self.network_protection.stop_protection()
            
            # Clear protected data
            for data_id in list(self.protected_data.keys()):
                self.unprotect_data(data_id)
                
            # Clean up sessions
            self.cleanup_sessions()
            
        except Exception as e:
            self.logger.error(f"Cleanup error: {str(e)}")
            
    def block_ip(self, address: str) -> None:
        """Block IP address
        
        Args:
            address: IP to block
        """
        self.network_protection.block_ip(address)
        
    def block_domain(self, domain: str) -> None:
        """Block domain
        
        Args:
            domain: Domain to block
        """
        self.network_protection.block_domain(domain)
        
    def encrypt_data(self, data: Union[str, bytes], peer_id: Optional[str] = None) -> Union[bytes, str]:
        """Encrypt data using crypto module
        
        Args:
            data: Data to encrypt
            peer_id: Optional peer ID for session encryption
            
        Returns:
            Encrypted data
        """
        return self.crypto.encrypt(data, peer_id)
        
    def decrypt_data(self, encrypted_data: Union[str, bytes], peer_id: Optional[str] = None) -> bytes:
        """Decrypt data using crypto module
        
        Args:
            encrypted_data: Data to decrypt
            peer_id: Optional peer ID for session decryption
            
        Returns:
            Decrypted data
        """
        return self.crypto.decrypt(encrypted_data, peer_id)
        
    def establish_crypto_session(self, peer_id: str, peer_public_key: str) -> str:
        """Establish encrypted session with peer
        
        Args:
            peer_id: Peer identifier
            peer_public_key: Peer's public key
            
        Returns:
            Encrypted session key
        """
        return self.crypto.establish_session(peer_id, peer_public_key)
        
    def receive_crypto_session(self, peer_id: str, encrypted_key: str) -> None:
        """Receive encrypted session from peer
        
        Args:
            peer_id: Peer identifier
            encrypted_key: Encrypted session key
        """
        self.crypto.receive_session_key(peer_id, encrypted_key)