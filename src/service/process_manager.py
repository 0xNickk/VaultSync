#!/usr/bin/env python3
"""
Process management for VaultSync background service.
Handles starting, stopping, and monitoring the sync process.
"""

import sys
import os
import subprocess
import psutil
import time
from pathlib import Path
from datetime import datetime
from typing import Optional


class ProcessManager:

    def __init__( self, base_dir: Path ):

        self.base_dir = base_dir
        self.src_dir = self.base_dir / "src"
        self.sync_script = self.src_dir / "sync.py"
        self.pid_file = self.base_dir / ".pid"

    def start_background( self ) -> bool:

        if self.is_running():
            print("\n[*] VaultSync is already running in background")
            return False

        print("\n[+] Starting VaultSync in background...")

        if not self.sync_script.exists():
            print(f"[-] Sync script not found: {self.sync_script}")
            return False

        try:
            if sys.platform == "win32":
                return self._start_windows_background()
            else:
                return self._start_unix_background()

        except Exception as e:
            print(f"[x] Error starting background process: {e}")
            return False

    def _start_windows_background( self ) -> bool:

        python_executable = sys.executable
        if python_executable.endswith('python.exe'):
            pythonw_executable = python_executable.replace('python.exe', 'pythonw.exe')

            if not Path(pythonw_executable).exists():
                print("[!] Warning: pythonw.exe not found, using python.exe (console may appear)")
                pythonw_executable = python_executable
        else:
            pythonw_executable = python_executable

        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE

        # Start completely detached process with no console
        process = subprocess.Popen(
            [pythonw_executable, str(self.sync_script)],
            cwd=self.base_dir,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL,
            startupinfo=startupinfo,
            creationflags=(
                subprocess.DETACHED_PROCESS |
                subprocess.CREATE_NEW_PROCESS_GROUP |
                subprocess.CREATE_NO_WINDOW
            ),
            close_fds=True
        )

        return self._finalize_startup()

    def _start_unix_background( self ) -> bool:


        process = subprocess.Popen(
            [sys.executable, str(self.sync_script)],
            cwd=self.base_dir,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL,
            preexec_fn=os.setsid,
            close_fds=True
        )

        return self._finalize_startup()

    def _finalize_startup( self ) -> bool:

        # Wait a moment to allow process to start
        time.sleep(3)

        vault_pid = self.find_vault_process()

        if vault_pid:

            self.pid_file.write_text(str(vault_pid))
            print(f"[+] VaultSync started in background!")
            print(f"[+] PID: {vault_pid}")
            print("[+] Logs: VaultSync.log\n")
            return True

        else:
            print("[x] Failed to run VaultSync - process not found")
            print("[+] Check VaultSync.log for details")
            return False

    def find_vault_process( self ) -> Optional[int]:

        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if proc.info['name']:
                        proc_name = proc.info['name'].lower()

                        if 'python' in proc_name or 'pythonw' in proc_name:
                            cmdline = proc.info['cmdline']

                            if cmdline and any('sync.py' in str(arg) for arg in cmdline):
                                return proc.info['pid']
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except Exception:
            pass

        return None

    def stop_background(self) -> bool:

        if not self.is_running():
            print("[*] VaultSync is not running")
            return False

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
            return True

        except Exception as e:
            print(f"[x] Error stopping process: {e}")
            return False

    def is_running(self) -> bool:

        if not self.pid_file.exists():
            return False

        try:
            pid = int(self.pid_file.read_text().strip())

            if psutil.pid_exists(pid):
                process = psutil.Process(pid)
                proc_name = process.name().lower()

                return process.is_running() and ('python' in proc_name or 'pythonw' in proc_name)
            else:

                self.pid_file.unlink()
                return False

        except (ValueError, psutil.NoSuchProcess, psutil.AccessDenied):
            return False

    def get_process_info( self ) -> Optional[dict]:

        if not self.is_running():
            return None

        try:
            pid = int(self.pid_file.read_text().strip())
            process = psutil.Process(pid)

            return {
                'pid': pid,
                'create_time': datetime.fromtimestamp(process.create_time()),
                'memory_mb': process.memory_info().rss / 1024 / 1024,
                'status': process.status()
            }
        except Exception:
            return None

    def check_status(self) -> None:

        print("\n[+] VaultSync Process Status")

        if self.is_running():

            info = self.get_process_info()
            if info:
                print("[+] Status: RUNNING")
                print(f"[+] PID: {info['pid']}")
                print(f"[+] Started: {info['create_time'].strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"[+] Memory: {info['memory_mb']:.1f} MB")
            else:
                print("[+] Status: RUNNING (details unavailable)")
        else:
            print("[+] Status: NOT RUNNING")

        log_file = self.base_dir / "VaultSync.log"
        if log_file.exists():

            print(f"\n[+] Log file: {log_file}")
            print(f"[+] Log size: {log_file.stat().st_size} bytes")
            mod_time = datetime.fromtimestamp(log_file.stat().st_mtime)
            print(f"[+] Last modified: {mod_time.strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            print("\n[+] Log file: Not found")

        print()
