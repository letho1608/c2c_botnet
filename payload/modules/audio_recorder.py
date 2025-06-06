#!/usr/bin/env python3
"""
Audio Recording Module
Ported from control_computer/bot.py - removed Telegram dependencies
"""

import sounddevice as sd
import wavio
import numpy as np
import threading
import time
import os
import tempfile
import logging
from typing import Optional, Callable, Dict, Any, List
from base64 import b64encode
import json


class AudioRecorder:
    """Advanced audio recording with multiple format support"""
    
    def __init__(self, 
                 sample_rate: int = 44100,
                 channels: int = 2,
                 format: str = 'wav',
                 callback: Optional[Callable] = None):
        """
        Initialize audio recorder
        
        Args:
            sample_rate (int): Audio sample rate (8000, 16000, 22050, 44100, 48000)
            channels (int): Number of channels (1=mono, 2=stereo)
            format (str): Output format ('wav', 'flac', 'mp3')
            callback (Callable): Callback function to send audio data
        """
        self.sample_rate = sample_rate
        self.channels = channels
        self.format = format
        self.callback = callback
        
        self.is_recording = False
        self.recording_thread = None
        self.current_recording = None
        self.start_time = None
        
        self.logger = logging.getLogger(__name__)
        
        # Validate sample rate
        valid_rates = [8000, 16000, 22050, 44100, 48000]
        if sample_rate not in valid_rates:
            self.logger.warning(f"Invalid sample rate {sample_rate}, using 44100")
            self.sample_rate = 44100
            
        # Audio statistics
        self.stats = {
            'recordings_made': 0,
            'total_duration': 0,
            'total_size_bytes': 0,
            'average_duration': 0,
            'last_recording_size': 0
        }
        
        # Get available audio devices
        self.devices = self._get_audio_devices()
        self.selected_device = None
        
    def _get_audio_devices(self) -> List[Dict[str, Any]]:
        """Get list of available audio input devices"""
        try:
            devices = []
            device_list = sd.query_devices()
            
            for i, device in enumerate(device_list):
                if device['max_input_channels'] > 0:  # Input device
                    devices.append({
                        'id': i,
                        'name': device['name'],
                        'channels': device['max_input_channels'],
                        'sample_rate': device['default_samplerate'],
                        'is_default': i == sd.default.device[0]
                    })
                    
            return devices
            
        except Exception as e:
            self.logger.error(f"Error getting audio devices: {e}")
            return []
            
    def get_devices(self) -> List[Dict[str, Any]]:
        """Get available audio input devices"""
        return self.devices
        
    def set_device(self, device_id: Optional[int]) -> bool:
        """Set audio input device"""
        try:
            if device_id is None:
                self.selected_device = None
                return True
                
            # Check if device exists
            device_list = sd.query_devices()
            if 0 <= device_id < len(device_list):
                device = device_list[device_id]
                if device['max_input_channels'] > 0:
                    self.selected_device = device_id
                    self.logger.info(f"Selected audio device: {device['name']}")
                    return True
                    
            self.logger.error(f"Invalid audio device ID: {device_id}")
            return False
            
        except Exception as e:
            self.logger.error(f"Error setting audio device: {e}")
            return False
            
    def record_duration(self, duration: float) -> Dict[str, Any]:
        """Record audio for specified duration"""
        try:
            if self.is_recording:
                return {
                    'success': False,
                    'message': 'Recording already in progress'
                }
                
            self.logger.info(f"Recording audio for {duration} seconds...")
            
            # Record audio
            recording = sd.rec(
                int(duration * self.sample_rate),
                samplerate=self.sample_rate,
                channels=self.channels,
                device=self.selected_device,
                dtype='float64'
            )
            
            # Wait for recording to complete
            sd.wait()
            
            # Save to temporary file
            temp_path = self._save_recording(recording)
            
            if temp_path:
                # Read file for callback/return
                file_size = os.path.getsize(temp_path)
                
                # Update statistics
                self.stats['recordings_made'] += 1
                self.stats['total_duration'] += duration
                self.stats['total_size_bytes'] += file_size
                self.stats['last_recording_size'] = file_size
                self.stats['average_duration'] = self.stats['total_duration'] / self.stats['recordings_made']
                
                # Prepare result
                result = {
                    'success': True,
                    'message': f'Recorded {duration} seconds',
                    'file_path': temp_path,
                    'duration': duration,
                    'size_bytes': file_size,
                    'sample_rate': self.sample_rate,
                    'channels': self.channels,
                    'format': self.format
                }
                
                # Send via callback if provided
                if self.callback:
                    with open(temp_path, 'rb') as f:
                        audio_data = f.read()
                        
                    callback_data = {
                        'type': 'audio_recording',
                        'timestamp': time.time(),
                        'duration': duration,
                        'size': file_size,
                        'sample_rate': self.sample_rate,
                        'channels': self.channels,
                        'format': self.format,
                        'data': b64encode(audio_data).decode('utf-8')
                    }
                    
                    self.callback(callback_data)
                    
                return result
                
            else:
                return {
                    'success': False,
                    'message': 'Failed to save recording'
                }
                
        except Exception as e:
            self.logger.error(f"Error recording audio: {e}")
            return {
                'success': False,
                'message': f'Recording error: {str(e)}'
            }
            
    def start_continuous_recording(self) -> Dict[str, Any]:
        """Start continuous recording in background"""
        try:
            if self.is_recording:
                return {
                    'success': False,
                    'message': 'Recording already in progress'
                }
                
            self.is_recording = True
            self.start_time = time.time()
            
            self.recording_thread = threading.Thread(
                target=self._continuous_recording_loop,
                daemon=True
            )
            self.recording_thread.start()
            
            self.logger.info("Started continuous audio recording")
            return {
                'success': True,
                'message': 'Continuous recording started',
                'sample_rate': self.sample_rate,
                'channels': self.channels
            }
            
        except Exception as e:
            self.logger.error(f"Error starting continuous recording: {e}")
            return {
                'success': False,
                'message': f'Error: {str(e)}'
            }
            
    def stop_continuous_recording(self) -> Dict[str, Any]:
        """Stop continuous recording"""
        try:
            if not self.is_recording:
                return {
                    'success': False,
                    'message': 'No recording in progress'
                }
                
            self.is_recording = False
            
            if self.recording_thread and self.recording_thread.is_alive():
                self.recording_thread.join(timeout=3)
                
            duration = time.time() - self.start_time if self.start_time else 0
            
            self.logger.info(f"Stopped continuous recording after {duration:.1f} seconds")
            return {
                'success': True,
                'message': f'Continuous recording stopped after {duration:.1f} seconds',
                'total_duration': duration,
                'stats': self.stats.copy()
            }
            
        except Exception as e:
            self.logger.error(f"Error stopping continuous recording: {e}")
            return {
                'success': False,
                'message': f'Error: {str(e)}'
            }
            
    def _continuous_recording_loop(self) -> None:
        """Continuous recording loop with chunks"""
        chunk_duration = 10  # Record in 10-second chunks
        
        while self.is_recording:
            try:
                # Record chunk
                recording = sd.rec(
                    int(chunk_duration * self.sample_rate),
                    samplerate=self.sample_rate,
                    channels=self.channels,
                    device=self.selected_device,
                    dtype='float64'
                )
                
                # Wait for chunk to complete
                sd.wait()
                
                if self.is_recording:  # Check if still recording
                    # Save chunk
                    temp_path = self._save_recording(recording, f"chunk_{int(time.time())}")
                    
                    if temp_path and self.callback:
                        # Send chunk via callback
                        with open(temp_path, 'rb') as f:
                            audio_data = f.read()
                            
                        callback_data = {
                            'type': 'audio_chunk',
                            'timestamp': time.time(),
                            'duration': chunk_duration,
                            'size': len(audio_data),
                            'sample_rate': self.sample_rate,
                            'channels': self.channels,
                            'format': self.format,
                            'data': b64encode(audio_data).decode('utf-8')
                        }
                        
                        self.callback(callback_data)
                        
                        # Clean up chunk file
                        try:
                            os.remove(temp_path)
                        except:
                            pass
                            
            except Exception as e:
                self.logger.error(f"Error in continuous recording loop: {e}")
                time.sleep(1)  # Prevent rapid error loop
                
    def _save_recording(self, recording: np.ndarray, filename_prefix: str = "recording") -> Optional[str]:
        """Save recording to temporary file"""
        try:
            # Create temporary file
            temp_dir = tempfile.gettempdir()
            timestamp = int(time.time())
            filename = f"{filename_prefix}_{timestamp}.{self.format}"
            temp_path = os.path.join(temp_dir, filename)
            
            # Save based on format
            if self.format.lower() == 'wav':
                wavio.write(temp_path, recording, self.sample_rate, sampwidth=2)
            else:
                # For other formats, save as WAV (can be extended)
                temp_path = temp_path.replace(f'.{self.format}', '.wav')
                wavio.write(temp_path, recording, self.sample_rate, sampwidth=2)
                
            self.logger.debug(f"Saved recording to: {temp_path}")
            return temp_path
            
        except Exception as e:
            self.logger.error(f"Error saving recording: {e}")
            return None
            
    def get_stats(self) -> Dict[str, Any]:
        """Get recording statistics"""
        stats = self.stats.copy()
        stats.update({
            'is_recording': self.is_recording,
            'current_device': self.selected_device,
            'sample_rate': self.sample_rate,
            'channels': self.channels,
            'format': self.format
        })
        
        if self.is_recording and self.start_time:
            stats['current_duration'] = time.time() - self.start_time
            
        return stats
        
    def test_audio_device(self, device_id: Optional[int] = None) -> Dict[str, Any]:
        """Test audio device by recording a short sample"""
        try:
            test_duration = 1.0  # 1 second test
            
            # Record test sample
            recording = sd.rec(
                int(test_duration * self.sample_rate),
                samplerate=self.sample_rate,
                channels=self.channels,
                device=device_id or self.selected_device,
                dtype='float64'
            )
            
            sd.wait()
            
            # Analyze recording
            max_amplitude = np.max(np.abs(recording))
            rms_level = np.sqrt(np.mean(recording**2))
            
            return {
                'success': True,
                'message': 'Audio device test successful',
                'max_amplitude': float(max_amplitude),
                'rms_level': float(rms_level),
                'has_signal': max_amplitude > 0.01,  # Threshold for signal detection
                'test_duration': test_duration
            }
            
        except Exception as e:
            self.logger.error(f"Error testing audio device: {e}")
            return {
                'success': False,
                'message': f'Device test failed: {str(e)}'
            }


