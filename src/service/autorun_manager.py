#!/usr/bin/env python3
"""
Windows autorun management for VaultSync.
Handles automatic startup via Windows Registry.
"""

import sys
import winreg
from pathlib import Path
from typing import Optional


class AutorunManager:

    # Manages VaultSync auto-run on Windows boot using Windows Registry.

    def __init__( self, base_dir: Path ):

        self.base_dir = base_dir
        self.startup_key = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"
        self.app_name = "VaultSync"

    def enable( self ) -> bool:

        if sys.platform != "win32":
            print("[x] Auto-run is only supported on Windows")
            return False

        try:
            print("\n[+] Enabling VaultSync auto-run on Windows boot...")

            main_script = self.base_dir / "VaultSync.py"

            # Hide console window
            python_executable = sys.executable
            if python_executable.endswith('python.exe'):
                pythonw_executable = python_executable.replace('python.exe', 'pythonw.exe')
            else:
                pythonw_executable = python_executable

            startup_command = f'"{pythonw_executable}" "{main_script}" --background'

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
            print(f"[+] Registry key: {full_key}")
            print("[+] VaultSync will now run silently when Windows boots")
            print("[+] Use --disable-autorun to remove auto-run\n")

            return True

        except PermissionError:
            print("[x] Permission denied. Run as administrator to enable auto-run")
            return False

        except Exception as e:
            print(f"[x] Failed to enable auto-run: {e}")
            return False

    def disable( self ) -> bool:

        if sys.platform != "win32":
            print("[x] Auto-run is only supported on Windows")
            return False

        try:
            if not self.is_enabled():
                print("\n[*] VaultSync auto-run is not enabled\n")
                return True

            print("\n[+] Disabling VaultSync auto-run...")
            print(f"[*] Removing registry key (HKEY_CURRENT_USER\\{self.startup_key}\\{self.app_name})")

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

    def is_enabled( self ) -> bool:

        if sys.platform != "win32":
            return False

        try:
            with winreg.OpenKey(

                winreg.HKEY_CURRENT_USER,
                self.startup_key,
                0,
                winreg.KEY_READ

            ) as key:
                try:
                    value, _ = winreg.QueryValueEx(key, self.app_name)
                    return True
                except FileNotFoundError:
                    return False

        except Exception:
            return False

    def get_command( self ) -> Optional[str]:

        if sys.platform != "win32":
            return None

        try:
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                self.startup_key,
                0,
                winreg.KEY_READ
            ) as key:
                try:
                    value, _ = winreg.QueryValueEx(key, self.app_name)
                    return value
                except FileNotFoundError:
                    return None
        except Exception:
            return None

    def get_status_info( self ) -> dict:

        return {
            'enabled': self.is_enabled(),
            'command': self.get_command(),
            'registry_path': f"HKEY_CURRENT_USER\\{self.startup_key}\\{self.app_name}"
        }

