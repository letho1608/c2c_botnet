from __future__ import annotations
import os
import time
import base64
import logging
import threading
from datetime import datetime
from typing import Dict, List, Optional, Any, Union, Tuple
from pathlib import Path
import PIL.ImageGrab
import cv2
import numpy as np

class Screenshot:
    def __init__(self, save_dir: str = "screenshots") -> None:
        """Initialize screenshot module

        Args:
            save_dir (str, optional): Directory to save screenshots. Defaults to "screenshots".
        """
        self.save_dir = Path(save_dir)
        self.logger = logging.getLogger(__name__)
        self.lock = threading.Lock()
        self.screenshot_count = 0
        self.max_retries = 3
        
        # Create save directory
        self.save_dir.mkdir(parents=True, exist_ok=True)
        
    def capture(self) -> Optional[str]:
        """Take screenshot of full screen

        Returns:
            Optional[str]: Path to saved screenshot or None if failed
        """
        try:
            # Take screenshot
            with self.lock:
                image = PIL.ImageGrab.grab()
                
                if not image:
                    raise Exception("Failed to capture screen")
                    
                # Create filename with timestamp
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = self.save_dir / f"screenshot_{timestamp}.png"
                
                # Save image
                image.save(str(filename), 'PNG')
                
                self.logger.info(f"Screenshot saved to {filename}")
                return str(filename)
                
        except Exception as e:
            self.logger.error(f"Error capturing screenshot: {str(e)}")
            return None
            
        finally:
            # Cleanup
            if 'image' in locals():
                image.close()
                
    def capture_to_base64(self) -> Optional[str]:
        """Take screenshot and convert to base64

        Returns:
            Optional[str]: Base64 encoded image data or None if failed
        """
        try:
            filename = self.capture()
            if not filename:
                return None
                
            # Read and convert to base64
            with open(filename, 'rb') as f:
                image_data = f.read()
                base64_data = base64.b64encode(image_data).decode()
                
            # Clean up temp file
            Path(filename).unlink()
            
            return base64_data
            
        except Exception as e:
            self.logger.error(f"Error converting to base64: {str(e)}")
            return None
            
    def capture_monitor(self, monitor_index: int = 0) -> Optional[str]:
        """Take screenshot of specific monitor

        Args:
            monitor_index (int, optional): Monitor index. Defaults to 0.

        Returns:
            Optional[str]: Path to saved screenshot or None if failed
        """
        try:
            # Get monitor info
            monitors = self._get_monitor_info()
            
            if monitor_index >= len(monitors):
                raise ValueError(f"Invalid monitor index: {monitor_index}")
                
            monitor = monitors[monitor_index]
            
            # Take screenshot
            with self.lock:
                image = PIL.ImageGrab.grab(
                    bbox=(
                        monitor['left'],
                        monitor['top'],
                        monitor['left'] + monitor['width'],
                        monitor['top'] + monitor['height']
                    )
                )
                
                if not image:
                    raise Exception("Failed to capture monitor")
                    
                # Create filename
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = self.save_dir / f"monitor{monitor_index}_{timestamp}.png"
                
                # Save image
                image.save(str(filename), 'PNG')
                
                self.logger.info(f"Monitor screenshot saved to {filename}")
                return str(filename)
                
        except Exception as e:
            self.logger.error(f"Error capturing monitor {monitor_index}: {str(e)}")
            return None
            
        finally:
            # Cleanup
            if 'image' in locals():
                image.close()
                
    def capture_window(self, window_title: str) -> Optional[str]:
        """Take screenshot of specific window

        Args:
            window_title (str): Window title to capture

        Returns:
            Optional[str]: Path to saved screenshot or None if failed
        """
        try:
            # Find window
            import win32gui
            hwnd = win32gui.FindWindow(None, window_title)
            
            if not hwnd:
                raise Exception(f"Window not found: {window_title}")
                
            # Get window rect
            rect = win32gui.GetWindowRect(hwnd)
            
            # Take screenshot
            with self.lock:
                image = PIL.ImageGrab.grab(bbox=rect)
                
                if not image:
                    raise Exception("Failed to capture window")
                    
                # Create filename
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = self.save_dir / f"window_{timestamp}.png"
                
                # Save image
                image.save(str(filename), 'PNG')
                
                self.logger.info(f"Window screenshot saved to {filename}")
                return str(filename)
                
        except Exception as e:
            self.logger.error(f"Error capturing window: {str(e)}")
            return None
            
        finally:
            # Cleanup
            if 'image' in locals():
                image.close()
                
    def capture_region(self, left: int, top: int, width: int, height: int) -> Optional[str]:
        """Take screenshot of specific region

        Args:
            left (int): Left coordinate
            top (int): Top coordinate
            width (int): Region width
            height (int): Region height

        Returns:
            Optional[str]: Path to saved screenshot or None if failed
        """
        try:
            # Validate coordinates
            if width <= 0 or height <= 0:
                raise ValueError("Invalid region dimensions")
                
            # Take screenshot
            with self.lock:
                image = PIL.ImageGrab.grab(
                    bbox=(left, top, left + width, top + height)
                )
                
                if not image:
                    raise Exception("Failed to capture region")
                    
                # Create filename
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = self.save_dir / f"region_{timestamp}.png"
                
                # Save image
                image.save(str(filename), 'PNG')
                
                self.logger.info(f"Region screenshot saved to {filename}")
                return str(filename)
                
        except Exception as e:
            self.logger.error(f"Error capturing region: {str(e)}")
            return None
            
        finally:
            # Cleanup
            if 'image' in locals():
                image.close()
                
    def start_capture_sequence(self, interval: float = 1.0, duration: float = 0) -> None:
        """Start taking periodic screenshots

        Args:
            interval (float, optional): Interval between captures in seconds. Defaults to 1.0.
            duration (float, optional): Total duration in seconds, 0 for infinite. Defaults to 0.
        """
        try:
            def capture_loop() -> None:
                start_time = time.time()
                while True:
                    try:
                        self.capture()
                        time.sleep(interval)
                        
                        if duration > 0 and (time.time() - start_time) >= duration:
                            break
                            
                    except Exception as e:
                        self.logger.error(f"Capture sequence error: {str(e)}")
                        
            thread = threading.Thread(target=capture_loop)
            thread.daemon = True
            thread.start()
            
            self.logger.info(f"Started capture sequence: interval={interval}s duration={duration}s")
            
        except Exception as e:
            self.logger.error(f"Error starting capture sequence: {str(e)}")
            
    def cleanup_old_screenshots(self, max_age_hours: int = 24) -> None:
        """Delete old screenshot files

        Args:
            max_age_hours (int, optional): Maximum age in hours. Defaults to 24.
        """
        try:
            current_time = datetime.now()
            
            with self.lock:
                for file in self.save_dir.glob('*.png'):
                    try:
                        file_time = datetime.fromtimestamp(file.stat().st_mtime)
                        age_hours = (current_time - file_time).total_seconds() / 3600
                        
                        if age_hours > max_age_hours:
                            file.unlink()
                            self.logger.info(f"Deleted old screenshot: {file.name}")
                            
                    except Exception as e:
                        self.logger.error(f"Error cleaning up file {file}: {str(e)}")
                        
        except Exception as e:
            self.logger.error(f"Error cleaning up screenshots: {str(e)}")
            
    def _get_monitor_info(self) -> List[Dict[str, int]]:
        """Get information about monitors

        Returns:
            List[Dict[str, int]]: List of monitor information
        """
        try:
            import win32api
            
            monitors = []
            for i, monitor in enumerate(win32api.EnumDisplayMonitors()):
                info = win32api.GetMonitorInfo(monitor[0])
                monitors.append({
                    'index': i,
                    'left': info['Monitor'][0],
                    'top': info['Monitor'][1],
                    'width': info['Monitor'][2] - info['Monitor'][0],
                    'height': info['Monitor'][3] - info['Monitor'][1],
                    'is_primary': info['Flags'] == 1
                })
            return monitors
            
        except Exception as e:
            self.logger.error(f"Error getting monitor info: {str(e)}")
            return []