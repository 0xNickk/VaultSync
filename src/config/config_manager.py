#!/usr/bin/env python3

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass
from dotenv import load_dotenv


@dataclass
class VaultConfig:

    path: Path
    branch: str


@dataclass
class SyncConfig:

    mode: str
    interval_minutes: int
    process_name: str


@dataclass
class BackupConfig:
    
    enabled: bool
    directory: Path
    max_backups: int


@dataclass
class NotificationConfig:   
    
    enabled: bool
    timeout: int
    icon_path: Optional[Path]


@dataclass
class GitConfig:

    timeout: int
    user_name: str
    user_email: str
    gitignore: Dict[str, list] 


class ConfigManager:

        
    def __init__( self, config_path: str = "config.yaml", env_path: str = ".env" ):
        
        current_dir = Path(__file__).parent.parent.parent.absolute()  # Go up to VaultSync directory
        self.base_dir = current_dir
        
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

        # Load and parse the .yaml configuration file
        
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
        
        try:
            
            with self.config_path.open('r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
            
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in config file: {e}")
        
        self._create_config_objects(config_data)
        self._build_git_remote()
        
        
    def _create_config_objects( self, config_data: Dict[str, Any] ) -> None:
        
        # Create dataclass instances for each config section
                
        try:
            
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
                directory=Path(config_data['backup']['directory']) if config_data['backup']['directory'] else Path(),
                max_backups=config_data['backup']['max_backups']
            )
            
            icon_path = config_data['notification']['icon_path']
            self.notification = NotificationConfig(
                
                enabled=config_data['notification']['enabled'],
                timeout=config_data['notification']['timeout'],
                icon_path=Path(icon_path) if icon_path else None
            )
            
            self.git = GitConfig(
                
                timeout=config_data['git']['timeout'],
                user_name=config_data['git']['user_name'],
                user_email=config_data['git']['user_email'],
                gitignore=config_data['git']['gitignore']  
            )
            
        except KeyError as e:
            raise ValueError(f"Missing required configuration key: {e}")
        
        except Exception as e:
            raise ValueError(f"Error creating configuration objects: {e}")
        
        
    def _build_git_remote( self ) -> None:
                
        github_token = os.getenv('GITHUB_TOKEN')
        github_username = os.getenv('GITHUB_USERNAME')
        github_repository = os.getenv('GITHUB_REPOSITORY')
        
        missing_vars = []
        if not github_token:
            missing_vars.append('GITHUB_TOKEN')
        if not github_username:
            missing_vars.append('GITHUB_USERNAME')
        if not github_repository:
            missing_vars.append('GITHUB_REPOSITORY')
            
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
        
        self.git_remote = f"https://{github_token}@github.com/{github_username}/{github_repository}.git"
    
    
    def validate( self ) -> None:


        if not self.vault.path.exists():
            raise ValueError(f"Vault path does not exist: {self.vault.path}")
        
        if self.sync.mode not in ['interval', 'on_close']:
            raise ValueError(f"Invalid sync mode: {self.sync.mode}. Must be 'interval' or 'on_close'")
        
        if self.sync.interval_minutes <= 0:
            raise ValueError("Sync interval must be positive")
            
        if self.backup.enabled and not self.backup.directory:
            raise ValueError("Backup directory must be set when backups are enabled")
            
        if not self.git.user_name:
            raise ValueError("Git user name must be set")
            
        if not self.git.user_email:
            raise ValueError("Git user email must be set")
            
        if self.git.timeout <= 0:
            raise ValueError("Git timeout must be positive")


