#!/usr/bin/env python3

import time
import psutil
from typing import Set, Optional
from .logger import Logger


class ProcessMonitor:

        
    def __init__( self, process_name: str, logger: Logger ):
        
        self.process_name = process_name
        self.logger = logger
        
        # Process caching for performance
        self._cached_pids: Set[int] = set()
        self._last_full_scan = 0
        self._full_scan_interval = 30  
        self._last_check_result = False
        self._last_check_time = 0
        self._check_cache_duration = 2  
        
        self.logger.debug(f"[+] Process monitor initialized for: {process_name}")
    

    def is_running( self ) -> bool:

        
        current_time = time.time()
        
        # Use cached result if recent enough
        if current_time - self._last_check_time < self._check_cache_duration:
            return self._last_check_result
        
        try:
            
            # First, check cached PIDs for quick validation
            if self._cached_pids:
                
                alive_pids = self._validate_cached_pids()
                
                if alive_pids:
                    
                    self._cached_pids = alive_pids
                    self._last_check_result = True
                    self._last_check_time = current_time
                    return True
                
                # Clear cache if no processes found
                self._cached_pids.clear()
            
            # Perform full scan if cache is empty or enough time has passed
            should_full_scan = (
                
                not self._cached_pids or 
                current_time - self._last_full_scan > self._full_scan_interval
            )
            
            if should_full_scan:
                
                found_pids = self._full_process_scan()
                self._last_full_scan = current_time
                
                if found_pids:
                    
                    self._cached_pids = found_pids
                    self._last_check_result = True
                    self._last_check_time = current_time
                    return True
            
            # No processes found
            self._last_check_result = False
            self._last_check_time = current_time
            return False
                
        except Exception as e:
            
            self.logger.warning(f"[!] Process monitoring error: {e}")

            self._last_check_result = False
            self._last_check_time = current_time
            return False


    def _validate_cached_pids( self ) -> Set[int]:
        
        
        alive_pids = set()
        
        for pid in self._cached_pids.copy():
            
            try:
                
                if psutil.pid_exists(pid):
                    
                    proc = psutil.Process(pid)
                
                    if proc.name() == self.process_name:
                        alive_pids.add(pid)
                        
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                
                # Process no longer exists or accessible
                pass
        
        return alive_pids


    def _full_process_scan( self ) -> Set[int]:
        
        # Perform a full scan of all processes to find matches
                
        found_pids = set()
        
        try:
            
            for proc in psutil.process_iter(['pid', 'name'], ad_value=None):
                
                try:
                    
                    proc_info = proc.info
                    
                    if proc_info['name'] == self.process_name:
                        
                        found_pids.add(proc_info['pid'])
                        self.logger.debug(f"[+] Found {self.process_name} process: PID {proc_info['pid']}")
                        
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    
                    continue
                    
        except Exception as e:
            
            self.logger.warning(f"[!] Error during full process scan: {e}")
            
        return found_pids


    def get_process_info( self ) -> Optional[dict]:
        
        
        if not self.is_running():
            return None
            
        try:
            
            if self._cached_pids:
                
                pid = next(iter(self._cached_pids))
                proc = psutil.Process(pid)
                
                return {
                    
                    'pid': pid,
                    'name': proc.name(),
                    'status': proc.status(),
                    'create_time': proc.create_time(),
                    'memory_mb': proc.memory_info().rss / 1024 / 1024,
                    'cpu_percent': proc.cpu_percent()
                }
                
        except Exception as e:
            
            self.logger.warning(f"[!] Error getting process info: {e}")
            
        return None


    def wait_for_process_start( self, timeout: int = 60, check_interval: float = 1.0 ) -> bool:
        
        
        self.logger.info(f"[+] Waiting for {self.process_name} to start (timeout: {timeout}s)")
        
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            
            if self.is_running():
                
                self.logger.info(f"[+] {self.process_name} started")
                return True
                
            time.sleep(check_interval)
        
        self.logger.warning(f"[!] Timeout waiting for {self.process_name} to start")
        return False


    def wait_for_process_stop( self, timeout: int = 60, check_interval: float = 1.0 ) -> bool:
        
        
        self.logger.info(f"[+] Waiting for {self.process_name} to stop (timeout: {timeout}s)")
        
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            
            if not self.is_running():
                
                self.logger.info(f"[+] {self.process_name} stopped")
                return True
                
            time.sleep(check_interval)
        
        self.logger.warning(f"[!] Timeout waiting for {self.process_name} to stop")
        return False


    def clear_cache( self ) -> None:
                
        self._cached_pids.clear()
        self._last_full_scan = 0
        self._last_check_time = 0
        self.logger.debug("[+] Process monitor cache cleared")