class AudioManager:
    """Manager for audio recording operations"""
    
    def __init__(self, send_callback: Optional[Callable] = None):
        """
        Initialize audio manager
        
        Args:
            send_callback: Function to send data to server/client
        """
        self.send_callback = send_callback
        self.recorder = None
        self.logger = logging.getLogger(__name__)
        
    def initialize_recorder(self, 
                           sample_rate: int = 44100,
                           channels: int = 2,
                           format: str = 'wav') -> Dict[str, Any]:
        """Initialize audio recorder with settings"""
        try:
            self.recorder = AudioRecorder(
                sample_rate=sample_rate,
                channels=channels,
                format=format,
                callback=self._audio_callback
            )
            
            devices = self.recorder.get_devices()
            
            return {
                'success': True,
                'message': 'Audio recorder initialized',
                'settings': {
                    'sample_rate': sample_rate,
                    'channels': channels,
                    'format': format
                },
                'available_devices': devices
            }
            
        except Exception as e:
            self.logger.error(f"Error initializing recorder: {e}")
            return {
                'success': False,
                'message': f'Initialization error: {str(e)}'
            }
            
    def record_duration(self, duration: float) -> Dict[str, Any]:
        """Record audio for specified duration"""
        if not self.recorder:
            return {
                'success': False,
                'message': 'Recorder not initialized'
            }
            
        return self.recorder.record_duration(duration)
        
    def start_continuous(self) -> Dict[str, Any]:
        """Start continuous recording"""
        if not self.recorder:
            return {
                'success': False,
                'message': 'Recorder not initialized'
            }
            
        return self.recorder.start_continuous_recording()
        
    def stop_continuous(self) -> Dict[str, Any]:
        """Stop continuous recording"""
        if not self.recorder:
            return {
                'success': False,
                'message': 'Recorder not initialized'
            }
            
        return self.recorder.stop_continuous_recording()
        
    def set_device(self, device_id: Optional[int]) -> Dict[str, Any]:
        """Set audio input device"""
        if not self.recorder:
            return {
                'success': False,
                'message': 'Recorder not initialized'
            }
            
        success = self.recorder.set_device(device_id)
        return {
            'success': success,
            'message': f'Device set to {device_id}' if success else 'Failed to set device'
        }
        
    def get_status(self) -> Dict[str, Any]:
        """Get audio recording status"""
        if not self.recorder:
            return {
                'initialized': False,
                'message': 'Recorder not initialized'
            }
            
        return {
            'initialized': True,
            'stats': self.recorder.get_stats(),
            'devices': self.recorder.get_devices()
        }
        
    def test_device(self, device_id: Optional[int] = None) -> Dict[str, Any]:
        """Test audio device"""
        if not self.recorder:
            return {
                'success': False,
                'message': 'Recorder not initialized'
            }
            
        return self.recorder.test_audio_device(device_id)
        
    def _audio_callback(self, audio_data: Dict[str, Any]) -> None:
        """Callback to handle recorded audio"""
        try:
            if self.send_callback:
                self.send_callback(audio_data)
            else:
                self.logger.debug(f"Audio {audio_data['type']}: {audio_data['size']} bytes, "
                                f"{audio_data['duration']}s")
                                
        except Exception as e:
            self.logger.error(f"Error in audio callback: {e}")


