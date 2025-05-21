from __future__ import annotations
import os
import base64
import json
import logging
import time
from typing import Dict, Optional, Tuple, Union, Any
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
from cryptography.exceptions import InvalidKey, InvalidSignature

class CryptoError(Exception):
    """Crypto operation errors"""
    pass

class Crypto:
    """Cryptographic operations handler"""
    def __init__(self, key: Optional[bytes] = None, key_size: int = 2048) -> None:
        """Initialize crypto with optional key

        Args:
            key (Optional[bytes], optional): Symmetric encryption key. Defaults to None.
            key_size (int, optional): RSA key size in bits. Defaults to 2048.
        """
        if key_size < 2048:
            raise CryptoError("Key size must be at least 2048 bits")
            
        self.backend = default_backend()
        self.logger = logging.getLogger(__name__)
        self.key_size = key_size
        
        # Load or generate symmetric key
        if key:
            if len(key) != 32:
                raise CryptoError("Key must be 32 bytes")
            self.key = key
        else:
            self.key = self._generate_key()
        self.fernet = Fernet(base64.urlsafe_b64encode(self.key))

        # Load or generate asymmetric keys
        self.private_key = None
        self.public_key = None
        self._load_or_generate_keys()

        # Session keys for peers with TTL
        self.session_keys: Dict[str, Tuple[bytes, float]] = {}
        self._last_cleanup = time.time()

    def _load_or_generate_keys(self) -> None:
        """Load existing RSA keys or generate new ones"""
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
            self.private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=self.key_size,
                backend=self.backend
            )
            self.public_key = self.private_key.public_key()
            self._save_keys()

        except Exception as e:
            self.logger.error(f"Error generating RSA keys: {str(e)}")
            raise

    def _save_keys(self) -> None:
        """Save RSA keys to files"""
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
            self.logger.error(f"Error saving RSA keys: {str(e)}")

    def _generate_key(self) -> bytes:
        """Generate random symmetric key

        Returns:
            bytes: Random 32-byte key
        """
        try:
            salt = os.urandom(16)
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
                backend=self.backend
            )
            return kdf.derive(os.urandom(32))

        except Exception as e:
            self.logger.error(f"Key generation error: {str(e)}")
            raise

    def encrypt(self, data: Union[str, bytes], peer_id: Optional[str] = None) -> Union[bytes, str]:
        """Encrypt data using symmetric or session key

        Args:
            data (Union[str, bytes]): Data to encrypt
            peer_id (Optional[str], optional): Peer ID for session encryption. Defaults to None.

        Returns:
            Union[bytes, str]: Encrypted data
        """
        if not data:
            raise CryptoError("Empty data provided for encryption")
            
        # Cleanup expired sessions
        self._cleanup_expired_sessions()
        try:
            # Convert string to bytes if needed
            if isinstance(data, str):
                data = data.encode()

            if peer_id:
                # Use session key encryption
                if peer_id not in self.session_keys:
                    raise ValueError(f"No session key for peer {peer_id}")

                key = self.session_keys[peer_id]
                iv = os.urandom(16)

                cipher = Cipher(
                    algorithms.AES(key),
                    modes.GCM(iv),
                    backend=self.backend
                )
                encryptor = cipher.encryptor()
                ciphertext = encryptor.update(data) + encryptor.finalize()

                encrypted = {
                    'iv': base64.b64encode(iv).decode(),
                    'ciphertext': base64.b64encode(ciphertext).decode(),
                    'tag': base64.b64encode(encryptor.tag).decode()
                }
                return base64.b64encode(json.dumps(encrypted).encode()).decode()

            else:
                # Use symmetric encryption
                return self.fernet.encrypt(data)

        except Exception as e:
            self.logger.error(f"Encryption error: {str(e)}")
            raise

    def decrypt(self, encrypted_data: Union[str, bytes], peer_id: Optional[str] = None) -> bytes:
        """Decrypt data using symmetric or session key

        Args:
            encrypted_data (Union[str, bytes]): Data to decrypt
            peer_id (Optional[str], optional): Peer ID for session decryption. Defaults to None.

        Returns:
            bytes: Decrypted data
        """
        if not encrypted_data:
            raise CryptoError("Empty data provided for decryption")
            
        # Cleanup expired sessions
        self._cleanup_expired_sessions()
        try:
            if peer_id:
                # Use session key decryption
                if peer_id not in self.session_keys:
                    raise ValueError(f"No session key for peer {peer_id}")

                key = self.session_keys[peer_id]
                encrypted = json.loads(base64.b64decode(encrypted_data))
                
                iv = base64.b64decode(encrypted['iv'])
                ciphertext = base64.b64decode(encrypted['ciphertext'])
                tag = base64.b64decode(encrypted['tag'])

                cipher = Cipher(
                    algorithms.AES(key),
                    modes.GCM(iv, tag),
                    backend=self.backend
                )
                decryptor = cipher.decryptor()
                return decryptor.update(ciphertext) + decryptor.finalize()

            else:
                # Use symmetric decryption
                return self.fernet.decrypt(encrypted_data)

        except Exception as e:
            self.logger.error(f"Decryption error: {str(e)}")
            raise

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
        if not peer_id or not peer_public_key:
            raise CryptoError("Invalid peer ID or public key")
        """Establish encrypted session with peer

        Args:
            peer_id (str): Unique peer identifier
            peer_public_key (str): Peer's public key in PEM format

        Returns:
            str: Encrypted session key
        """
        try:
            session_key = os.urandom(32)
            self.session_keys[peer_id] = session_key

            peer_key = serialization.load_pem_public_key(
                peer_public_key.encode(),
                backend=self.backend
            )

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
        if not peer_id or not encrypted_key:
            raise CryptoError("Invalid peer ID or encrypted key")
        """Receive and decrypt session key from peer

        Args:
            peer_id (str): Unique peer identifier  
            encrypted_key (str): Base64 encoded encrypted session key
        """
        try:
            encrypted = base64.b64decode(encrypted_key)
            session_key = self.private_key.decrypt(
                encrypted,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            self.session_keys[peer_id] = session_key

        except Exception as e:
            self.logger.error(f"Error receiving session key: {str(e)}")
            raise

    def derive_key(self, password: str, salt: Optional[bytes] = None) -> Tuple[bytes, bytes]:
        if not password:
            raise CryptoError("Empty password provided")
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

            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
                backend=self.backend
            )

            key = kdf.derive(password.encode())
            return key, salt

        except Exception as e:
            self.logger.error(f"Error deriving key: {str(e)}")
            raise

    def verify_key(self, password: str, key: bytes, salt: bytes) -> bool:
        if not password or not key or not salt:
            raise CryptoError("Invalid password, key or salt")
        """Verify password against key

        Args:
            password (str): Password to verify 
            key (bytes): Key to verify against
            salt (bytes): Salt used for key derivation

        Returns:
            bool: True if password matches key
        """
        try:
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
                backend=self.backend
            )
            kdf.verify(password.encode(), key)
            return True

        except Exception:
            return False

    def _cleanup_expired_sessions(self) -> None:
        """Remove expired session keys"""
        current_time = time.time()
        # Cleanup every 5 minutes
        if current_time - self._last_cleanup < 300:
            return
            
        expired = []
        for peer_id, (_, expiry) in self.session_keys.items():
            if current_time > expiry:
                expired.append(peer_id)
                
        for peer_id in expired:
            del self.session_keys[peer_id]
            
        self._last_cleanup = current_time

    @contextmanager
    def _file_encryption_context(self, mode: str):
        """Context manager for file encryption/decryption"""
        cipher = None
        try:
            # Generate IV and create cipher
            iv = os.urandom(16)
            cipher = Cipher(
                algorithms.AES(self.key),
                modes.CBC(iv),
                backend=self.backend
            )
            yield cipher, iv
        finally:
            if cipher:
                # Ensure cipher is properly closed
                del cipher

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
        if not input_path or not output_path:
            raise CryptoError("Invalid input or output path")
        if not os.path.exists(input_path):
            raise CryptoError(f"Input file not found: {input_path}")
        try:
            with self._file_encryption_context('encrypt') as (cipher, iv), \
                 open(input_path, 'rb') as in_file, \
                 open(output_path, 'wb') as out_file:
                
                encryptor = cipher.encryptor()
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
        if not input_path or not output_path:
            raise CryptoError("Invalid input or output path")
        if not os.path.exists(input_path):
            raise CryptoError(f"Input file not found: {input_path}")
            
        try:
            with open(input_path, 'rb') as in_file:
                # Read IV first
                iv = in_file.read(16)
                if len(iv) != 16:
                    raise CryptoError("Invalid IV in encrypted file")

                with self._file_encryption_context('decrypt') as (cipher, _), \
                     open(output_path, 'wb') as out_file:
                    
                    # Override IV from context with the one from file
                    cipher = Cipher(
                        algorithms.AES(self.key),
                        modes.CBC(iv),
                        backend=self.backend
                    )
                    decryptor = cipher.decryptor()

                    # Use memoryview for efficient chunk processing
                    while True:
                        chunk = in_file.read(chunk_size)
                        if not chunk:
                            break

                        decrypted_chunk = decryptor.update(chunk)
                        out_file.write(decrypted_chunk)

                    # Write final block and remove padding
                    final_chunk = decryptor.finalize()
                    if final_chunk:
                        # Validate padding
                        padding = final_chunk[-1]
                        if padding > 16:
                            raise CryptoError("Invalid padding")
                        # Verify padding bytes are consistent
                        if not all(x == padding for x in final_chunk[-padding:]):
                            raise CryptoError("Inconsistent padding")
                        out_file.write(final_chunk[:-padding])

            return True

        except (IOError, InvalidKey) as e:
            self.logger.error(f"File decryption I/O error: {str(e)}")
            return False
        except CryptoError as e:
            self.logger.error(f"Decryption validation error: {str(e)}")
            return False
        except Exception as e:
            self.logger.exception("Unexpected error during file decryption")
            return False