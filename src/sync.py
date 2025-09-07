#!/usr/bin/env python3
"""
VaultSync Core Engine
Author: 0xNickk
Version: 2.1.0
License: MIT
"""

import os
import sys
import time
import shutil
import subprocess
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict
from dataclasses import dataclass
import psutil
import schedule
import yaml
from dotenv import load_dotenv
from plyer import notification


@dataclass
class VaultConfig:
    # Config for vault
    path: Path
    branch: str

@dataclass
class SyncConfig:
    # Config for sync settings
    mode: str
    interval_minutes: int
    process_name: str

@dataclass
class BackupConfig:
    # Config for backups
    enabled: bool
    directory: Path
    max_backups: int

@dataclass
class NotificationConfig:   
    # Config for desktop notifications
    enabled: bool
    timeout: int
    icon_path: Optional[Path]

@dataclass
class GitConfig:
    # Config for git 
    timeout: int
    user_name: str
    user_email: str
    gitignore: Dict[str, list] 


class ConfigManager:
        
    def __init__( self, config_path: str = "config.yaml", env_path: str = ".env" ):  
        
        current_dir = Path(__file__).parent.absolute()  # src directory
        self.base_dir = current_dir.parent.absolute()   # VaultSync directory        
        self.config_path = self.base_dir / config_path
        self.env_path = self.base_dir / env_path
        self._load_environment()
        self._load_config()      
        
    def _load_environment( self ) -> None:    
        
        if self.env_path.exists():
            load_dotenv(self.env_path)
        else:
            raise FileNotFoundError(f"Environment file not found: {self.env_path}") 
            
    def _load_config( self ) -> None:
        
        # Load configuration from .yaml file     
        
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")     
            
        with self.config_path.open('r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)
            
        # Create config objects        
        self.vault = VaultConfig(            
            path=Path(config_data['vault']['path']),
            branch=config_data['vault']['branch']
        )     
        
        self.sync = SyncConfig(            
            mode=config_data['sync']['mode'],
            interval_minutes=config_data['sync']['interval_minutes'],
            process_name=config_data['sync']['process_name']
        )        
        
        self.backup = BackupConfig(            
            enabled=config_data['backup']['enabled'],
            directory=Path(config_data['backup']['directory']),
            max_backups=config_data['backup']['max_backups']
        )       
        
        self.notification = NotificationConfig(            
            enabled=config_data['notification']['enabled'],
            timeout=config_data['notification']['timeout'],
            icon_path=Path(config_data['notification']['icon_path']) 
                      if config_data['notification']['icon_path'] else None
        )    
        
        self.git = GitConfig(            
            timeout=config_data['git']['timeout'],
            user_name=config_data['git']['user_name'],
            user_email=config_data['git']['user_email'],
            gitignore=config_data['git']['gitignore']  
        )   
        
        # Build Git remote URL from environment variables
        github_token = os.getenv('GITHUB_TOKEN')
        github_username = os.getenv('GITHUB_USERNAME')
        github_repository = os.getenv('GITHUB_REPOSITORY')
        
        if not all([github_token, github_username, github_repository]):
            raise ValueError("Missing required environment variables: GITHUB_TOKEN, GITHUB_USERNAME, GITHUB_REPOSITORY")
        
        self.git_remote = f"https://{github_token}@github.com/{github_username}/{github_repository}.git"
    
    def validate( self ) -> None:
        
        # Basic validation of config values        
        if not self.vault.path.exists():
            raise ValueError(f"Vault path does not exist: {self.vault.path}")
        
        if self.sync.mode not in ['interval', 'on_close']:
            raise ValueError(f"Invalid sync mode: {self.sync.mode}")
        
        if self.sync.interval_minutes <= 0:
            raise ValueError("Sync interval must be positive")


class Logger:

    def __init__( self, log_file: str, level: str = "INFO", service_mode: bool = False ):  
        
        self.logger = logging.getLogger("VaultSync")
        self.logger.setLevel(getattr(logging, level.upper()))
        self.service_mode = service_mode

        # Clear existing handlers
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        formatter = logging.Formatter(            
            '[%(asctime)s] [%(levelname)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )        
        
        if not service_mode:            
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        
    
    def debug( self, message: str ) -> None:
        self.logger.debug(message)
    
    def info( self, message: str ) -> None:
        self.logger.info(message)
    
    def warning( self, message: str ) -> None:
        self.logger.warning(message)
    
    def error( self, message: str ) -> None:
        self.logger.error(message)


class NotificationManager:

    # Handles desktop notifications

    def __init__( self, config: NotificationConfig, logger: Logger ):   
        
        self.config = config
        self.logger = logger
            
    def send( self, success: bool, message: Optional[str] = None ) -> None:

        if not self.config.enabled:
            return
         
        try:
            
            title = "🔄 Vault Sync" if success else "🔄 Vault Sync Error"
            msg = message or ("Sync completed successfully!" if success else "Sync failed - check logs")

            notification.notify(                
                title=title,
                message=msg,
                app_name="VaultSync",
                timeout=self.config.timeout
            )      
            
        except Exception as e:
            self.logger.warning(f"Notification error: {e}")


class BackupManager:

    # Handles vault backups

    def __init__( self, config: BackupConfig, vault_path: Path, logger: Logger ): 
        
        self.config = config
        self.vault_path = vault_path
        self.logger = logger
    
    def create_backup( self ) -> bool:

        if not self.config.enabled:
            return True
        
        try:     
            
            self.config.directory.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = self.config.directory / f"vault_backup_{timestamp}"
            
            shutil.copytree(                
                self.vault_path,
                backup_path,
                ignore=shutil.ignore_patterns('.git', '*.tmp', '*.lock', '__pycache__', '.trash')
            )       
            
            self.logger.info(f"[+] Backup created: {backup_path.name}")
            self._cleanup_old_backups()
            return True       
            
        except Exception as e:
            self.logger.error(f"[x] Backup failed: {e}")
            return False
    
    def _cleanup_old_backups( self ) -> None:        
        # Remove old backups exceeding max_backups

        try:
            backups = sorted([                
                d for d in self.config.directory.iterdir()
                if d.is_dir() and d.name.startswith('vault_backup_')                
            ], key=lambda x: x.name)
            
            while len(backups) > self.config.max_backups:                
                oldest = backups.pop(0)
                shutil.rmtree(oldest, ignore_errors=True)
                self.logger.info(f"[+] Removed old backup: {oldest.name}")   
                
        except Exception as e:
            self.logger.warning(f"[!] Cleanup warning: {e}")


class GitManager:    
    
    # Handles all Git operations

    def __init__( self, config: GitConfig, vault_path: Path, remote_url: str, branch: str, logger: Logger ):   
        
        self.config = config
        self.vault_path = vault_path
        self.remote_url = remote_url
        self.branch = branch
        self.logger = logger
        
        # Setup startup info for hiding Git windows on Windows
        self.startupinfo = None
        if sys.platform == "win32":            
            self.startupinfo = subprocess.STARTUPINFO()
            self.startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            self.startupinfo.wShowWindow = subprocess.SW_HIDE

    def _run_command( self, cmd: list, description: str = "Git command" ) -> Optional[subprocess.CompletedProcess]:

        # Run a git command and handle output
        try:
            result = subprocess.run(                
                cmd,
                cwd=self.vault_path,
                capture_output=True,
                text=True,
                timeout=self.config.timeout,
                startupinfo=self.startupinfo,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            )            
            
            if result.stdout.strip() and "nothing to commit" not in result.stdout.lower():
                self.logger.info(f"[+] {description}: {result.stdout.strip()}")
            
            if result.stderr.strip():
                stderr = result.stderr.strip()
                
                # Filter out common non-error messages
                if not any(msg in stderr.lower() for msg in [                    
                    "lf will be replaced by crlf",
                    "warning: adding embedded git repository",
                    "branch            main       -> fetch_head",
                    "[new branch]      main       -> origin/main",
                    "to https://github.com",
                    "main -> main"
                ]):
                    self.logger.warning(f"[!] {description} stderr: {stderr}")

            return result      
            
        except subprocess.TimeoutExpired:
            self.logger.error(f"[!] {description} timed out")
            return None           
            
        except Exception as e:
            self.logger.error(f"[x] {description} failed: {e}")
            return None
        
        
    def setup_repository( self ) -> bool:

        # Initialize and configure git repository if needed
        try:
            
            self.logger.info("[+] Setting up Git repository...")            
            if not (self.vault_path / ".git").exists():
                self.logger.info("[+] Initializing new Git repository")

                if not self._run_command(["git", "init"], "Git init"):
                    return False                
                self._run_command(["git", "branch", "-M", self.branch], "Set main branch")

            # Configure Git user
            self._run_command(["git", "config", "user.name", self.config.user_name], "Set user name")
            self._run_command(["git", "config", "user.email", self.config.user_email], "Set user email")
            
            result = self._run_command(["git", "remote", "get-url", "origin"], "Check remote")
            
            if not result or result.returncode != 0:   
                
                self.logger.info("🔗 Adding remote origin")
                self._run_command(["git", "remote", "add", "origin", self.remote_url], "Add remote")   
                
            else:
                current_remote = result.stdout.strip()
                
                if current_remote != self.remote_url:
                    self.logger.info("[+] Updating remote URL")
                    self._run_command(["git", "remote", "set-url", "origin", self.remote_url], "Update remote")

            self._create_gitignore()            
            self.logger.info("[+] Git repository setup completed")
            return True   
            
        except Exception as e:
            self.logger.error(f"[x] Git setup failed: {e}")
            return False
        
        
    def _create_gitignore( self ) -> None:

        # Create or update .gitignore based on config
        gitignore_path = self.vault_path / ".gitignore"
        
        if gitignore_path.exists():
            self.logger.info("[+] Updating existing .gitignore file...")
        else:
            self.logger.info("[+] Creating new .gitignore file...")

        gitignore_sections = []
        
        # Obsidian files
        if 'obsidian' in self.config.gitignore and self.config.gitignore['obsidian']:            
            gitignore_sections.append("# Obsidian workspace (user-specific)")
            gitignore_sections.extend(self.config.gitignore['obsidian'])
            gitignore_sections.append("") 
        
        # System files 
        if 'system' in self.config.gitignore and self.config.gitignore['system']:            
            gitignore_sections.append("# System files")
            gitignore_sections.extend(self.config.gitignore['system'])
            gitignore_sections.append("")  
        
        # Directories
        if 'directories' in self.config.gitignore and self.config.gitignore['directories']:            
            gitignore_sections.append("# Directories")
            gitignore_sections.extend(self.config.gitignore['directories'])
            gitignore_sections.append("") 
        
        # Custom 
        if 'custom' in self.config.gitignore and self.config.gitignore['custom']:            
            gitignore_sections.append("# Custom patterns")
            gitignore_sections.extend(self.config.gitignore['custom'])
            gitignore_sections.append("")  
        
        gitignore_content = f"""# .gitignore generated by VaultSync
# Configuration: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
# Edit patterns in config.yaml under git.gitignore section

{chr(10).join(gitignore_sections).rstrip()}

# End of VaultSync .gitignore
"""
        
        try:        
            
            gitignore_path.write_text(gitignore_content, encoding='utf-8')
            self.logger.info(f"[+] .gitignore file {'updated' if gitignore_path.exists() else 'created'} successfully")            
            configured_sections = [k for k, v in self.config.gitignore.items() if v]
            
            if configured_sections:
                self.logger.info(f"[+] Configured sections: {', '.join(configured_sections)}")    
                
        except Exception as e:
            self.logger.error(f"[x] Failed to create .gitignore: {e}")
            
            
    def _has_initial_commit( self ) -> bool:

        # Check if repository has at least one commit
        try:
            result = self._run_command(["git", "rev-parse", "HEAD"], "Check initial commit")
            return result and result.returncode == 0
        except:
            return False

    def _remote_branch_exists( self ) -> bool:

        # Check if the remote branch exists

        try:            
            result = self._run_command(["git", "ls-remote", "--heads", "origin", self.branch], "Check remote branch")
            return result and result.returncode == 0 and result.stdout.strip()            
        except:
            return False
        
    def pull(self) -> bool:

        # Pull changes from remote repository        
        try:
            
            self.logger.info("[+] Pulling changes from remote...")
            
            # First check if remote branch exists
            if not self._remote_branch_exists():  
                
                self.logger.info("[*] Remote branch doesn't exist yet - this is normal for new repositories")
                self.logger.info("[*] Skipping pull, will push local changes to create remote branch")
                return True
            
            fetch_result = self._run_command(["git", "fetch", "origin", self.branch], "Fetch")
            
            if not fetch_result or fetch_result.returncode != 0:                
                # Check if it's because the remote ref doesn't exist
                if fetch_result and "couldn't find remote ref" in fetch_result.stderr:
                    self.logger.info("[*] Remote branch doesn't exist yet - this is normal for new repositories")
                    return True
                    
                self.logger.error("[x] Failed to fetch from remote")
                return False
            
            # Check for local changes
            status_result = self._run_command(["git", "status", "--porcelain"], "Status check")
            has_changes = status_result and status_result.stdout.strip()
            
            # Handle stashing
            stashed = False
            if has_changes and self._has_initial_commit():  
                
                self.logger.info("[+] Stashing local changes before pull")
                stash_result = self._run_command(                    
                    ["git", "stash", "push", "-m", f"Auto-stash before pull {datetime.now()}"] ,
                    "Stash"
                )     
                
                if stash_result and stash_result.returncode == 0:
                    stashed = True
                else:
                    self.logger.warning("[x] Could not stash changes")
            
            # Pull changes
            pull_result = self._run_command(["git", "pull", "origin", self.branch], "Pull")
            
            if pull_result and pull_result.returncode == 0:
                self.logger.info("[+] Successfully pulled changes")
                
                # Restore stashed changes
                if stashed:                    
                    self.logger.info("[+] Restoring stashed changes")
                    pop_result = self._run_command(["git", "stash", "pop"], "Stash pop")
                    
                    if pop_result and pop_result.returncode != 0:
                        self.logger.warning("[x] Could not restore stashed changes automatically")
                        return False
                
                return True
            else:
                self.logger.error("[x] Pull failed")
                return False    
                
        except Exception as e:
            self.logger.error(f"[x] Pull operation failed: {e}")
            return False
            
        
    def push(self) -> bool:

        # Push local changes to remote repository
        try:
            self.logger.info("[+] Pushing changes to remote...")

            # Check for changes
            status_result = self._run_command(["git", "status", "--porcelain"], "Status check")
            
            if not status_result or not status_result.stdout.strip():
                self.logger.info("[*] No changes to push")
                return True
            
            # Add changes
            add_result = self._run_command(["git", "add", "."], "Add changes")
            if not add_result or add_result.returncode != 0:
                return False
            
            # Commit changes
            commit_msg = f"VaultSync: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            commit_result = self._run_command(["git", "commit", "-m", commit_msg], "Commit")
            
            if not commit_result or commit_result.returncode != 0:
                self.logger.info("[*] Nothing new to commit")
                return True
            
            # Check if this is the first push to an empty repository
            if not self._remote_branch_exists():
                self.logger.info("[+] Pushing to empty repository - creating remote branch")
                push_result = self._run_command(["git", "push", "-u", "origin", self.branch], "Initial push")
            else:
                # Normal push
                push_result = self._run_command(["git", "push", "origin", self.branch], "Push")
            
            if push_result and push_result.returncode == 0:
                self.logger.info("[+] Successfully pushed changes")
                return True
            else:
                self.logger.error("[x] Push failed")
                return False       
                
        except Exception as e:
            self.logger.error(f"[x] Push operation failed: {e}")
            return False


class ProcessMonitor:

    # Monitors if Obsidian process is running        
    def __init__( self, process_name: str, logger: Logger ):     
        
        self.process_name = process_name
        self.logger = logger
        self._cached_pids = set()
    
    def is_running(self) -> bool:

        # Check through cached PIDs first for performance
        if self._cached_pids:
            alive_pids = set()
            
            for pid in self._cached_pids.copy():
                try:
                    if psutil.pid_exists(pid):
                        proc = psutil.Process(pid)
                        if proc.name() == self.process_name:
                            alive_pids.add(pid)
                             
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            if alive_pids:                
                self._cached_pids = alive_pids
                return True
            
            self._cached_pids.clear()
        
        # Full scan if no cached PIDs
        try:
            for proc in psutil.process_iter(['pid', 'name']):
                
                if proc.info['name'] == self.process_name:
                    self._cached_pids.add(proc.info['pid'])
                    return True
                
        except Exception as e:
            self.logger.warning(f"[x] Process scan error: {e}")
        
        return False


class VaultSync:    
    
    # Main 
    def __init__( self, config_path: str = "config.yaml", env_path: str = ".env", service_mode: bool = False ):

        # Load config 
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
        
        # State variables
        self._obsidian_was_running = False
        self._initial_pull_done = False
        
    def _handle_obsidian_startup( self ) -> None:

        # Handle pull when Obsidian starts
        self.logger.info("[+] Obsidian startup detected - pulling latest changes")
        
        self.backup.create_backup()
        
        if self.git.pull():
            
            self.notification.send(True, "✅ Synced with remote on startup")
            self._initial_pull_done = True
        else:
            self.notification.send(False, "❌ Failed to sync on startup")
            self._initial_pull_done = False
            
    def _handle_obsidian_shutdown( self ) -> None:

        # Handle push when Obsidian closes
        self.logger.info("[x] Obsidian shutdown detected - pushing changes")
        
        if self.git.push():
            self.notification.send(True, "✅ Changes pushed on shutdown")
        else:
            self.notification.send(False, "❌ Failed to push on shutdown")
            
    def _periodic_push( self ) -> None:

        # Handle periodic push in interval mode
        self.logger.info("[+] Periodic sync triggered")

        if self.git.push():
            self.notification.send(True, "✅ Periodic sync completed")
        else:
            self.notification.send(False, "❌ Periodic sync failed")

    def run(self) -> None:

        # Main run loop
        self.logger.info("=" * 60)
        self.logger.info("🔄 VaultSync Starting")
        self.logger.info(f"📁 Vault: {self.config.vault.path}")
        self.logger.info(f"⚙️  Mode: {self.config.sync.mode}")
        
        if self.service_mode:
            self.logger.info("[+] Running as Windows Service")
            
        self.logger.info("=" * 60)
        
        if not self.git.setup_repository():
            self.logger.error("[x] Git setup failed - exiting")
            return
        
        try:
            if self.config.sync.mode == "interval":
                self._run_interval_mode()
                
            elif self.config.sync.mode == "on_close":
                self._run_on_close_mode()
                
            else:
                self.logger.error("[x] Invalid sync mode")

        except KeyboardInterrupt:
            
            self.logger.info("[x] Interrupted by user")
            
            if self._obsidian_was_running:
                self.logger.info("[+] Performing final push...")
                self.git.push()
        
        self.logger.info("[+] VaultSync stopped")
        
    
    def _run_interval_mode( self ) -> None:
        
        # Run in interval mode
        self.logger.info(f"[+] Starting interval mode (every {self.config.sync.interval_minutes} minutes)")
        
        # Initial pull
        self._handle_obsidian_startup()
        
        # Schedule periodic pushes
        schedule.every(self.config.sync.interval_minutes).minutes.do(self._periodic_push)
        
        while True:
            # Check for Obsidian startup
            obsidian_running = self.process_monitor.is_running()
            
            if obsidian_running and not self._obsidian_was_running:
                
                if self._initial_pull_done:
                    self.logger.info("[+] Obsidian restarted - pulling updates")
                    self._handle_obsidian_startup()
            
            self._obsidian_was_running = obsidian_running
            schedule.run_pending()
            time.sleep(5)
    
    def _run_on_close_mode(self) -> None:

        # Run in on-close mode
        self.logger.info("[+] Starting on-close mode - monitoring Obsidian")

        while True:
            
            obsidian_running = self.process_monitor.is_running()
            
            # Obsidian started
            if obsidian_running and not self._obsidian_was_running:
                self._handle_obsidian_startup()
            
            # Obsidian stopped
            elif not obsidian_running and self._obsidian_was_running:
                self._handle_obsidian_shutdown()
                self.logger.info("[+] Continuing to monitor for next Obsidian session...")

            self._obsidian_was_running = obsidian_running
            time.sleep(3)


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
