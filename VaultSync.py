#!/usr/bin/env python3
"""
Author: 0xNickk
Version: 2.1.0
License: MIT
"""

import sys
import argparse
from pathlib import Path


current_dir = Path(__file__).parent.absolute()
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))

from service_handler import ServiceHandler
from config.config_manager import ConfigSetup


def main():
        

    parser = argparse.ArgumentParser(
        
        description="VaultSync - Obsidian Vault Synchronization Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
        """
        
    )
    parser.add_argument('--version', action='version', version='%(prog)s 2.1.0')

    # Control commands group
    control_group = parser.add_argument_group('Control Commands')
    control_group.add_argument('--background', action='store_true',
                       help='Run VaultSync as background process (no console)')
    control_group.add_argument('--run', action='store_true',
                       help='Run VaultSync normally (showing console output)')
    control_group.add_argument('--stop', action='store_true',
                       help='Stop VaultSync background process')
    control_group.add_argument('--status', action='store_true',
                       help='Check VaultSync process status and if auto-run is enabled')
    control_group.add_argument('--config', action='store_true',
                       help='Show VaultSync configuration')
    control_group.add_argument('--check', action='store_true',
                       help='Check configuration and requirements')
    control_group.add_argument('--enable-autorun', action='store_true',
                       help='Enable VaultSync to run automatically on Windows boot')
    control_group.add_argument('--disable-autorun', action='store_true',
                       help='Disable VaultSync auto-run on Windows boot')

    # Configuration setup commands group
    setup_group = parser.add_argument_group('Configuration Commands', 
                                           'Argument syntax: --argument <Value>')
    
    
    setup_group.add_argument('--vault-path', metavar='PATH',
                       help='Set vault path')
    setup_group.add_argument('--sync-mode', metavar='MODE',
                       help='Set sync mode: on_close or interval')
    setup_group.add_argument('--interval-time', type=int, metavar='MIN',
                       help='  Set interval time in minutes (only for interval mode)')
    setup_group.add_argument('--backup', metavar='',
                       help='Enable or disable backup functionality: enable or disable',)
    setup_group.add_argument('--backup-dir', metavar='PATH',
                       help='Set backup directory path')
    setup_group.add_argument('--max-backups', type=int, metavar='NUM',
                       help='Set maximum number of backups to keep')
    setup_group.add_argument('--notification', metavar='',
                       help='Enable or disable desktop notifications: enable or disable')
    setup_group.add_argument('--git-username', metavar='',
                       help='Set Git username')
    setup_group.add_argument('--git-email', metavar='EMAIL',
                       help='Set Git email address')
    setup_group.add_argument('--github-token', metavar='TOKEN',
                       help='Set GitHub personal access token')
    setup_group.add_argument('--github-username', metavar='',
                       help='Set GitHub username')
    setup_group.add_argument('--github-repository', metavar='',
                       help='Set GitHub repository name')

    args = parser.parse_args()
    
    if len(sys.argv) == 1:
        parser.print_help()
        return
    
    try:

        handler = ServiceHandler()
        config_setup = ConfigSetup()
        
        setup_args = [
            
            args.vault_path, args.sync_mode, args.interval_time,
            args.backup, args.backup_dir, args.max_backups,
            args.notification, args.git_username, args.git_email,
            args.github_token, args.github_username, args.github_repository
            
        ]
        
        if any(setup_args):
            
            config_setup.handle_setup(args)
            return
        
        if args.background:
            handler.run_background()
            
        elif args.run:
            handler.run_normal()
            
        elif args.config:
            handler.show_config()
            
        elif args.check:
            handler.check_requirements()
            
        elif args.stop:
            handler.stop_background()
            
        elif args.status:
            handler.check_status()
            
        elif args.enable_autorun:
            handler.enable_autorun()

        elif args.disable_autorun:
            handler.disable_autorun()

        else:
            print("[x] Invalid arguments. Use --help for usage information.")

    except ImportError as e:
        
        print(f"[x] Import Error: {e}")
        print(" [*] Make sure service_handler.py exists in src/ directory")
        sys.exit(1)
        
    except Exception as e:
        print(f"[x] Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()