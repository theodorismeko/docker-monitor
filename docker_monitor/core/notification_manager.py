"""Notification management and coordination."""

from typing import Dict, Any, List

from .cooldown_manager import CooldownManager
from .notification_formatter import NotificationFormatter
from ..integrations.slack import SlackNotifier
from ..utils.logging_config import get_logger

logger = get_logger(__name__)


class NotificationManager:
    """Coordinates notifications using formatter, cooldown manager, and slack notifier."""
    
    def __init__(self, slack_notifier: SlackNotifier, cooldown_seconds: int = 120):
        """
        Initialize notification manager.
        
        Args:
            slack_notifier: SlackNotifier instance
            cooldown_seconds: Cooldown period in seconds (default: 120)
        """
        self.slack_notifier = slack_notifier
        self.cooldown_manager = CooldownManager(cooldown_seconds)
        self.formatter = NotificationFormatter()
    
    def process_changes(self, changes: List[Dict[str, Any]]) -> None:
        """
        Process detected changes and send notifications as needed.
        
        Args:
            changes: List of detected changes
        """
        if not changes:
            logger.info("No changes detected")
            return
        
        logger.info(f"Processing {len(changes)} changes")
        
        for change in changes:
            container_name = change.get('container_name', change.get('container_info', {}).get('name', change.get('container_id', 'unknown')[:12]))
            
            # Log restart events for debugging first
            if change['type'] == 'container_restarted':
                self._log_restart_event(change)
            
            # Check if we should notify
            should_notify = self._should_notify(change)
            logger.info(f"Should notify for {change['type']} on {container_name}: {should_notify}")
            
            if should_notify:
                self._send_notification(change)
            else:
                logger.info(f"Skipped notification for {change['type']} on {container_name}")
                # Debug why notification was skipped
                container_key = change.get('container_name', change.get('container_id', ''))
                if self.cooldown_manager.is_in_cooldown(container_key):
                    logger.info(f"  Reason: Container {container_name} is in cooldown period")
                else:
                    logger.info(f"  Reason: Change type {change['type']} not configured for notification")
    
    def _should_notify(self, change: Dict[str, Any]) -> bool:
        """
        Determine if a change should trigger a notification.
        
        Args:
            change: Change information dictionary
            
        Returns:
            True if notification should be sent, False otherwise
        """
        container_key = change.get('container_name', change.get('container_id', ''))
        change_type = change.get('type', '')
        
        # Always notify for critical changes regardless of cooldown
        critical_changes = [
            'container_removed',
            'container_failed',
            'container_unhealthy',
            'container_stopped',  # Container stops are critical
            'container_restarted',  # Restarts are important and should bypass cooldown
            'container_started'     # Starts are important and should bypass cooldown
        ]
        
        if change_type in critical_changes:
            return True
        
        # Check cooldown for other types of changes
        if self.cooldown_manager.is_in_cooldown(container_key):
            logger.info(f"Skipping notification for {container_key[:12]} - in cooldown period")
            return False
        
        # Notify for status changes but not for routine running containers
        if change.get('type') == 'state_change':
            previous_status = change.get('previous_status', '')
            current_status = change.get('current_status', '')
            
            # Don't notify for containers that are just continuing to run
            if previous_status == 'running' and current_status == 'running':
                return False
            
            # Always notify for critical state changes (running -> stopped/exited/dead)
            if previous_status == 'running' and current_status in ['exited', 'stopped', 'dead']:
                return True
            
            return True
        
        # Default to notify for other changes
        return True
    
    def _send_notification(self, change: Dict[str, Any]) -> None:
        """
        Send notification for a change.
        
        Args:
            change: Change information dictionary
        """
        try:
            container_key = change.get('container_name', change.get('container_id', ''))
            container_name = change.get('container_name', change.get('container_info', {}).get('name', container_key[:12]))
            
            # Create notification
            notification = self.formatter.create_notification(change)
            
            # Combine description and details for the message
            message_text = notification['description']
            if notification.get('details'):
                message_text += f"\n\n{notification['details']}"
            
            success = self.slack_notifier.send_custom_message(
                title=notification['title'],
                message=message_text,
                color=notification['color']
            )
            
            if success:
                logger.info(f"Sent notification for {change['type']}: {notification['title']}")
                # Update cooldown using container name as key
                self.cooldown_manager.update_cooldown(container_key)
            else:
                logger.error(f"Failed to send notification for {change['type']}")
                
        except Exception as e:
            logger.error(f"Error sending notification: {e}")
    
    def _log_restart_event(self, change: Dict[str, Any]) -> None:
        """Log restart event details for debugging."""
        container_name = change.get('container_name', change.get('container_info', {}).get('name', change.get('container_id', 'unknown')[:12]))
        restart_type = change.get('restart_type', 'unknown')
        current_status = change['current_status']
        
        if restart_type == 'automatic':
            previous_count = change['previous_restart_count']
            current_count = change['current_restart_count']
            logger.info(
                f"🔄 AUTO-RESTART DETECTED: {container_name} "
                f"(restart count: {previous_count} → {current_count}, "
                f"status: {current_status})"
            )
        elif restart_type == 'manual':
            logger.info(
                f"🔄 MANUAL RESTART DETECTED: {container_name} "
                f"(started time changed, status: {current_status})"
            )
        else:
            logger.info(
                f"🔄 RESTART DETECTED: {container_name} "
                f"(type: {restart_type}, status: {current_status})"
            ) 