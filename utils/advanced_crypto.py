from __future__ import annotations
import os
import base64
import json
import logging
from typing import Dict, Optional, Tuple, Union
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend

class AdvancedCrypto:
    def __init__(self, key_size: int = 2048) -> None:
        """Initialize crypto with new or existing keys

        Args:
            key_size (int, optional): RSA key size in bits. Defaults to 2048.
        """
        self.logger = logging.getLogger(__name__)
        self.backend = default_backend()
        self.key_size = key_size
        
        # Generate or load RSA keys
        self.private_key = None
        self.public_key = None
        self._load_or_generate_keys()
        
        # Session keys for each peer
        self.session_keys: Dict[str, bytes] = {}
        
    def _load_or_generate_keys(self) -> None:
        """Load existing keys or generate new ones"""
        try:
            if os.path.exists('private.pem'):
                with open('private.pem', 'rb') as f:
                    self.private_key = serialization.load_pem_private_key(
                        f.read(),
                        password=None,
                        backend=self.backend
                    )
                with open('public.pem', 'rb') as f:
                    self.public_key = serialization.load_pem_public_key(
                        f.read(),
                        backend=self.backend
                    )
            else:
                self._generate_rsa_keys()
                
        except Exception as e:
            self.logger.error(f"Error loading keys: {str(e)}")
            self._generate_rsa_keys()
            
    def _generate_rsa_keys(self) -> None:
        """Generate new RSA key pair"""
        try:
            # Generate private key
            self.private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=self.key_size,
                backend=self.backend
            )
            
            # Get public key
            self.public_key = self.private_key.public_key()
            
            # Save keys
            self._save_keys()
            
        except Exception as e:
            self.logger.error(f"Error generating keys: {str(e)}")
            raise
            
    def _save_keys(self) -> None:
        """Save keys to files"""
        try:
            # Save private key
            pem = self.private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            )
            with open('private.pem', 'wb') as f:
                f.write(pem)
                
            # Save public key
            pem = self.public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
            with open('public.pem', 'wb') as f:
                f.write(pem)
                
        except Exception as e:
            self.logger.error(f"Error saving keys: {str(e)}")
            
    def get_public_key(self) -> str:
        """Get public key in PEM format

        Returns:
            str: PEM encoded public key
        """
        try:
            pem = self.public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
            return pem.decode()
        except Exception as e:
            self.logger.error(f"Error exporting public key: {str(e)}")
            raise
            
    def establish_session(self, peer_id: str, peer_public_key: str) -> str:
        """Establish encrypted session with peer

        Args:
            peer_id (str): Unique peer identifier
            peer_public_key (str): Peer's public key in PEM format

        Returns:
            str: Encrypted session key
        """
        try:
            # Generate session key
            session_key = os.urandom(32)
            self.session_keys[peer_id] = session_key
            
            # Load peer public key
            peer_key = serialization.load_pem_public_key(
                peer_public_key.encode(),
                backend=self.backend
            )
            
            # Encrypt session key with peer public key
            encrypted_key = peer_key.encrypt(
                session_key,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            
            return base64.b64encode(encrypted_key).decode()
            
        except Exception as e:
            self.logger.error(f"Error establishing session: {str(e)}")
            raise
            
    def receive_session_key(self, peer_id: str, encrypted_key: str) -> None:
        """Receive and decrypt session key from peer

        Args:
            peer_id (str): Unique peer identifier
            encrypted_key (str): Base64 encoded encrypted session key
        """
        try:
            # Decrypt session key
            encrypted = base64.b64decode(encrypted_key)
            session_key = self.private_key.decrypt(
                encrypted,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            
            # Store session key
            self.session_keys[peer_id] = session_key
            
        except Exception as e:
            self.logger.error(f"Error receiving session key: {str(e)}")
            raise
            
    def encrypt(self, peer_id: str, data: Union[str, bytes]) -> str:
        """Encrypt data for peer using session key

        Args:
            peer_id (str): Peer identifier
            data (Union[str, bytes]): Data to encrypt

        Returns:
            str: Base64 encoded encrypted data
        """
        try:
            if peer_id not in self.session_keys:
                raise ValueError(f"No session key for peer {peer_id}")
                
            # Get session key
            key = self.session_keys[peer_id]
            
            # Generate IV
            iv = os.urandom(16)
            
            # Create cipher
            cipher = Cipher(
                algorithms.AES(key),
                modes.GCM(iv),
                backend=self.backend
            )
            encryptor = cipher.encryptor()
            
            # Convert string to bytes if needed
            if isinstance(data, str):
                data = data.encode()
                
            # Encrypt data
            ciphertext = encryptor.update(data) + encryptor.finalize()
            
            # Combine IV, ciphertext and tag
            encrypted = {
                'iv': base64.b64encode(iv).decode(),
                'ciphertext': base64.b64encode(ciphertext).decode(),
                'tag': base64.b64encode(encryptor.tag).decode()
            }
            
            return base64.b64encode(json.dumps(encrypted).encode()).decode()
            
        except Exception as e:
            self.logger.error(f"Error encrypting data: {str(e)}")
            raise
            
    def decrypt(self, peer_id: str, encrypted_data: str) -> bytes:
        """Decrypt data from peer using session key

        Args:
            peer_id (str): Peer identifier
            encrypted_data (str): Base64 encoded encrypted data

        Returns:
            bytes: Decrypted data
        """
        try:
            if peer_id not in self.session_keys:
                raise ValueError(f"No session key for peer {peer_id}")
                
            # Get session key
            key = self.session_keys[peer_id]
            
            # Parse encrypted data
            encrypted = json.loads(base64.b64decode(encrypted_data))
            iv = base64.b64decode(encrypted['iv'])
            ciphertext = base64.b64decode(encrypted['ciphertext'])
            tag = base64.b64decode(encrypted['tag'])
            
            # Create cipher
            cipher = Cipher(
                algorithms.AES(key),
                modes.GCM(iv, tag),
                backend=self.backend
            )
            decryptor = cipher.decryptor()
            
            # Decrypt data
            return decryptor.update(ciphertext) + decryptor.finalize()
            
        except Exception as e:
            self.logger.error(f"Error decrypting data: {str(e)}")
            raise
            
    def derive_key(self, password: str, salt: Optional[bytes] = None) -> Tuple[bytes, bytes]:
        """Derive key from password

        Args:
            password (str): Password to derive key from
            salt (Optional[bytes], optional): Salt for key derivation. Defaults to None.

        Returns:
            Tuple[bytes, bytes]: (key, salt) tuple
        """
        try:
            if not salt:
                salt = os.urandom(16)
                
            # Create KDF
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
                backend=self.backend
            )
            
            # Derive key
            key = kdf.derive(password.encode())
            
            return key, salt
            
        except Exception as e:
            self.logger.error(f"Error deriving key: {str(e)}")
            raise
            
    def verify_key(self, password: str, key: bytes, salt: bytes) -> bool:
        """Verify password against key

        Args:
            password (str): Password to verify
            key (bytes): Key to verify against
            salt (bytes): Salt used for key derivation

        Returns:
            bool: True if password matches key
        """
        try:
            # Create KDF
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
                backend=self.backend
            )
            
            # Verify password
            kdf.verify(password.encode(), key)
            return True
            
        except Exception:
            return False