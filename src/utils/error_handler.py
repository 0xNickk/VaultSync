#!/usr/bin/env python3

import sys
import traceback
from typing import Optional, Callable, Any
from functools import wraps
from .logger import Logger


class VaultSyncError(Exception):
    # Base class for VaultSync errors
    pass


class ConfigurationError(VaultSyncError):
    # Configuration related errors
    pass


class GitOperationError(VaultSyncError):
    # Git operation errors
    pass


class BackupError(VaultSyncError):
    # Backup operation errors
    pass


class ProcessMonitorError(VaultSyncError):
    # Process monitoring errors
    pass


class ErrorHandler:
        
    def __init__( self, logger: Logger ):
        
        self.logger = logger
        self.error_count = 0
        self.last_error: Optional[Exception] = None
        
        
    def handle_error( self, error: Exception, context: str = "", fatal: bool = False ) -> bool:
                
        self.error_count += 1
        self.last_error = error
        
        error_msg = f"[x] Error in {context}: {str(error)}" if context else f"[x] Error: {str(error)}"
        
        if fatal:
            
            self.logger.critical(error_msg)
            self.logger.critical(f"[x] Stack trace: {traceback.format_exc()}")
            
        else:
            
            self.logger.error(error_msg)
            self.logger.debug(f"[!] Stack trace: {traceback.format_exc()}")
        
        return not fatal


def retry_on_error( max_retries: int = 3, delay: float = 1.0, exceptions: tuple = (Exception,) ):
    
    
    def decorator( func: Callable ) -> Callable:
        
        @wraps(func)
        def wrapper( *args, **kwargs ) -> Any:
            
            last_exception = None
            
            for attempt in range(max_retries + 1):
                
                try:
                    
                    return func(*args, **kwargs)
                    
                except exceptions as e:
                    
                    last_exception = e
                    
                    if attempt < max_retries:
                        
                        logger = None
                        for arg in args:
                            if hasattr(arg, 'logger'):
                                logger = arg.logger
                                break
                        
                        if logger:
                            logger.warning(f"[!] Attempt {attempt + 1} failed, retrying in {delay}s: {e}")
                        
                        import time
                        time.sleep(delay)
                        
                    else:
                        
                        if logger:
                            logger.error(f"[x] All {max_retries + 1} attempts failed")
                        
                        raise last_exception
            
            raise last_exception
            
        return wrapper
        
    return decorator


def safe_execute( func: Callable, logger: Logger, context: str = "", default_return: Any = None ) -> Any:
        
    try:
        
        return func()
        
    except Exception as e:
        
        error_handler = ErrorHandler(logger)
        error_handler.handle_error(e, context)
        
        return default_return