"""Notification cooldown management."""

import threading
from typing import Dict
from datetime import datetime

from ..utils.logging_config import get_logger

logger = get_logger(__name__)


class CooldownManager:
    """Handles notification timing logic to prevent spam."""
    
    def __init__(self, cooldown_seconds: int = 120):
        """
        Initialize cooldown manager.
        
        Args:
            cooldown_seconds: Cooldown period in seconds (default: 120)
        """
        self.cooldown_seconds = cooldown_seconds
        self._lock = threading.Lock()
        self._last_notifications: Dict[str, datetime] = {}
    
    def is_in_cooldown(self, container_id: str) -> bool:
        """
        Check if container is in notification cooldown period (thread-safe).
        
        Args:
            container_id: Container ID to check
            
        Returns:
            True if container is in cooldown, False otherwise
        """
        with self._lock:
            last_notification = self._last_notifications.get(container_id)
            if last_notification:
                time_since_last = datetime.now() - last_notification
                cooldown_remaining = self.cooldown_seconds - time_since_last.total_seconds()
                if cooldown_remaining > 0:
                    logger.debug(f"Container {container_id[:12]} in cooldown: {cooldown_remaining:.1f}s remaining")
                    return True
            return False
    
    def update_cooldown(self, container_id: str) -> None:
        """
        Update cooldown timestamp for a container (thread-safe).
        
        Args:
            container_id: Container ID to update
        """
        with self._lock:
            self._last_notifications[container_id] = datetime.now()
            logger.debug(f"Updated cooldown for {container_id[:12]} until {(datetime.now().timestamp() + self.cooldown_seconds)}")
    
    def get_cooldown_remaining(self, container_id: str) -> float:
        """
        Get remaining cooldown time for a container (thread-safe).
        
        Args:
            container_id: Container ID to check
            
        Returns:
            Remaining cooldown time in seconds, 0 if not in cooldown
        """
        with self._lock:
            last_notification = self._last_notifications.get(container_id)
            if last_notification:
                time_since_last = datetime.now() - last_notification
                cooldown_remaining = self.cooldown_seconds - time_since_last.total_seconds()
                return max(0, cooldown_remaining)
            return 0
    
    def clear_cooldown(self, container_id: str) -> None:
        """
        Clear cooldown for a container (thread-safe).
        
        Args:
            container_id: Container ID to clear
        """
        with self._lock:
            self._last_notifications.pop(container_id, None)
            logger.debug(f"Cleared cooldown for {container_id[:12]}")
    
    def get_all_cooldowns(self) -> Dict[str, float]:
        """
        Get all active cooldowns (thread-safe).
        
        Returns:
            Dictionary mapping container IDs to remaining cooldown times
        """
        with self._lock:
            cooldowns = {}
            current_time = datetime.now()
            
            for container_id, last_notification in self._last_notifications.items():
                time_since_last = current_time - last_notification
                cooldown_remaining = self.cooldown_seconds - time_since_last.total_seconds()
                if cooldown_remaining > 0:
                    cooldowns[container_id] = cooldown_remaining
            
            return cooldowns 