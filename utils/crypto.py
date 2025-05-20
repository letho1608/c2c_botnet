from __future__ import annotations
import os
import base64
import logging
from typing import Optional, Union, Any
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

class Crypto:
    def __init__(self, key: Optional[bytes] = None) -> None:
        """Initialize crypto with optional key

        Args:
            key (Optional[bytes], optional): Encryption key. Defaults to None.
        """
        self.backend = default_backend()
        self.logger = logging.getLogger(__name__)
        
        if key:
            self.key = key
        else:
            self.key = self._generate_key()
            
        self.fernet = Fernet(base64.urlsafe_b64encode(self.key))
        
    def encrypt(self, data: Union[str, bytes]) -> bytes:
        """Encrypt data

        Args:
            data (Union[str, bytes]): Data to encrypt

        Returns:
            bytes: Encrypted data
        """
        try:
            # Convert string to bytes if needed
            if isinstance(data, str):
                data = data.encode()
                
            # Encrypt with Fernet
            encrypted = self.fernet.encrypt(data)
            return encrypted
            
        except Exception as e:
            self.logger.error(f"Encryption error: {str(e)}")
            raise
            
    def decrypt(self, encrypted_data: bytes) -> bytes:
        """Decrypt data

        Args:
            encrypted_data (bytes): Data to decrypt

        Returns:
            bytes: Decrypted data

        Raises:
            Exception: If decryption fails
        """
        try:
            # Decrypt with Fernet
            decrypted = self.fernet.decrypt(encrypted_data)
            return decrypted
            
        except Exception as e:
            self.logger.error(f"Decryption error: {str(e)}")
            raise
            
    def encrypt_file(self, input_path: str, output_path: str) -> bool:
        """Encrypt a file

        Args:
            input_path (str): Path to input file
            output_path (str): Path to save encrypted file

        Returns:
            bool: True if successful
        """
        try:
            # Read input file
            with open(input_path, 'rb') as f:
                data = f.read()
                
            # Encrypt data
            encrypted = self.encrypt(data)
            
            # Write encrypted data
            with open(output_path, 'wb') as f:
                f.write(encrypted)
                
            return True
            
        except Exception as e:
            self.logger.error(f"File encryption error: {str(e)}")
            return False
            
    def decrypt_file(self, input_path: str, output_path: str) -> bool:
        """Decrypt a file

        Args:
            input_path (str): Path to encrypted file
            output_path (str): Path to save decrypted file

        Returns:
            bool: True if successful
        """
        try:
            # Read encrypted file
            with open(input_path, 'rb') as f:
                encrypted = f.read()
                
            # Decrypt data
            decrypted = self.decrypt(encrypted)
            
            # Write decrypted data
            with open(output_path, 'wb') as f:
                f.write(decrypted)
                
            return True
            
        except Exception as e:
            self.logger.error(f"File decryption error: {str(e)}")
            return False
            
    def _generate_key(self) -> bytes:
        """Generate random encryption key

        Returns:
            bytes: Random 32-byte key
        """
        try:
            # Generate salt
            salt = os.urandom(16)
            
            # Generate key using PBKDF2
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
                backend=self.backend
            )
            
            key = kdf.derive(os.urandom(32))
            return key
            
        except Exception as e:
            self.logger.error(f"Key generation error: {str(e)}")
            raise
            
    def get_key_fingerprint(self) -> str:
        """Get fingerprint of current key

        Returns:
            str: Key fingerprint
        """
        try:
            # Calculate SHA256 hash of key
            digest = hashes.Hash(hashes.SHA256(), backend=self.backend)
            digest.update(self.key)
            fingerprint = digest.finalize()
            
            # Convert to hex string
            return fingerprint.hex()
            
        except Exception as e:
            self.logger.error(f"Fingerprint error: {str(e)}")
            raise
            
    def derive_key(self, password: str, salt: Optional[bytes] = None) -> bytes:
        """Derive key from password

        Args:
            password (str): Password to derive key from
            salt (Optional[bytes], optional): Salt for key derivation. Defaults to None.

        Returns:
            bytes: Derived key

        Raises:
            Exception: If key derivation fails
        """
        try:
            if not salt:
                salt = os.urandom(16)
                
            # Generate key using PBKDF2
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
                backend=self.backend
            )
            
            key = kdf.derive(password.encode())
            return key
            
        except Exception as e:
            self.logger.error(f"Key derivation error: {str(e)}")
            raise
            
    def encrypt_large_file(self, input_path: str, output_path: str, 
                          chunk_size: int = 64 * 1024) -> bool:
        """Encrypt a large file in chunks

        Args:
            input_path (str): Path to input file
            output_path (str): Path to save encrypted file
            chunk_size (int, optional): Chunk size in bytes. Defaults to 64KB.

        Returns:
            bool: True if successful
        """
        try:
            # Generate random IV
            iv = os.urandom(16)
            
            # Create AES cipher
            cipher = Cipher(
                algorithms.AES(self.key),
                modes.CBC(iv),
                backend=self.backend
            )
            encryptor = cipher.encryptor()
            
            with open(input_path, 'rb') as in_file, \
                 open(output_path, 'wb') as out_file:
                # Write IV
                out_file.write(iv)
                
                # Encrypt file in chunks
                while True:
                    chunk = in_file.read(chunk_size)
                    if not chunk:
                        break
                        
                    # Pad last chunk if needed
                    if len(chunk) % 16:
                        padding = 16 - (len(chunk) % 16)
                        chunk += bytes([padding]) * padding
                        
                    encrypted_chunk = encryptor.update(chunk)
                    out_file.write(encrypted_chunk)
                    
                # Write final block
                out_file.write(encryptor.finalize())
                
            return True
            
        except Exception as e:
            self.logger.error(f"Large file encryption error: {str(e)}")
            return False
            
    def decrypt_large_file(self, input_path: str, output_path: str,
                          chunk_size: int = 64 * 1024) -> bool:
        """Decrypt a large file in chunks

        Args:
            input_path (str): Path to encrypted file 
            output_path (str): Path to save decrypted file
            chunk_size (int, optional): Chunk size in bytes. Defaults to 64KB.

        Returns:
            bool: True if successful
        """
        try:
            with open(input_path, 'rb') as in_file, \
                 open(output_path, 'wb') as out_file:
                # Read IV
                iv = in_file.read(16)
                
                # Create AES cipher
                cipher = Cipher(
                    algorithms.AES(self.key),
                    modes.CBC(iv),
                    backend=self.backend
                )
                decryptor = cipher.decryptor()
                
                # Decrypt file in chunks
                while True:
                    chunk = in_file.read(chunk_size)
                    if not chunk:
                        break
                        
                    decrypted_chunk = decryptor.update(chunk)
                    out_file.write(decrypted_chunk)
                    
                # Write final block and remove padding
                final_chunk = decryptor.finalize()
                if final_chunk:
                    padding = final_chunk[-1]
                    out_file.write(final_chunk[:-padding])
                    
            return True
            
        except Exception as e:
            self.logger.error(f"Large file decryption error: {str(e)}")
            return False