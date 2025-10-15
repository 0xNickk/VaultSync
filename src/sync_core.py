#!/usr/bin/env python3

import sys
import time
import schedule
from pathlib import Path
from typing import Optional
from datetime import datetime

from config.config_manager import ConfigManager
from utils.logger import Logger
from utils.notification_manager import NotificationManager
from utils.backup_manager import BackupManager
from git.git_manager import GitManager
from utils.process_monitor import ProcessMonitor


class VaultSync:

    def __init__( self, config_path: str = "config.yaml", env_path: str = ".env", service_mode: bool = False ):

        self.config = ConfigManager(config_path, env_path)
        self.config.validate()
        
        self.service_mode = service_mode
        
        log_file = self.config.base_dir / "VaultSync.log"
        self.logger = Logger(str(log_file), service_mode=service_mode)
        
        self.notification = NotificationManager(self.config.notification, self.logger)
        self.backup = BackupManager(self.config.backup, self.config.vault.path, self.logger)
        
        self.git = GitManager(
            
            self.config.git,
            self.config.vault.path,
            self.config.git_remote,
            self.config.vault.branch,
            self.logger
        )
        
        self.process_monitor = ProcessMonitor(self.config.sync.process_name, self.logger)
        
        self._obsidian_was_running = False
        self._initial_pull_done = False
        self._sync_in_progress = False
        
        
    def _handle_obsidian_startup( self ) -> None:

        # Handle pull operations when Obsidian starts

        if self._sync_in_progress:
            self.logger.warning("[!] Sync already in progress, skipping startup sync")
            return
            
        self._sync_in_progress = True
        
        try:
            
            self.logger.info("[+] Obsidian startup detected - pulling latest changes")
            
            backup_success = self.backup.create_backup()
            
            if not backup_success:
                self.logger.warning("[!] Backup failed, but continuing with sync")
            
            if self.git.pull():
                
                self.notification.send(True, "Synced with remote on startup")
                self._initial_pull_done = True
                self.logger.info("[+] Startup sync completed successfully")
                
            else:
                
                self.notification.send(False, "Failed to sync on startup")
                self._initial_pull_done = False
                self.logger.error("[x] Startup sync failed")
                
        except Exception as e:
            
            self.logger.error(f"[x] Startup sync error: {e}")
            self.notification.send(False, f"Startup sync error: {str(e)}")
            
        finally:
            self._sync_in_progress = False
            
            
    def _handle_obsidian_shutdown( self ) -> None:

        # Handle push operations when Obsidian closes
        
        if self._sync_in_progress:
            self.logger.warning("[!] Sync already in progress, skipping shutdown sync")
            return
            
        self._sync_in_progress = True
        
        try:
            
            self.logger.info("[+] Obsidian shutdown detected - pushing changes")
            
            if self.git.push():
                
                self.notification.send(True, "Changes pushed on shutdown")
                self.logger.info("[+] Shutdown sync completed successfully")
                
            else:
                
                self.notification.send(False, "Failed to push on shutdown")
                self.logger.error("[x] Shutdown sync failed")
                
        except Exception as e:
            
            self.logger.error(f"[x] Shutdown sync error: {e}")
            self.notification.send(False, f"Shutdown sync error: {str(e)}")
            
        finally:
            self._sync_in_progress = False
            

    def _periodic_push( self ) -> None:

        # Handle periodic push operations in interval mode

        if self._sync_in_progress:
            self.logger.warning("[!] Sync already in progress, skipping periodic sync")
            return
            
        self._sync_in_progress = True
        
        try:
            
            self.logger.info("[+] Periodic sync triggered")

            if self.git.push():
                
                self.notification.send(True, "Periodic sync completed")
                self.logger.info("[+] Periodic sync completed successfully")
                
            else:
                
                self.notification.send(False, "Periodic sync failed")
                self.logger.error("[x] Periodic sync failed")
                
        except Exception as e:
            
            self.logger.error(f"[x] Periodic sync error: {e}")
            self.notification.send(False, f"Periodic sync error: {str(e)}")
            
        finally:
            self._sync_in_progress = False


    def run( self ) -> None:


        self.logger.info("[+] VaultSync Starting")
        self.logger.info(f"[+] Vault: {self.config.vault.path}")
        self.logger.info(f"[+] Mode: {self.config.sync.mode}")
        
        if self.service_mode:
            self.logger.info("[+] Running as Windows Service")

        self.notification.send_startup()

        if not self.git.setup_repository():
            self.logger.error("[x] Git setup failed - exiting")
            self.notification.send_error("Git setup failed")
            return
        
        try:
            if self.config.sync.mode == "interval":
                self._run_interval_mode()
                
            elif self.config.sync.mode == "on_close":
                self._run_on_close_mode()
                
            else:
                self.logger.error(f"[x] Invalid sync mode: {self.config.sync.mode}")
                self.notification.send_error(f"Invalid sync mode: {self.config.sync.mode}")

        except KeyboardInterrupt:

            self.logger.info("[x] Interrupted by user")
            
            if self._obsidian_was_running:
                self.logger.info("[+] Performing final push...")
                self.git.push()
                
        except Exception as e:

            self.logger.error(f"[x] Unexpected error: {e}")
            self.notification.send_error(f"Unexpected error: {str(e)}")

        finally:
            self.logger.info("[+] VaultSync stopped")
            self.notification.send_shutdown()

    
    def _run_interval_mode( self ) -> None:
        
        
        self.logger.info(f"[+] Starting interval mode (every {self.config.sync.interval_minutes} minutes)")
        
        # Initial startup pull
        self._handle_obsidian_startup()
        
        schedule.every(self.config.sync.interval_minutes).minutes.do(self._periodic_push)
        
        last_check = time.time()
        check_interval = 5  
        
        while True:

            current_time = time.time()
            
            # Only check process status every few seconds to reduce CPU usage
            if current_time - last_check >= check_interval:
                
                obsidian_running = self.process_monitor.is_running()
                
                # Handle Obsidian restart
                if obsidian_running and not self._obsidian_was_running:
                    
                    if self._initial_pull_done:
                        self.logger.info("[+] Obsidian restarted - pulling updates")
                        self._handle_obsidian_startup()
                
                self._obsidian_was_running = obsidian_running
                last_check = current_time
            
            schedule.run_pending()
            time.sleep(1) 
    
    
    def _run_on_close_mode( self ) -> None:
       
        self.logger.info("[+] Starting on-close mode - monitoring Obsidian")

        last_check = time.time()
        check_interval = 3  
        
        while True:
            
            current_time = time.time()
            
            # Only check process status periodically to reduce CPU usage
            if current_time - last_check >= check_interval:
                
                obsidian_running = self.process_monitor.is_running()
                
                # Handle Obsidian startup
                if obsidian_running and not self._obsidian_was_running:
                    self._handle_obsidian_startup()
                
                # Handle Obsidian shutdown
                elif not obsidian_running and self._obsidian_was_running:
                    
                    self._handle_obsidian_shutdown()
                    self.logger.info("[+] Continuing to monitor for next Obsidian session...")

                self._obsidian_was_running = obsidian_running
                last_check = current_time

            time.sleep(1)  


def create_service_instance():

    return VaultSync(service_mode=True)


def main():
    
    try:
        
        app = VaultSync()
        app.run()
        
    except Exception as e:
        
        print(f"[x] Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()