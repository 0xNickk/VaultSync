#!/usr/bin/env python3

import time
from typing import Optional, Dict, Any
from pathlib import Path
from config.config_manager import NotificationConfig
from .logger import Logger

try:
    from plyer import notification
    PLYER_AVAILABLE = True
except ImportError:
    PLYER_AVAILABLE = False


class NotificationManager:


    def __init__( self, config: NotificationConfig, logger: Logger ):

        self.config = config
        self.logger = logger
        
        self._last_notification_time = 0
        self._min_notification_interval = 5 
        self._notification_count = 0
        
        self._recent_notifications: Dict[str, float] = {}
        self._duplicate_timeout = 30

        if not PLYER_AVAILABLE:
            self.logger.warning("[!] Plyer not available - notifications disabled")
            self.logger.warning("[!] Install with: pip install plyer")

        elif self.config.enabled:
            self.logger.info("[+] Notification system initialized and enabled")

        else:
            self.logger.info("[+] Notification system initialized but disabled in config")


    def send(self, success: bool, message: Optional[str] = None, force: bool = False) -> bool:

        if not self.config.enabled:
            self.logger.debug("[*] Notifications disabled in configuration")
            return False

        if not PLYER_AVAILABLE:
            self.logger.debug("[*] Plyer not available - notification skipped")
            return False
        
        try:

            title = "🔄 VaultSync" if success else "❌ VaultSync Error"
            msg = message or ("Sync completed successfully!" if success else "Sync failed - check logs")
            
            current_time = time.time()
            
            if not force and current_time - self._last_notification_time < self._min_notification_interval:
                self.logger.debug(f"[*] Notification rate limited ({self._min_notification_interval}s interval)")
                return False
            
            notification_key = f"{title}:{msg}"
            
            if not force and notification_key in self._recent_notifications:

                time_since_last = current_time - self._recent_notifications[notification_key]
                if time_since_last < self._duplicate_timeout:
                    self.logger.debug(f"[*] Duplicate notification suppressed (sent {time_since_last:.1f}s ago)")
                    return False
            
            notification_kwargs = {
                'title': title,
                'message': msg,
                'app_name': "VaultSync",
                'timeout': self.config.timeout
            }

            if self.config.icon_path and self.config.icon_path.exists():
                notification_kwargs['app_icon'] = str(self.config.icon_path)

            # Send the notification
            self.logger.info(f"[+] Notification: {msg}")
            notification.notify(**notification_kwargs)

            self._last_notification_time = current_time
            self._recent_notifications[notification_key] = current_time
            self._notification_count += 1

            self._cleanup_notification_history(current_time)

            return True

        except Exception as e:
            self.logger.error(f"[x] Notification error: {e}")
            import traceback
            self.logger.debug(traceback.format_exc())
            return False


    def send_startup( self ) -> bool:
        
        # Send startup notification
        
        return self.send(
            
            success=True, 
            message="VaultSync started - monitoring your vault",
            force=True
        )


    def send_shutdown( self ) -> bool:
        
        # Send shutdown notification
             
        return self.send(
            
            success=True, 
            message="VaultSync stopped",
            force=True
        )


    def send_error( self, error_message: str ) -> bool:
        
        # Send error notification
        
        return self.send(
            
            success=False, 
            message=f"Error: {error_message}",
            force=True
        )


    def send_sync_completed( self, changes_count: int = 0 ) -> bool:
        
        # Send sync completed notification
        
        if changes_count > 0:
            message = f"Sync completed - {changes_count} changes synced"
        else:
            message = "Sync completed - no changes"
            
        return self.send(success=True, message=message)


    def _cleanup_notification_history( self, current_time: float ) -> None: 
        
        cutoff_time = current_time - self._duplicate_timeout
        
        # Remove old entries
        keys_to_remove = [
            
            key for key, timestamp in self._recent_notifications.items() 
            if timestamp < cutoff_time
        ]
        
        for key in keys_to_remove:
            del self._recent_notifications[key]


    def get_stats( self ) -> Dict[str, Any]:
        
        
        return {
            
            'enabled': self.config.enabled,
            'plyer_available': PLYER_AVAILABLE,
            'total_sent': self._notification_count,
            'recent_count': len(self._recent_notifications),
            'timeout': self.config.timeout,
            'min_interval': self._min_notification_interval
        }