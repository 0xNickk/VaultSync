#!/usr/bin/env python3

import logging
import logging.handlers
from pathlib import Path
from typing import Optional


class Logger:


    def __init__( self, log_file: str, level: str = "INFO", service_mode: bool = False ):
        
        self.logger = logging.getLogger("VaultSync")
        self.logger.setLevel(getattr(logging, level.upper()))
        self.service_mode = service_mode

        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        formatter = logging.Formatter(
            
            '[%(asctime)s] [%(levelname)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        if not service_mode:
            
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            console_handler.setLevel(logging.INFO)
            self.logger.addHandler(console_handler)
        
        file_handler = logging.handlers.RotatingFileHandler(
            
            log_file, 
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        
        self.logger.propagate = False
    
    
    def debug( self, message: str ) -> None:

        self.logger.debug(message)
    
    
    def info( self, message: str ) -> None:

        self.logger.info(message)
    
    
    def warning( self, message: str ) -> None:

        self.logger.warning(message)
    
    
    def error( self, message: str ) -> None:

        self.logger.error(message)
        
        
    def critical( self, message: str ) -> None:

        self.logger.critical(message)