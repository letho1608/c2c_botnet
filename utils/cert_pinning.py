import ssl
import socket
import logging
import hashlib
import OpenSSL
from typing import Dict, List, Optional, Set, Union
from dataclasses import dataclass
from datetime import datetime
import cryptography.x509 as x509
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.exceptions import InvalidSignature

@dataclass
class CertInfo:
    """Thông tin certificate"""
    subject: str
    issuer: str
    fingerprint: str
    public_key: str
    not_before: datetime
    not_after: datetime
    serial_number: str
    signature_algorithm: str

class CertificatePinning:
    def __init__(self):
        self.logger = logging.getLogger('security')
        self.pinned_certs: Dict[str, Set[str]] = {}
        self.cert_cache: Dict[str, CertInfo] = {}
        self.revoked_certs: Set[str] = set()
        
    def add_pin(self, hostname: str, cert_hash: str) -> bool:
        """Thêm pin cho một hostname

        Args:
            hostname: Hostname cần pin
            cert_hash: SHA256 hash của certificate
        """
        try:
            if hostname not in self.pinned_certs:
                self.pinned_certs[hostname] = set()
                
            self.pinned_certs[hostname].add(cert_hash)
            return True
            
        except Exception as e:
            self.logger.error(f"Error adding pin: {str(e)}")
            return False

    def remove_pin(self, hostname: str, cert_hash: str) -> bool:
        """Xóa pin cho một hostname

        Args:
            hostname: Hostname cần xóa pin
            cert_hash: Hash của certificate cần xóa
        """
        try:
            if hostname in self.pinned_certs:
                self.pinned_certs[hostname].discard(cert_hash)
                if not self.pinned_certs[hostname]:
                    del self.pinned_certs[hostname]
            return True
            
        except Exception as e:
            self.logger.error(f"Error removing pin: {str(e)}")
            return False

    def verify_cert(self, hostname: str, cert: Union[str, bytes],
                   check_revocation: bool = True) -> bool:
        """Kiểm tra certificate có hợp lệ không

        Args:
            hostname: Hostname cần verify
            cert: Certificate cần kiểm tra (PEM format)
            check_revocation: Có check revocation không
        """
        try:
            # Parse certificate
            if isinstance(cert, str):
                cert = cert.encode()
                
            x509_cert = x509.load_pem_x509_certificate(cert)
            
            # Calculate fingerprint
            fingerprint = self._get_cert_fingerprint(cert)
            
            # Check if pinned
            if hostname in self.pinned_certs:
                if fingerprint not in self.pinned_certs[hostname]:
                    self.logger.warning(f"Certificate not pinned for {hostname}")
                    return False
                    
            # Check if revoked
            if check_revocation and fingerprint in self.revoked_certs:
                self.logger.warning(f"Certificate revoked for {hostname}")
                return False
                
            # Verify dates
            now = datetime.utcnow()
            if now < x509_cert.not_valid_before or now > x509_cert.not_valid_after:
                self.logger.warning(f"Certificate expired for {hostname}")
                return False
                
            # Verify hostname
            self._verify_hostname(x509_cert, hostname)
            
            # Cache cert info
            self.cert_cache[fingerprint] = CertInfo(
                subject=self._get_subject_string(x509_cert),
                issuer=self._get_issuer_string(x509_cert),
                fingerprint=fingerprint,
                public_key=self._get_pubkey_string(x509_cert),
                not_before=x509_cert.not_valid_before,
                not_after=x509_cert.not_valid_after,
                serial_number=str(x509_cert.serial_number),
                signature_algorithm=x509_cert.signature_algorithm_oid._name
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Certificate verification error: {str(e)}")
            return False

    def verify_chain(self, cert_chain: List[bytes],
                    trusted_certs: Optional[List[bytes]] = None) -> bool:
        """Kiểm tra certificate chain có hợp lệ không

        Args:
            cert_chain: Danh sách các certificates trong chain
            trusted_certs: Danh sách trusted root certificates
        """
        try:
            # Build cert store
            store = OpenSSL.crypto.X509Store()
            
            # Add trusted certs
            if trusted_certs:
                for cert_data in trusted_certs:
                    cert = OpenSSL.crypto.load_certificate(
                        OpenSSL.crypto.FILETYPE_PEM,
                        cert_data
                    )
                    store.add_cert(cert)
                    
            # Convert chain to OpenSSL certs
            chain = [
                OpenSSL.crypto.load_certificate(
                    OpenSSL.crypto.FILETYPE_PEM,
                    cert_data
                )
                for cert_data in cert_chain
            ]
            
            # Create store context
            store_ctx = OpenSSL.crypto.X509StoreContext(store, chain[0], chain[1:])
            
            # Verify chain
            try:
                store_ctx.verify_certificate()
                return True
            except OpenSSL.crypto.X509StoreContextError:
                return False
                
        except Exception as e:
            self.logger.error(f"Chain verification error: {str(e)}")
            return False

    def revoke_cert(self, cert_hash: str) -> bool:
        """Thêm certificate vào revocation list

        Args:
            cert_hash: Hash của certificate cần revoke
        """
        try:
            self.revoked_certs.add(cert_hash)
            return True
            
        except Exception as e:
            self.logger.error(f"Error revoking certificate: {str(e)}")
            return False

    def wrap_socket(self, sock: socket.socket, hostname: str, **kwargs) -> ssl.SSLSocket:
        """Wrap socket với SSL và certificate pinning

        Args:
            sock: Socket cần wrap
            hostname: Hostname để verify certificate
        """
        try:
            # Create context
            context = ssl.create_default_context()
            
            # Set verify mode
            context.verify_mode = ssl.CERT_REQUIRED
            
            # Custom verify callback
            def verify_callback(conn, cert, errno, depth, result):
                if depth == 0:  # Leaf certificate
                    cert_data = OpenSSL.crypto.dump_certificate(
                        OpenSSL.crypto.FILETYPE_PEM,
                        cert
                    )
                    return self.verify_cert(hostname, cert_data)
                return True
                
            context._set_verify(
                ssl.CERT_REQUIRED,
                verify_callback
            )
            
            # Wrap socket
            return context.wrap_socket(
                sock,
                server_hostname=hostname,
                **kwargs
            )
            
        except Exception as e:
            self.logger.error(f"Error wrapping socket: {str(e)}")
            raise

    def get_cert_info(self, cert_hash: str) -> Optional[CertInfo]:
        """Lấy thông tin về một certificate

        Args:
            cert_hash: Hash của certificate
        """
        return self.cert_cache.get(cert_hash)

    def _get_cert_fingerprint(self, cert_data: bytes) -> str:
        """Tính fingerprint của certificate"""
        return hashlib.sha256(cert_data).hexdigest()

    def _get_subject_string(self, cert: x509.Certificate) -> str:
        """Convert subject name thành string"""
        return ','.join([
            f"{oid._name}={value}"
            for oid, value in cert.subject
        ])

    def _get_issuer_string(self, cert: x509.Certificate) -> str:
        """Convert issuer name thành string"""
        return ','.join([
            f"{oid._name}={value}"
            for oid, value in cert.issuer
        ])

    def _get_pubkey_string(self, cert: x509.Certificate) -> str:
        """Convert public key thành string"""
        return cert.public_key().public_bytes(
            encoding=x509.Encoding.PEM,
            format=x509.PublicFormat.SubjectPublicKeyInfo
        ).decode()

    def _verify_hostname(self, cert: x509.Certificate, hostname: str) -> bool:
        """Kiểm tra hostname có match với certificate không"""
        try:
            # Get subject alternative names
            san = cert.extensions.get_extension_for_oid(
                x509.oid.ExtensionOID.SUBJECT_ALTERNATIVE_NAME
            )
            names = san.value.get_values_for_type(x509.DNSName)
            
            # Check hostname against SAN
            if self._hostname_matches_san(hostname, names):
                return True
                
            # Check against common name as fallback
            common_names = cert.subject.get_attributes_for_oid(
                x509.oid.NameOID.COMMON_NAME
            )
            if common_names and self._hostname_matches_pattern(
                hostname,
                common_names[0].value
            ):
                return True
                
            return False
            
        except Exception as e:
            self.logger.error(f"Hostname verification error: {str(e)}")
            return False

    def _hostname_matches_san(self, hostname: str, san_patterns: List[str]) -> bool:
        """Kiểm tra hostname có match với SANs không"""
        return any(
            self._hostname_matches_pattern(hostname, pattern)
            for pattern in san_patterns
        )

    def _hostname_matches_pattern(self, hostname: str, pattern: str) -> bool:
        """Kiểm tra hostname có match với một pattern không"""
        if pattern.startswith('*.'):
            # Wildcard match
            suffix = pattern[2:]
            hostname_parts = hostname.split('.')
            if len(hostname_parts) >= 2:
                return hostname.endswith(suffix)
        return hostname.lower() == pattern.lower()