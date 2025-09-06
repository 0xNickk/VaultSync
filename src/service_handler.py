#!/usr/bin/env python3
"""
VaultSync Service Handler - Background process management
Author: 0xNickk
Version: 2.1.0
"""

import sys
import os
import subprocess
import psutil
import time
import yaml
import winreg
from pathlib import Path
from datetime import datetime
from typing import Optional
from sync import VaultSync
from anytree import Node, RenderTree


class ServiceHandler:
    
    # Handle starting/stopping VaultSync as background process
    
    def __init__( self ):
        
        self.base_dir = Path(__file__).parent.parent.absolute()
        self.src_dir = self.base_dir / "src"
        self.sync_script = self.src_dir / "sync.py"
        self.pid_file = self.base_dir / ".pid"
        
        # Windows Registry key for startup programs
        self.startup_key = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"
        self.app_name = "VaultSync"
        
        
    def run_background( self ):
        
        if not self._validate_configuration():
            return
            
        if self.is_running():
            
            print("\n[*] VaultSync is already running in background")
            self.check_status()
            return

        print("\n[+] Starting VaultSync in background...")
    
        
        try:

            if not self.sync_script.exists():
                print(f"[-] Sync script not found: {self.sync_script}")
                return
            
            if sys.platform == "win32":
                
                # Create startup info to hide window
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE
                
                # Start detached process
                process = subprocess.Popen([
                    
                    sys.executable, str(self.sync_script)
                    
                ], 
                                           
                cwd=self.base_dir,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL,
                startupinfo=startupinfo,
                creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP,
                close_fds=True
                
                )
                
            else:
                
                # For Unix-like systems
                process = subprocess.Popen([
                    
                    sys.executable, str(self.sync_script)
                    
                ], 
                cwd=self.base_dir,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL,
                preexec_fn=os.setsid,
                close_fds=True
                )

            # Wait a moment for process to start
            time.sleep(3)
            
            # Find the actual VaultSync process
            vault_pid = self._find_vault_process()
            
            if vault_pid:
                
                self.pid_file.write_text(str(vault_pid))
                print(f"[+] VaultSync started in background!")
                print(f"[+] PID: {vault_pid}")
                print("[+] Logs: VaultSync.log\n")
                
            else:
                print("[x] Failed to run VaultSync - process not found")
                print("[+] Check VaultSync.log for details")
                
        except Exception as e:
            print(f"[x] Error starting background process: {e}")
            
            
    
    def _find_vault_process( self ) -> Optional[int]:
        
        # Find VaultSync process by command line arguments
        try:
            
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                
                try:
                    
                    if proc.info['name'] and 'python' in proc.info['name'].lower():
                        
                        cmdline = proc.info['cmdline']
                        if cmdline and any('sync.py' in str(arg) for arg in cmdline):
                            return proc.info['pid']
                            
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
                    
        except Exception:
            pass
            
        return None
    
    
    
    def run_normal( self ):

        if not self._validate_configuration():
            return

        if self.is_running():
            
            print("\n[*]  VaultSync is already running in background")
            print("[+]  Use --stop to stop it first, then --run\n")
            return
        
        try:

            print("[+] Starting VaultSync normally...")
            print("[+] Press Ctrl+C to stop")
            print("-" * 50)
            
            app = VaultSync()
            app.run()
            
        except ImportError as e:
            
            print(f"[x] Cannot import sync module: {e}")
            
        except KeyboardInterrupt:
            print("\n[*] VaultSync stopped by user")
            
        except Exception as e:
            print(f"[x] Error running VaultSync: {e}")
            
    
    def stop_background( self ):
    
        # Stop background VaultSync process

        if not self.is_running():
            print("[*] VaultSync is not running")
            return
        
        try:
            pid = int(self.pid_file.read_text().strip())
            process = psutil.Process(pid)
            
            print("\n[+] Stopping VaultSync background process...")
            process.terminate()
            
            try:
                process.wait(timeout=10)
            except psutil.TimeoutExpired:

                print("[*] Force killing process...")
                process.kill()
                
            if self.pid_file.exists():
                self.pid_file.unlink()

            print("[+] VaultSync process stopped.\n")
            
        except Exception as e:
            print(f"[x] Error stopping process: {e}")
            
            
    
    def enable_autorun( self ):
        
        if not self._validate_configuration():
            return
        
        # Enable VaultSync to run automatically on Windows boot
        
        if sys.platform != "win32":
            print("[x] Auto-run is only supported on Windows")
            return False
            
        try:

            print("\n[+] Enabling VaultSync auto-run on Windows boot...")
            
            main_script = self.base_dir / "VaultSync.py"
            
            # Use pythonw.exe instead of python.exe to avoid console window
            python_executable = sys.executable
            if python_executable.endswith('python.exe'):
                pythonw_executable = python_executable.replace('python.exe', 'pythonw.exe')
            else:
                pythonw_executable = python_executable
            
            startup_command = f'"{pythonw_executable}" "{main_script}" --background'
            
            # Open Windows Registry key for startup programs
            with winreg.OpenKey(
                
                winreg.HKEY_CURRENT_USER, 
                self.startup_key, 
                0, 
                winreg.KEY_SET_VALUE
                
            ) as key:
                
                winreg.SetValueEx(
                    
                    key, 
                    self.app_name, 
                    0, 
                    winreg.REG_SZ, 
                    startup_command
                )
                
            full_key = f"HKEY_CURRENT_USER\\{self.startup_key}\\{self.app_name}"
            
            print(f"[+] VaultSync auto-run enabled")
            print(f"[+] HKEY created: {full_key}")
            print("[+] VaultSync will now run silently when Windows boots")
            print("[+] Use --disable-autorun to remove auto-run\n")

            return True
            
        except PermissionError:
            print("[x] Permission denied. Run as administrator to enable auto-run")
            return False
            
        except Exception as e:
            print(f"[x] Failed to enable auto-run: {e}")
            return False
        
           
        
        
    def disable_autorun( self ):

        # Disable VaultSync auto-run on Windows boot

        if sys.platform != "win32":
            print("[x] Auto-run is only supported on Windows")
            return False

        try:

            if not self.is_autorun_enabled():
                print("\n[*] VaultSync auto-run is not enabled\n")
                return True

            print("\n[+] Disabling VaultSync auto-run...")
            print(f"[*] Removing HKEY (HKEY_CURRENT_USER\\{self.startup_key}\\{self.app_name})")
            
            # Open Windows Registry key for startup programs
            with winreg.OpenKey(
                
                winreg.HKEY_CURRENT_USER, 
                self.startup_key, 
                0, 
                winreg.KEY_SET_VALUE
                
            ) as key:
                
                winreg.DeleteValue(key, self.app_name)

            print("[+] VaultSync auto-run disabled")
            print("[+] VaultSync will no longer run automatically on Windows boot\n")
            
            return True
        
            
        except PermissionError:
            print("[x] Permission denied. Run as administrator to disable auto-run")
            return False
            
        except Exception as e:
            print(f"[x] Failed to disable auto-run: {e}")
            return False
        
        
    
    def is_autorun_enabled( self ) -> bool:

        # Check if VaultSync auto-run is enabled

        if sys.platform != "win32":
            return False
            
        try:
            
            # Open Windows Registry key for startup programs
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.startup_key, 0, winreg.KEY_READ) as key:
                
                try:
                    value, _ = winreg.QueryValueEx(key, self.app_name)
                    return True
                    
                except FileNotFoundError:
                    return False
                    
        except Exception:
            return False
        


    def get_autorun_command( self ) -> Optional[str]:

        # Get the autorun command if enabled

        if sys.platform != "win32":
            return None
            
        try:
            
            # Open Windows Registry key for startup programs
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.startup_key, 0, winreg.KEY_READ) as key:
                
                try:
                    
                    value, _ = winreg.QueryValueEx(key, self.app_name)
                    return value
                    
                except FileNotFoundError:
                    return None
                    
        except Exception:
            return None
        
        
    
    def is_running( self ) -> bool:
        
        if not self.pid_file.exists():
            return False
        
        try:
            pid = int(self.pid_file.read_text().strip())
            
            if psutil.pid_exists(pid):
                process = psutil.Process(pid)
                return process.is_running() and "python" in process.name().lower()
            else:
                
                # Clean up stale PID file
                self.pid_file.unlink()
                return False
                
        except ( ValueError, psutil.NoSuchProcess, psutil.AccessDenied ):
            return False
        
    
    def check_status( self ):

        # Check VaultSync background process status
        print("\n[+] VaultSync Status")
        print("-" * 25)
        
        if self.is_running():
            
            try:
                
                pid = int(self.pid_file.read_text().strip())
                process = psutil.Process(pid)
                
                create_time = datetime.fromtimestamp(process.create_time())
                memory_mb = process.memory_info().rss / 1024 / 1024
                
                print("[+] Status: RUNNING")
                print(f"[+] PID: {pid}")
                print(f"[+] Started: {create_time.strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"[+] Memory: {memory_mb:.1f} MB")
                

            except Exception as e:
                print(f"[+] Status: RUNNING (details unavailable: {e})")
        else:
            print("[+] Status: NOT RUNNING")

        # Check auto-run status
        if sys.platform == "win32":

            if self.is_autorun_enabled():

                command = self.get_autorun_command()
                print(f"[+] Auto-run: ENABLED")
                print(f"[+] HKEY location: HKEY_CURRENT_USER\\{self.startup_key}\\{self.app_name}")
                
            else:
                print("[+] Auto-run: DISABLED")

        log_file = self.base_dir / "VaultSync.log"
        
        if log_file.exists():
            
            print(f"[+] Log file: {log_file}")
            print(f"[+] Log size: {log_file.stat().st_size} bytes")
            mod_time = datetime.fromtimestamp(log_file.stat().st_mtime)
            print(f"[+] Last modified: {mod_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            
        else:
            print("[+] Log file: Not found\n")
            

    def check_requirements( self ) -> bool:

        print("\n[+] Checking VaultSync requirements...")
        print("-" * 50)
        
        required_files = [
            
            (self.base_dir / ".env", "Environment file"),
            (self.base_dir / "config.yaml", "Configuration file"),
            (self.sync_script, "Sync engine"),
        ]
        
        missing_files = []
        
        for file_path, description in required_files:
            
            if file_path.exists():
                print(f"[+] {description}: {file_path}")
            else:
                print(f"[-] {description}: {file_path}")
                missing_files.append(description)
        
        print("-" * 50)
        
        dependencies = [
            
            ('psutil', 'Process monitoring'),
            ('schedule', 'Task scheduling'),
            ('plyer', 'Notifications'),
            ('anytree', 'Tree display (optional)'),
        ]
        
        for module, description in dependencies:
            
            try:
                __import__(module.replace('-', '_'))
                print(f"[+] {description}: {module}")
                
            except ImportError:
                if module == 'anytree':
                    print(f"[*] {description}: {module} (using fallback)")
                else:
                    print(f"[-] {description}: {module}")
                    missing_files.append(module)
        
        
        if missing_files:
            
            print(f"[x] Missing requirements: {', '.join(missing_files)}")
            print("[+] Install missing packages:")
            print("[+]  pip install -r requirements.txt")
            return False
        
        else:
            print("[+] All requirements satisfied!\n")
            return True
        
        
    
    def _validate_configuration( self ) -> bool:

        # Validate that all required configuration fields are set
        
        config_file = self.base_dir / "config.yaml"
        env_file = self.base_dir / ".env"
        
        # Check if files exist
        if not config_file.exists():
            print("[x] Configuration file not found: config.yaml")
            return False
            
        if not env_file.exists():
            print("[x] Environment file not found: .env")
            return False
        
        try:
            
            # Load and validate config.yaml
            with open(config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            # Load and validate .env
            env_vars = {}
            with open(env_file, 'r', encoding='utf-8') as f:
                
                for line in f:
                    
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        
                        key, value = line.split('=', 1)
                        env_vars[key.strip()] = value.strip()
            
            missing_fields = []
            
            # Check required config fields
            if not config.get('vault', {}).get('path'):
                missing_fields.append('vault.path')
                
            if not config.get('git', {}).get('user_name'):
                missing_fields.append('git.user_name')
                
            if not config.get('git', {}).get('user_email'):
                missing_fields.append('git.user_email')
                
            # Check required environment variables
            if not env_vars.get('GITHUB_TOKEN'):
                missing_fields.append('GITHUB_TOKEN (in .env)')
                
            if not env_vars.get('GITHUB_USERNAME'):
                missing_fields.append('GITHUB_USERNAME (in .env)')
                
            if not env_vars.get('GITHUB_REPOSITORY'):
                missing_fields.append('GITHUB_REPOSITORY (in .env)')
            
            if missing_fields:
                
                print("\n[x] Configuration is incomplete")
                print("[+] Missing required fields:")
                
                for field in missing_fields:
                    print(f"    - {field}")
                    
                print("")
                    
                return False
            
            # Check if vault path exists
            vault_path = Path(config['vault']['path'])
            
            if not vault_path.exists():
                
                print(f"[x] Vault path does not exist: {vault_path}")
                print("[+] Please set a valid vault path using --vault-path\n")
                return False
            
            return True
            
        except Exception as e:
            print(f"[x] Error validating configuration: {e}")
            return False
    
    def show_config( self ):

        try:
            config_file = self.base_dir / "config.yaml"
            env_file = self.base_dir / ".env"
        
            self._show_config_with_anytree(config_file, env_file)
                
        except Exception as e:
            print(f"[x] Config display error: {e}")

    def _show_config_with_anytree( self, config_file, env_file ):
        
        root = Node("\n📁 VaultSync Configuration")
        
        # File information
        files_node = Node("📂 Files", parent=root)
        Node(f"📄 Config: {config_file.name}", parent=files_node)
        Node(f"🔑 Environment: {env_file.name}", parent=files_node)
        Node(f"📁 Directory: {self.base_dir}", parent=files_node)
        
        # Display config.yaml content
        if config_file.exists():
            
            with open(config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            config_node = Node("📋 config.yaml", parent=root)
            
            # Vault section
            vault_node = Node("📁 Vault", parent=config_node)
            Node(f"path: {config.get('vault', {}).get('path', 'NOT SET')}", parent=vault_node)
            Node(f"branch: {config.get('vault', {}).get('branch', 'main')}", parent=vault_node)
            
            # Sync section
            sync_node = Node("⚙️  Sync", parent=config_node)
            Node(f"mode: {config.get('sync', {}).get('mode', 'on_close')}", parent=sync_node)
            Node(f"interval_minutes: {config.get('sync', {}).get('interval_minutes', 2)}", parent=sync_node)
            Node(f"process_name: {config.get('sync', {}).get('process_name', 'Obsidian.exe')}", parent=sync_node)
            
            # Backup section
            backup_enabled = config.get('backup', {}).get('enabled', True)
            backup_node = Node("💾 Backup", parent=config_node)
            Node(f"enabled: {backup_enabled}", parent=backup_node)
            
            if backup_enabled:
                Node(f"directory: {config.get('backup', {}).get('directory', 'NOT SET')}", parent=backup_node)
                Node(f"max_backups: {config.get('backup', {}).get('max_backups', 2)}", parent=backup_node)
            
            # Logging section
            logging_node = Node("📝 Logging", parent=config_node)
            Node(f"file: {config.get('logging', {}).get('file', 'VaultSync.log')}", parent=logging_node)
            Node(f"level: {config.get('logging', {}).get('level', 'INFO')}", parent=logging_node)
            
            # Notification section
            notification_enabled = config.get('notification', {}).get('enabled', True)
            notification_node = Node("🔔 Notification", parent=config_node)
            Node(f"enabled: {notification_enabled}", parent=notification_node)
            
            if notification_enabled:
                Node(f"timeout: {config.get('notification', {}).get('timeout', 3)} seconds", parent=notification_node)
                icon_path = config.get('notification', {}).get('icon_path')
                Node(f"icon_path: {icon_path if icon_path else 'Default'}", parent=notification_node)
            
            # Git section
            git_node = Node("🔗 Git", parent=config_node)
            Node(f"timeout: {config.get('git', {}).get('timeout', 120)} seconds", parent=git_node)
            Node(f"user_name: {config.get('git', {}).get('user_name', 'NOT SET')}", parent=git_node)
            Node(f"user_email: {config.get('git', {}).get('user_email', 'NOT SET')}", parent=git_node)
            
            # Gitignore section
            gitignore = config.get('git', {}).get('gitignore', {})
            gitignore_node = Node("📝 gitignore", parent=git_node)
            
            for section, patterns in gitignore.items():
                
                if patterns:
                    Node(f"{section}: {len(patterns)} pattern(s)", parent=gitignore_node)
                else:
                    Node(f"{section}: No patterns", parent=gitignore_node)
        
        else:
            Node("[x] config.yaml not found", parent=root)
        
        # Display .env content
        if env_file.exists():
            
            env_node = Node("🔐 .env", parent=root)
            
            with open(env_file, 'r', encoding='utf-8') as f:
                
                for line in f:
                    
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip()
                        
                        if key == 'GITHUB_TOKEN':
                            if value:
                                obfuscated = f"{value[:4]}{'*' * (len(value) - 8)}{value[-4:]}" if len(value) > 8 else "***"
                                Node(f"{key}: {obfuscated}", parent=env_node)
                            else:
                                Node(f"{key}: NOT SET", parent=env_node)
                        else:
                            Node(f"{key}: {value if value else 'NOT SET'}", parent=env_node)
        
        else:
            Node("[x] .env not found", parent=root)
        
        # Print the tree using anytree
        for pre, fill, node in RenderTree(root):
            print(f"{pre}{node.name}")
        
        print()

    


if __name__ == "__main__":
    handler = ServiceHandler()