# Example integration with C2C server
def integrate_with_c2c_server():
    """Example of how to integrate with C2C server"""
    
    def send_to_client(data):
        """Send data to connected client"""
        print(f"Sending audio: {len(data['data'])} bytes, {data['duration']}s")
        
    # Create audio manager
    audio_manager = AudioManager(send_callback=send_to_client)
    
    # Commands that can be called from server
    def handle_audio_command(command: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Handle audio commands from C2C server"""
        params = params or {}
        
        if command == 'init':
            return audio_manager.initialize_recorder(
                sample_rate=params.get('sample_rate', 44100),
                channels=params.get('channels', 2),
                format=params.get('format', 'wav')
            )
            
        elif command == 'record':
            duration = params.get('duration', 10)
            return audio_manager.record_duration(duration)
            
        elif command == 'start_continuous':
            return audio_manager.start_continuous()
            
        elif command == 'stop_continuous':
            return audio_manager.stop_continuous()
            
        elif command == 'set_device':
            return audio_manager.set_device(params.get('device_id'))
            
        elif command == 'test_device':
            return audio_manager.test_device(params.get('device_id'))
            
        elif command == 'get_status':
            return audio_manager.get_status()
            
        else:
            return {
                'success': False,
                'message': f'Unknown command: {command}'
            }
    
    return handle_audio_command


if __name__ == "__main__":
    # Test the audio module
    def test_callback(audio_data):
        print(f"Audio {audio_data['type']}: {audio_data['size']} bytes, "
              f"{audio_data['duration']}s, {audio_data['sample_rate']}Hz")
    
    # Create and test recorder
    recorder = AudioRecorder(callback=test_callback)
    
    print("Available audio devices:")
    for device in recorder.get_devices():
        print(f"  {device['id']}: {device['name']} ({'Default' if device['is_default'] else 'Available'})")
    
    print("\nTesting device...")
    test_result = recorder.test_audio_device()
    print(f"Test result: {test_result}")
    
    if test_result['success'] and test_result['has_signal']:
        print("\nRecording 3 seconds...")
        result = recorder.record_duration(3.0)
        print(f"Recording result: {result}")
    else:
        print("No audio signal detected or device test failed")