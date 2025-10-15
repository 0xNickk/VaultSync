#!/usr/bin/env python3
"""
Main service handler for VaultSync.
Coordinates process management, autorun, and configuration validation.
"""

import sys
from pathlib import Path

# Use absolute imports since src is added to sys.path
from sync_core import VaultSync
from service.process_manager import ProcessManager
from service.autorun_manager import AutorunManager
from service.config_validator import ConfigValidator
from service.config_display import ConfigDisplay


class ServiceHandler:

    def __init__( self ):

        self.base_dir = Path(__file__).parent.parent.parent.absolute()

        self.process_manager  = ProcessManager(self.base_dir)
        self.autorun_manager  = AutorunManager(self.base_dir)
        self.config_validator = ConfigValidator(self.base_dir)
        self.config_display   = ConfigDisplay(self.base_dir)

    def run_background( self ) -> None:

        if not self.config_validator.validate_configuration():
            return

        if self.process_manager.is_running():
            print("\n[*] VaultSync is already running in background")
            self.check_status()
            return

        self.process_manager.start_background()

    def run_normal( self ) -> None:

        if not self.config_validator.validate_configuration():
            return

        if self.process_manager.is_running():
            print("\n[*] VaultSync is already running in background")
            print("[+] Use --stop to stop it first, then --run\n")
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

    def stop_background( self ) -> None:

        self.process_manager.stop_background()

    def enable_autorun( self ) -> None:

        if not self.config_validator.validate_configuration():
            return

        self.autorun_manager.enable()

    def disable_autorun( self ) -> None:

        self.autorun_manager.disable()

    def is_autorun_enabled( self ) -> bool:

        return self.autorun_manager.is_enabled()

    def get_autorun_command( self ) -> str:

        return self.autorun_manager.get_command()

    def is_running( self ) -> bool:

        return self.process_manager.is_running()

    def check_status( self ) -> None:

        print("\n[+] VaultSync Status")

        self.process_manager.check_status()

        if sys.platform == "win32":
            print("[+] Autorun Status")

            if self.autorun_manager.is_enabled():

                info = self.autorun_manager.get_status_info()
                print("[+] Auto-run: ENABLED")
                print(f"[+] Registry: {info['registry_path']}")
            else:
                print("[+] Auto-run: DISABLED")

            print()

    def check_requirements( self ) -> bool:

        return self.config_validator.check_requirements()

    def show_config(self) -> None:

        self.config_display.show_config()


if __name__ == "__main__":
    handler = ServiceHandler()