class ConfigSetup:
    
    
    def __init__( self ):
        
        current_dir = Path(__file__).parent.parent.parent.absolute()
        self.base_dir = current_dir
        self.config_file = self.base_dir / "config.yaml"
        self.env_file = self.base_dir / ".env"
        
        
    def handle_setup( self, args ) -> None:
        
        
        self._apply_args_setup(args)
        
        
    def _apply_args_setup( self, args ) -> None:
        
        
        config_data = self._load_existing_config()
        env_data = self._load_existing_env()
        
        config_updated = False
        env_updated = False
        
        # Apply vault configuration
        if args.vault_path:
            
            config_data['vault']['path'] = args.vault_path
            config_updated = True
            print(f"[+] Vault path set to: {args.vault_path}")
            
        # Apply sync configuration
        if args.sync_mode:
            
            if args.sync_mode in ['on_close', 'interval']:
                config_data['sync']['mode'] = args.sync_mode
                config_updated = True
                print(f"[+] Sync mode set to: {args.sync_mode}")
            else:
                print(f"[x] Invalid sync mode: {args.sync_mode}. Use 'on_close' or 'interval'")
                return
            
        if args.interval_time is not None:
            
            if args.interval_time > 0:
                config_data['sync']['interval_minutes'] = args.interval_time
                config_updated = True
                print(f"[+] Interval time set to: {args.interval_time} minutes")
            else:
                print("[x] Interval time must be greater than 0")
                return
            
        # Apply backup configuration
        if args.backup:
            
            if args.backup.lower() in ['enable', 'enabled', 'true', '1']:
                config_data['backup']['enabled'] = True
                config_updated = True
                print("[+] Backup enabled")
                
            elif args.backup.lower() in ['disable', 'disabled', 'false', '0']:
                config_data['backup']['enabled'] = False
                config_updated = True
                print("[+] Backup disabled")
                
            else:
                print(f"[x] Invalid backup value: {args.backup}. Use 'enable' or 'disable'")
                return
            
        if args.backup_dir:
            
            backup_path = Path(args.backup_dir)

            backup_path.mkdir(parents=True, exist_ok=True)
            
            config_data['backup']['directory'] = str(backup_path)
            config_updated = True
            print(f"[+] Backup directory set to: {backup_path}")
            
        if args.max_backups is not None:
            
            if args.max_backups > 0:
                config_data['backup']['max_backups'] = args.max_backups
                config_updated = True
                print(f"[+] Maximum backups set to: {args.max_backups}")
            else:
                print("[x] Maximum backups must be greater than 0")
                return
            
        # Apply notification configuration
        if args.notification:
            
            if args.notification.lower() in ['enable', 'enabled', 'true', '1']:
                config_data['notification']['enabled'] = True
                config_updated = True
                print("[+] Notifications enabled")
                
            elif args.notification.lower() in ['disable', 'disabled', 'false', '0']:
                config_data['notification']['enabled'] = False
                config_updated = True
                print("[+] Notifications disabled")
                
            else:
                print(f"[x] Invalid notification value: {args.notification}. Use 'enable' or 'disable'")
                return
            
        if args.git_username:
            
            config_data['git']['user_name'] = args.git_username
            config_updated = True
            print(f"[+] Git username set to: {args.git_username}")
            
        if args.git_email:
            
            config_data['git']['user_email'] = args.git_email
            config_updated = True
            print(f"[+] Git email set to: {args.git_email}")
            

        if args.github_token:
            
            env_data['GITHUB_TOKEN'] = args.github_token
            env_updated = True
            print("[+] GitHub token updated")
            
        if args.github_username:
            
            env_data['GITHUB_USERNAME'] = args.github_username
            env_updated = True
            print(f"[+] GitHub username set to: {args.github_username}")
            
        if args.github_repository:
            
            env_data['GITHUB_REPOSITORY'] = args.github_repository
            env_updated = True
            print(f"[+] GitHub repository set to: {args.github_repository}")
            
        if config_updated:
            self._save_config(config_data)
            
        if env_updated:
            self._save_env(env_data)
            
        if not config_updated and not env_updated:
            print("[*] No configuration changes to apply")
            
            
    def _load_existing_config( self ) -> Dict[str, Any]:
        
        # Load existing config or return default template
        
        if self.config_file.exists():
            
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f)
            except Exception as e:
                print(f"[!] Warning: Could not load existing config: {e}")
                
        # Default configuration template
        return {
            
            'vault': {
                'path': '',
                'branch': 'main'
            },
            
            'sync': {
                'mode': 'on_close',
                'interval_minutes': 2,
                'process_name': 'Obsidian.exe'
            },
            
            'backup': {
                'enabled': True,
                'directory': '',
                'max_backups': 2
            },
            
            'logging': {
                'file': 'VaultSync.log',
                'level': 'INFO'
            },
            
            'notification': {
                'enabled': True,
                'timeout': 3,
                'icon_path': None
            },
            
            'git': {
                'timeout': 120,
                'user_name': '',
                'user_email': '',
                'gitignore': {
                    'obsidian': [],
                    'system': [
                        '.DS_Store',
                        'Thumbs.db',
                        '*.tmp',
                        '*.lock',
                        '*.swp',
                        '*~'
                    ],
                    'directories': [
                        '.trash/',
                        '__pycache__/',
                        '.vscode/',
                        '.idea/'
                    ],
                    'custom': []
                }
            }
        }
        
        
    def _load_existing_env( self ) -> Dict[str, str]:
                
        env_data = {}
        
        if self.env_file.exists():
            
            try:
                with open(self.env_file, 'r', encoding='utf-8') as f:
                    
                    for line in f:
                        
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            
                            key, value = line.split('=', 1)
                            env_data[key.strip()] = value.strip()
            except Exception as e:
                print(f"[!] Warning: Could not load existing .env: {e}")
                        
        return env_data
    
    
    def _save_config( self, config_data: Dict[str, Any] ) -> None:
                
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                
                yaml.dump(
                    
                    config_data, 
                    f, 
                    default_flow_style=False, 
                    sort_keys=False, 
                    indent=2,
                    allow_unicode=True
                )
                
            print(f"[+] Configuration saved to: {self.config_file}")
            
        except Exception as e:
            print(f"[x] Error saving configuration: {e}")
        
        
    def _save_env( self, env_data: Dict[str, str] ) -> None:
        
        
        try:
            with open(self.env_file, 'w', encoding='utf-8') as f:
                
                f.write("# Environment Variables - KEEP THIS FILE PRIVATE!\n")
                
                for key, value in env_data.items():
                    f.write(f"{key}={value}\n")
                    
            print(f"[+] Environment file saved to: {self.env_file}")
            
        except Exception as e:
            print(f"[x] Error saving environment file: {e}")