#!/usr/bin/env python3


import shutil
import threading
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
from concurrent.futures import ThreadPoolExecutor
from config.config_manager import BackupConfig
from .logger import Logger


class BackupManager:

    def __init__( self, config: BackupConfig, vault_path: Path, logger: Logger ):
        
        self.config = config
        self.vault_path = vault_path
        self.logger = logger
        
        self._backup_lock = threading.Lock()
        self._backup_in_progress = False
        
        self._backup_count = 0
        self._last_backup_time: Optional[float] = None
        self._last_backup_size: Optional[int] = None
        
        if self.config.enabled:
            
            self.config.directory.mkdir(parents=True, exist_ok=True)
            self.logger.debug(f"[+] Backup manager initialized - directory: {self.config.directory}")
            
        else:
            
            self.logger.debug("[+] Backup manager initialized - backups disabled")
    

    def create_backup( self ) -> bool:
        
        if not self.config.enabled:
            self.logger.debug("[*] Backups disabled - skipping")
            return True
        
        # Check if backup is already in progress
        if self._backup_in_progress:
            self.logger.warning("[!] Backup already in progress")
            return False
        
        with self._backup_lock:
            
            if self._backup_in_progress:
                return False
                
            self._backup_in_progress = True
        
        try:
            
            if not self.vault_path.exists():
                self.logger.error(f"[x] Vault path does not exist: {self.vault_path}")
                return False
            
            # Ensure backup directory exists
            self.config.directory.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = self.config.directory / f"vault_backup_{timestamp}"
            
            self.logger.info(f"[+] Creating backup: {backup_path.name}")
            
            source_size = self._calculate_directory_size(self.vault_path)
            self.logger.debug(f"[+] Source size: {source_size / 1024 / 1024:.1f} MB")
            
            ignore_patterns = self._get_ignore_patterns()
            
            shutil.copytree(
                
                self.vault_path,
                backup_path,
                ignore=shutil.ignore_patterns(*ignore_patterns),
                copy_function=shutil.copy2,  # Preserve metadata
                ignore_dangling_symlinks=True
            )
            
            if not self._verify_backup(backup_path):
                
                self.logger.error("[x] Backup verification failed")
                
                if backup_path.exists():
                    shutil.rmtree(backup_path, ignore_errors=True)
                    
                return False
            
            backup_size = self._calculate_directory_size(backup_path)
            self._last_backup_time = datetime.now().timestamp()
            self._last_backup_size = backup_size
            self._backup_count += 1
            
            self.logger.info(f"[+] Backup created successfully: {backup_path.name}")
            self.logger.debug(f"[+] Backup size: {backup_size / 1024 / 1024:.1f} MB")
            
            self._cleanup_old_backups()
            
            return True
            
        except PermissionError as e:
            
            self.logger.error(f"[x] Backup failed - permission denied: {e}")
            return False
            
        except OSError as e:
            
            self.logger.error(f"[x] Backup failed - OS error: {e}")
            return False
            
        except Exception as e:
            
            self.logger.error(f"[x] Backup failed - unexpected error: {e}")
            return False
            
        finally:
            
            with self._backup_lock:
                self._backup_in_progress = False


    def create_backup_async( self ) -> bool:

        # Create backup asynchronously using ThreadPoolExecutor
        
        if not self.config.enabled:
            return True
            
        try:
            
            with ThreadPoolExecutor(max_workers=1) as executor:
                
                future = executor.submit(self.create_backup)
                return future.result(timeout=300)  # 5 minute timeout
                
        except Exception as e:
            
            self.logger.error(f"[x] Async backup failed: {e}")
            return False


    def _get_ignore_patterns( self ) -> List[str]:
        
        
        return [
            
            # Git and VCS
            '.git*',
            '.svn',
            '.hg',
            
            # System files
            '.DS_Store',
            'Thumbs.db',
            'desktop.ini',
            
            # Temporary files
            '*.tmp',
            '*.temp',
            '*.lock',
            '*.swp',
            '*~',
            
            
            # Large media files (optional - might want to backup these)
            # '*.mp4',
            # '*.avi',
            # '*.mov',
            
            # Trash folders
            '.trash',
            '.Trash',
            'Trash'
        ]


    def _calculate_directory_size( self, directory: Path ) -> int:
                
        try:
            
            total_size = 0
            
            for file_path in directory.rglob('*'):
                
                if file_path.is_file():
                    
                    try:
                        total_size += file_path.stat().st_size
                    except (OSError, PermissionError):

                        continue
            
            return total_size
            
        except Exception as e:
            
            self.logger.warning(f"[!] Could not calculate directory size: {e}")
            return 0


    def _verify_backup( self, backup_path: Path ) -> bool:
                
        try:
            
            if not backup_path.exists() or not backup_path.is_dir():
                return False
            
            file_count = sum(1 for _ in backup_path.rglob('*') if _.is_file())
            
            if file_count == 0:
                self.logger.warning("[!] Backup appears to be empty")
                return False
            
            self.logger.debug(f"[+] Backup verification passed - {file_count} files")
            return True
            
        except Exception as e:
            
            self.logger.error(f"[x] Backup verification error: {e}")
            return False


    def _cleanup_old_backups( self ) -> None:
        
        # Remove old backups exceeding max_backups 

        try:
            
            # Get all backup directories
            backups = []
            
            for item in self.config.directory.iterdir():
                
                if item.is_dir() and item.name.startswith('vault_backup_'):
                    
                    try:
                        
                        timestamp_str = item.name.replace('vault_backup_', '')
                        timestamp = datetime.strptime(timestamp_str, '%Y%m%d_%H%M%S')
                        backups.append((timestamp, item))
                        
                    except ValueError:
                        
                        self.logger.warning(f"[!] Skipping backup with invalid format: {item.name}")
                        continue
            
            # Sort by timestamp (oldest first)
            backups.sort(key=lambda x: x[0])
            
            while len(backups) > self.config.max_backups:
                
                oldest_timestamp, oldest_path = backups.pop(0)
                
                try:
                    
                    shutil.rmtree(oldest_path, ignore_errors=True)
                    self.logger.info(f"[+] Removed old backup: {oldest_path.name}")
                    
                except Exception as e:
                    
                    self.logger.warning(f"[!] Could not remove old backup {oldest_path.name}: {e}")
                    
        except Exception as e:
            
            self.logger.warning(f"[!] Cleanup error: {e}")


    def list_backups( self ) -> List[Dict[str, Any]]:
        
        # List available backups with details
        
        if not self.config.enabled or not self.config.directory.exists():
            return []
        
        backups = []
        
        try:
            
            for item in self.config.directory.iterdir():
                
                if item.is_dir() and item.name.startswith('vault_backup_'):
                    
                    try:
                        
                        # Extract timestamp
                        timestamp_str = item.name.replace('vault_backup_', '')
                        timestamp = datetime.strptime(timestamp_str, '%Y%m%d_%H%M%S')
                        
                        # Get size
                        size = self._calculate_directory_size(item)
                        
                        backups.append({
                            
                            'name': item.name,
                            'path': item,
                            'timestamp': timestamp,
                            'size_bytes': size,
                            'size_mb': size / 1024 / 1024
                        })
                        
                    except (ValueError, OSError) as e:
                        
                        self.logger.warning(f"[!] Error processing backup {item.name}: {e}")
                        continue
            
            # Sort by timestamp (newest first)
            backups.sort(key=lambda x: x['timestamp'], reverse=True)
            
        except Exception as e:
            
            self.logger.error(f"[x] Error listing backups: {e}")
        
        return backups


    def restore_backup( self, backup_name: str, target_path: Optional[Path] = None ) -> bool:

        
        if not self.config.enabled:
            self.logger.error("[x] Backups are disabled")
            return False
        
        backup_path = self.config.directory / backup_name
        
        if not backup_path.exists():
            self.logger.error(f"[x] Backup not found: {backup_name}")
            return False
        
        restore_target = target_path or self.vault_path
        
        try:
            
            self.logger.info(f"[+] Restoring backup {backup_name} to {restore_target}")
            
            restore_target.parent.mkdir(parents=True, exist_ok=True)
            
            if restore_target.exists():
                shutil.rmtree(restore_target)
            
            shutil.copytree(backup_path, restore_target)
            
            self.logger.info(f"[+] Backup restored successfully to {restore_target}")
            return True
            
        except Exception as e:
            
            self.logger.error(f"[x] Backup restore failed: {e}")
            return False


    def delete_backup( self, backup_name: str ) -> bool:

        # Delete a specific backup 
        
        backup_path = self.config.directory / backup_name
        
        if not backup_path.exists():
            self.logger.error(f"[x] Backup not found: {backup_name}")
            return False
        
        try:
            
            shutil.rmtree(backup_path)
            self.logger.info(f"[+] Backup deleted: {backup_name}")
            return True
            
        except Exception as e:
            
            self.logger.error(f"[x] Failed to delete backup {backup_name}: {e}")
            return False


    def get_stats( self ) -> Dict[str, Any]:
        
        
        return {
            
            'enabled': self.config.enabled,
            'directory': str(self.config.directory),
            'max_backups': self.config.max_backups,
            'total_created': self._backup_count,
            'last_backup_time': self._last_backup_time,
            'last_backup_size': self._last_backup_size,
            'backup_in_progress': self._backup_in_progress,
            'available_backups': len(self.list_backups())
        }