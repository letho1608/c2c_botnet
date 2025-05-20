from __future__ import annotations
import cv2
import numpy as np
import base64
import time
import threading
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path

class Webcam:
    def __init__(self, save_dir: str = "webcam") -> None:
        self.camera: Optional[cv2.VideoCapture] = None
        self.recording = False
        self.save_dir = Path(save_dir)
        self.logger = logging.getLogger(__name__)
        
        # Create save directory
        self.save_dir.mkdir(parents=True, exist_ok=True)
        
    def capture_image(self, device_index: int = 0) -> Optional[str]:
        """Chụp ảnh từ webcam

        Args:
            device_index (int, optional): Camera index. Defaults to 0.

        Returns:
            Optional[str]: Base64 encoded image data or None if failed
        """
        try:
            # Initialize camera
            self.camera = cv2.VideoCapture(device_index)
            if not self.camera.isOpened():
                raise Exception("Failed to open camera")
                
            # Read frame
            ret, frame = self.camera.read()
            if not ret:
                raise Exception("Failed to capture frame")
                
            # Create filename with timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = self.save_dir / f"capture_{timestamp}.jpg"
            
            # Save image
            cv2.imwrite(str(filename), frame)
            
            # Convert to base64
            with open(filename, 'rb') as f:
                image_data = f.read()
            encoded = base64.b64encode(image_data).decode()
            
            # Cleanup
            filename.unlink()
            self.camera.release()
            
            self.logger.info(f"Captured image from camera {device_index}")
            return encoded
            
        except Exception as e:
            self.logger.error(f"Error capturing image: {str(e)}")
            if self.camera:
                self.camera.release()
            return None
            
    def start_recording(self, device_index: int = 0, duration: int = 30) -> bool:
        """Bắt đầu quay video

        Args:
            device_index (int, optional): Camera index. Defaults to 0.
            duration (int, optional): Recording duration in seconds. Defaults to 30.

        Returns:
            bool: True if recording started successfully
        """
        if self.recording:
            return False
            
        try:
            # Initialize camera
            self.camera = cv2.VideoCapture(device_index)
            if not self.camera.isOpened():
                raise Exception("Failed to open camera")
                
            # Create filename with timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = self.save_dir / f"video_{timestamp}.avi"
            
            # Initialize video writer
            fourcc = cv2.VideoWriter_fourcc(*'XVID')
            out = cv2.VideoWriter(
                str(filename),
                fourcc,
                20.0,  # FPS
                (640,480)  # Resolution
            )
            
            self.recording = True
            start_time = time.time()
            
            # Recording thread
            def record() -> Optional[str]:
                try:
                    while self.recording and (time.time() - start_time) < duration:
                        ret, frame = self.camera.read()
                        if ret:
                            out.write(frame)
                            
                    # Cleanup
                    self.recording = False
                    self.camera.release()
                    out.release()
                    
                    # Convert to base64
                    with open(filename, 'rb') as f:
                        video_data = f.read()
                    encoded = base64.b64encode(video_data).decode()
                    
                    # Delete temp file
                    filename.unlink()
                    
                    self.logger.info(f"Completed {duration}s recording from camera {device_index}")
                    return encoded
                    
                except Exception as e:
                    self.logger.error(f"Recording error: {str(e)}")
                    self.recording = False
                    if self.camera:
                        self.camera.release()
                    if out:
                        out.release()
                    return None
                    
            # Start recording thread
            thread = threading.Thread(target=record)
            thread.daemon = True
            thread.start()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error starting recording: {str(e)}")
            self.recording = False
            if self.camera:
                self.camera.release()
            return False
            
    def stop_recording(self) -> bool:
        """Dừng quay video

        Returns:
            bool: True if stopped successfully
        """
        if not self.recording:
            return False
            
        try:
            self.recording = False
            if self.camera:
                self.camera.release()
            self.logger.info("Recording stopped")
            return True
            
        except Exception as e:
            self.logger.error(f"Error stopping recording: {str(e)}")
            return False
            
    def list_cameras(self) -> List[int]:
        """Liệt kê các camera có sẵn

        Returns:
            List[int]: List of available camera indices
        """
        cameras = []
        try:
            for i in range(10):
                cap = cv2.VideoCapture(i)
                if cap.read()[0]:
                    cameras.append(i)
                cap.release()
                
            return cameras
            
        except Exception as e:
            self.logger.error(f"Error listing cameras: {str(e)}")
            return []
            
    def get_camera_info(self, device_index: int = 0) -> Optional[Dict[str, Any]]:
        """Lấy thông tin camera

        Args:
            device_index (int, optional): Camera index. Defaults to 0.

        Returns:
            Optional[Dict[str, Any]]: Camera properties or None if failed
        """
        try:
            cap = cv2.VideoCapture(device_index)
            if not cap.isOpened():
                return None
                
            info = {
                'width': int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                'height': int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
                'fps': cap.get(cv2.CAP_PROP_FPS),
                'brightness': cap.get(cv2.CAP_PROP_BRIGHTNESS),
                'contrast': cap.get(cv2.CAP_PROP_CONTRAST),
                'saturation': cap.get(cv2.CAP_PROP_SATURATION),
                'hue': cap.get(cv2.CAP_PROP_HUE),
                'gain': cap.get(cv2.CAP_PROP_GAIN),
                'exposure': cap.get(cv2.CAP_PROP_EXPOSURE)
            }
            
            cap.release()
            return info
            
        except Exception as e:
            self.logger.error(f"Error getting camera info: {str(e)}")
            if 'cap' in locals() and cap:
                cap.release()
            return None
            
    def cleanup_old_files(self, max_age_hours: int = 24) -> bool:
        """Xóa file cũ

        Args:
            max_age_hours (int, optional): Maximum age in hours. Defaults to 24.

        Returns:
            bool: True if cleanup successful
        """
        try:
            current_time = datetime.now()
            
            for file in self.save_dir.glob('*.*'):
                file_time = datetime.fromtimestamp(file.stat().st_mtime)
                age_hours = (current_time - file_time).total_seconds() / 3600
                
                if age_hours > max_age_hours:
                    file.unlink()
                    self.logger.info(f"Deleted old file: {file.name}")
                    
            return True
            
        except Exception as e:
            self.logger.error(f"Error cleaning up files: {str(e)}")
            return False
            
    def check_camera(self, device_index: int = 0) -> bool:
        """Kiểm tra camera có sẵn và hoạt động

        Args:
            device_index (int, optional): Camera index. Defaults to 0.

        Returns:
            bool: True if camera is available and working
        """
        try:
            cap = cv2.VideoCapture(device_index)
            if not cap.isOpened():
                return False
                
            ret = cap.read()[0]
            cap.release()
            
            return ret
            
        except Exception:
            return False