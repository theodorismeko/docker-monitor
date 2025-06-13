"""Real-time Docker container monitoring for immediate failure detection."""

import time
import threading
from typing import Dict, Set, Optional, Callable, Any
from datetime import datetime, timedelta

from .docker_client import DockerClient
from ..integrations.slack import SlackNotifier
from ..utils.config import Config
from ..utils.logging_config import get_logger

logger = get_logger(__name__)


class RealTimeMonitor:
    """Real-time container monitoring for immediate failure detection."""
    
    def __init__(self, config: Optional[Config] = None):
        """
        Initialize real-time monitor.
        
        Args:
            config: Configuration instance
        """
        self.config = config or Config()
        self.docker_client = DockerClient(self.config.docker_socket)
        self.slack_notifier = SlackNotifier(self.config.slack_webhook_url)
        
        # State tracking
        self.previous_states: Dict[str, str] = {}
        self.container_info: Dict[str, Dict[str, Any]] = {}
        self.monitoring = False
        self.monitor_thread: Optional[threading.Thread] = None
        
        # Configuration
        self.check_interval = 10  # seconds
        self.notification_cooldown = 300  # 5 minutes
        self.last_notifications: Dict[str, datetime] = {}
        
        logger.info("Real-time monitor initialized")
    
    def start_monitoring(self, check_interval: int = 10) -> None:
        """
        Start real-time monitoring in a background thread.
        
        Args:
            check_interval: Check interval in seconds (default: 10)
        """
        if self.monitoring:
            logger.warning("Real-time monitoring is already running")
            return
        
        self.check_interval = check_interval
        self.monitoring = True
        
        # Initialize current state
        self._update_container_states()
        
        # Start monitoring thread
        self.monitor_thread = threading.Thread(
            target=self._monitoring_loop,
            daemon=True,
            name="DockerRealTimeMonitor"
        )
        self.monitor_thread.start()
        
        logger.info(f"Real-time monitoring started (interval: {check_interval}s)")
    
    def stop_monitoring(self) -> None:
        """Stop real-time monitoring."""
        if not self.monitoring:
            logger.warning("Real-time monitoring is not running")
            return
        
        self.monitoring = False
        
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=5)
        
        logger.info("Real-time monitoring stopped")
    
    def _monitoring_loop(self) -> None:
        """Main monitoring loop that runs in background thread."""
        logger.info("Real-time monitoring loop started")
        
        while self.monitoring:
            try:
                self._check_for_changes()
                time.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(self.check_interval)
        
        logger.info("Real-time monitoring loop stopped")
    
    def _check_for_changes(self) -> None:
        """Check for container state changes and send notifications."""
        try:
            # Get current container states
            current_states = self._get_current_states()
            
            # Compare with previous states
            changes = self._detect_changes(current_states)
            
            # Send notifications for critical changes
            for change in changes:
                self._handle_state_change(change)
            
            # Update previous states
            self.previous_states = current_states.copy()
            
        except Exception as e:
            logger.error(f"Error checking for changes: {e}")
    
    def _get_current_states(self) -> Dict[str, str]:
        """Get current container states."""
        try:
            containers = self.docker_client.get_containers(
                include_stopped=True,
                name_filter=self.config.container_name_filter
            )
            
            states = {}
            self.container_info = {}
            
            for container in containers:
                container_id = container.get('id', '')
                container_name = container.get('name', '')
                status = container.get('status', 'unknown')
                
                if container_id:
                    states[container_id] = status
                    self.container_info[container_id] = container
            
            return states
            
        except Exception as e:
            logger.error(f"Error getting container states: {e}")
            return {}
    
    def _detect_changes(self, current_states: Dict[str, str]) -> list:
        """Detect significant state changes."""
        changes = []
        
        # Check for state changes in existing containers
        for container_id, current_status in current_states.items():
            previous_status = self.previous_states.get(container_id)
            
            if previous_status and previous_status != current_status:
                change = {
                    'type': 'state_change',
                    'container_id': container_id,
                    'container_info': self.container_info.get(container_id, {}),
                    'previous_status': previous_status,
                    'current_status': current_status,
                    'timestamp': datetime.now()
                }
                changes.append(change)
        
        # Check for new containers
        for container_id in current_states:
            if container_id not in self.previous_states:
                change = {
                    'type': 'container_added',
                    'container_id': container_id,
                    'container_info': self.container_info.get(container_id, {}),
                    'current_status': current_states[container_id],
                    'timestamp': datetime.now()
                }
                changes.append(change)
        
        # Check for removed containers
        for container_id in self.previous_states:
            if container_id not in current_states:
                change = {
                    'type': 'container_removed',
                    'container_id': container_id,
                    'previous_status': self.previous_states[container_id],
                    'timestamp': datetime.now()
                }
                changes.append(change)
        
        return changes
    
    def _handle_state_change(self, change: Dict[str, Any]) -> None:
        """Handle a detected state change."""
        change_type = change['type']
        container_id = change['container_id']
        container_info = change.get('container_info', {})
        container_name = container_info.get('name', container_id[:12])
        
        # Determine if this change requires notification
        should_notify = self._should_notify(change)
        
        if should_notify:
            logger.warning(f"Critical change detected: {change_type} for {container_name}")
            self._send_realtime_notification(change)
        else:
            logger.info(f"State change detected: {change_type} for {container_name}")
    
    def _should_notify(self, change: Dict[str, Any]) -> bool:
        """Determine if a change should trigger a notification."""
        change_type = change['type']
        container_id = change['container_id']
        current_status = change.get('current_status', '')
        previous_status = change.get('previous_status', '')
        
        # Check notification cooldown
        if self._is_in_cooldown(container_id):
            return False
        
        # Critical state changes that should trigger notifications
        critical_changes = [
            # Container went from running to stopped/exited
            (previous_status == 'running' and current_status in ['exited', 'stopped', 'dead']),
            # Container went from healthy to unhealthy
            (previous_status == 'running' and current_status == 'unhealthy'),
            # Container was removed unexpectedly
            (change_type == 'container_removed' and previous_status == 'running'),
            # Container restarting frequently (could indicate issues)
            (current_status == 'restarting'),
        ]
        
        return any(critical_changes)
    
    def _is_in_cooldown(self, container_id: str) -> bool:
        """Check if container is in notification cooldown period."""
        last_notification = self.last_notifications.get(container_id)
        if not last_notification:
            return False
        
        cooldown_end = last_notification + timedelta(seconds=self.notification_cooldown)
        return datetime.now() < cooldown_end
    
    def _send_realtime_notification(self, change: Dict[str, Any]) -> None:
        """Send real-time notification for critical changes."""
        try:
            container_id = change['container_id']
            container_info = change.get('container_info', {})
            container_name = container_info.get('name', container_id[:12])
            change_type = change['type']
            current_status = change.get('current_status', '')
            previous_status = change.get('previous_status', '')
            timestamp = change['timestamp']
            
            # Determine alert level and emoji
            if current_status in ['exited', 'stopped', 'dead'] or change_type == 'container_removed':
                color = "danger"
                emoji = "🚨"
                alert_level = "CRITICAL"
            elif current_status in ['restarting', 'unhealthy']:
                color = "warning"
                emoji = "⚠️"
                alert_level = "WARNING"
            else:
                color = "good"
                emoji = "ℹ️"
                alert_level = "INFO"
            
            # Create notification message
            if change_type == 'state_change':
                title = f"{emoji} Container Status Alert - {alert_level}"
                message = f"**Container:** {container_name}\n"
                message += f"**Status Change:** {previous_status} → {current_status}\n"
                message += f"**Image:** {container_info.get('image', 'unknown')}\n"
                message += f"**Time:** {timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n"
                
                if container_info.get('ports'):
                    message += f"**Ports:** {container_info['ports']}\n"
                
            elif change_type == 'container_removed':
                title = f"{emoji} Container Removed - {alert_level}"
                message = f"**Container:** {container_name}\n"
                message += f"**Previous Status:** {previous_status}\n"
                message += f"**Time:** {timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n"
                
            else:
                title = f"{emoji} Container Event - {alert_level}"
                message = f"**Container:** {container_name}\n"
                message += f"**Event:** {change_type}\n"
                message += f"**Status:** {current_status}\n"
                message += f"**Time:** {timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n"
            
            # Send notification
            success = self.slack_notifier.send_custom_message(title, message, color)
            
            if success:
                # Update cooldown tracker
                self.last_notifications[container_id] = datetime.now()
                logger.info(f"Real-time notification sent for {container_name}")
            else:
                logger.error(f"Failed to send real-time notification for {container_name}")
                
        except Exception as e:
            logger.error(f"Error sending real-time notification: {e}")
    
    def _update_container_states(self) -> None:
        """Update the initial container states."""
        self.previous_states = self._get_current_states()
        logger.info(f"Initialized monitoring for {len(self.previous_states)} containers")
    
    def get_monitoring_status(self) -> Dict[str, Any]:
        """Get current monitoring status."""
        return {
            'monitoring': self.monitoring,
            'check_interval': self.check_interval,
            'containers_tracked': len(self.previous_states),
            'thread_alive': self.monitor_thread.is_alive() if self.monitor_thread else False,
            'last_check': datetime.now().isoformat()
        } 