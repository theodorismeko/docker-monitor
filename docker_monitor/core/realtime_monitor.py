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
        self.previous_restart_counts: Dict[str, int] = {}
        self.previous_started_times: Dict[str, str] = {}
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
        logger.info(f"Initial monitoring flag value: {self.monitoring}")
        
        cycle_count = 0
        while self.monitoring:
            try:
                cycle_count += 1
                logger.info(f"Starting change check cycle #{cycle_count}...")
                self._check_for_changes()
                logger.info(f"Change check cycle #{cycle_count} completed, sleeping for {self.check_interval} seconds")
                time.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"Error in monitoring loop cycle #{cycle_count}: {e}")
                time.sleep(self.check_interval)
        
        logger.info(f"Real-time monitoring loop stopped (monitoring flag: {self.monitoring})")
    
    def _check_for_changes(self) -> None:
        """Check for container state changes and send notifications."""
        try:
            # Get current container states
            current_states = self._get_current_states()
            
            # Compare with previous states
            changes = self._detect_changes(current_states)
            
            # Debug logging
            if changes:
                logger.info(f"Detected {len(changes)} changes")
                for change in changes:
                    logger.info(f"Change: {change['type']} for {change.get('container_info', {}).get('name', change['container_id'][:12])}")
            else:
                logger.info("No changes detected")
            
            # Process changes and send notifications
            for change in changes:
                if self._should_notify(change):
                    # Log restart events for debugging
                    if change['type'] == 'container_restarted':
                        self._log_restart_event(change)
                    
                    notification = self._create_notification(change)
                    
                    try:
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
                            # Update cooldown
                            self.last_notifications[change['container_id']] = datetime.now()
                        else:
                            logger.error(f"Failed to send notification for {change['type']}")
                            
                    except Exception as e:
                        logger.error(f"Error sending notification: {e}")
            
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
            container_info = self.container_info.get(container_id, {})
            
            if previous_status and previous_status != current_status:
                change = {
                    'type': 'state_change',
                    'container_id': container_id,
                    'container_info': container_info,
                    'previous_status': previous_status,
                    'current_status': current_status,
                    'timestamp': datetime.now()
                }
                changes.append(change)
            
            # Check for restart count changes (indicates container restarted)
            current_restart_count = container_info.get('restart_count', 0)
            previous_restart_count = self.previous_restart_counts.get(container_id, 0)
            
            if current_restart_count > previous_restart_count:
                change = {
                    'type': 'container_restarted',
                    'container_id': container_id,
                    'container_info': container_info,
                    'previous_restart_count': previous_restart_count,
                    'current_restart_count': current_restart_count,
                    'current_status': current_status,
                    'restart_type': 'automatic',
                    'timestamp': datetime.now()
                }
                changes.append(change)
                
                # Update restart count tracking
                self.previous_restart_counts[container_id] = current_restart_count
            
            # Check for manual restarts (StartedAt timestamp changes while container is running)
            current_started_time = container_info.get('started', '')
            previous_started_time = self.previous_started_times.get(container_id, '')
            
            if (current_status == 'running' and 
                previous_started_time and 
                current_started_time != previous_started_time and
                previous_status == 'running'):
                
                change = {
                    'type': 'container_restarted',
                    'container_id': container_id,
                    'container_info': container_info,
                    'previous_started_time': previous_started_time,
                    'current_started_time': current_started_time,
                    'current_status': current_status,
                    'restart_type': 'manual',
                    'timestamp': datetime.now()
                }
                changes.append(change)
            
            # Update started time tracking
            if current_started_time:
                self.previous_started_times[container_id] = current_started_time
        
        # Check for new containers
        for container_id in current_states:
            if container_id not in self.previous_states:
                container_info = self.container_info.get(container_id, {})
                change = {
                    'type': 'container_added',
                    'container_id': container_id,
                    'container_info': container_info,
                    'current_status': current_states[container_id],
                    'timestamp': datetime.now()
                }
                changes.append(change)
                
                # Initialize restart count tracking for new containers
                restart_count = container_info.get('restart_count', 0)
                self.previous_restart_counts[container_id] = restart_count
                
                # Initialize started time tracking for new containers
                started_time = container_info.get('started', '')
                if started_time:
                    self.previous_started_times[container_id] = started_time
        
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
                
                # Clean up restart count tracking for removed containers
                self.previous_restart_counts.pop(container_id, None)
                
                # Clean up started time tracking for removed containers
                self.previous_started_times.pop(container_id, None)
        
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
            # Container restarted (restart count increased)
            (change_type == 'container_restarted'),
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
    
    def _create_notification(self, change: Dict[str, Any]) -> Dict[str, Any]:
        """Create a notification message for a change."""
        change_type = change['type']
        container_info = change.get('container_info', {})
        container_name = container_info.get('name', change['container_id'][:12])
        timestamp = change['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
        
        if change_type == 'state_change':
            previous_status = change['previous_status']
            current_status = change['current_status']
            
            # Determine alert level
            if previous_status == 'running' and current_status in ['exited', 'stopped', 'dead']:
                alert_level = 'critical'
                emoji = '🚨'
                color = '#FF0000'  # Red
                title = f"Container {container_name} STOPPED"
                description = f"Container transitioned from `{previous_status}` to `{current_status}`"
            elif current_status == 'restarting':
                alert_level = 'warning'
                emoji = '⚠️'
                color = '#FFA500'  # Orange
                title = f"Container {container_name} RESTARTING"
                description = f"Container is in restarting state (may indicate issues)"
            elif previous_status == 'running' and current_status == 'unhealthy':
                alert_level = 'warning'
                emoji = '⚠️'
                color = '#FFA500'  # Orange
                title = f"Container {container_name} UNHEALTHY"
                description = f"Container health check failed"
            else:
                alert_level = 'info'
                emoji = 'ℹ️'
                color = '#0099CC'  # Blue
                title = f"Container {container_name} Status Change"
                description = f"Container transitioned from `{previous_status}` to `{current_status}`"
        
        elif change_type == 'container_restarted':
            restart_type = change.get('restart_type', 'unknown')
            current_status = change['current_status']
            
            if restart_type == 'automatic':
                previous_count = change['previous_restart_count']
                current_count = change['current_restart_count']
                restart_diff = current_count - previous_count
                
                alert_level = 'warning'
                emoji = '🔄'
                color = '#FFA500'  # Orange
                title = f"Container {container_name} AUTO-RESTARTED"
                
                if restart_diff == 1:
                    description = f"Container automatically restarted due to failure (restart count: {previous_count} → {current_count})"
                else:
                    description = f"Container automatically restarted {restart_diff} times due to failures (restart count: {previous_count} → {current_count})"
                
                if current_status != 'running':
                    description += f"\n⚠️ Current status: `{current_status}`"
                    alert_level = 'critical'
                    emoji = '🚨'
                    color = '#FF0000'  # Red
            
            elif restart_type == 'manual':
                previous_time = change.get('previous_started_time', '')
                current_time = change.get('current_started_time', '')
                
                alert_level = 'warning'
                emoji = '🔄'
                color = '#FFA500'  # Orange
                title = f"Container {container_name} RESTARTED"
                description = f"Container was manually restarted (started time changed)"
                
                if current_status != 'running':
                    description += f"\n⚠️ Current status: `{current_status}`"
                    alert_level = 'critical'
                    emoji = '🚨'
                    color = '#FF0000'  # Red
            
            else:
                alert_level = 'warning'
                emoji = '🔄'
                color = '#FFA500'  # Orange
                title = f"Container {container_name} RESTARTED"
                description = f"Container restart detected (type: {restart_type})"
        
        elif change_type == 'container_removed':
            alert_level = 'critical'
            emoji = '🚨'
            color = '#FF0000'  # Red
            title = f"Container {container_name} REMOVED"
            description = f"Container was unexpectedly removed (was `{change['previous_status']}`)"
        
        elif change_type == 'container_added':
            alert_level = 'info'
            emoji = '✅'
            color = '#00AA00'  # Green
            title = f"Container {container_name} ADDED"
            description = f"New container detected with status: `{change['current_status']}`"
        
        else:
            alert_level = 'info'
            emoji = 'ℹ️'
            color = '#0099CC'  # Blue
            title = f"Container {container_name} Event"
            description = f"Unknown change type: {change_type}"
        
        # Build notification
        notification = {
            'alert_level': alert_level,
            'title': f"{emoji} {title}",
            'description': description,
            'timestamp': timestamp,
            'container_name': container_name,
            'container_id': change['container_id'],
            'color': color
        }
        
        # Add container details if available
        if container_info:
            details = []
            if 'image' in container_info:
                details.append(f"**Image:** {container_info['image']}")
            if 'ports' in container_info and container_info['ports']:
                details.append(f"**Ports:** {container_info['ports']}")
            if 'created' in container_info:
                details.append(f"**Created:** {container_info['created']}")
            
            if details:
                notification['details'] = '\n'.join(details)
        
        return notification

    def test_restart_detection(self) -> None:
        """Test restart detection functionality."""
        logger.info("Testing restart detection...")
        
        try:
            # Get current container states
            current_states = self._get_current_states()
            
            # Log current restart counts
            for container_id, container_info in self.container_info.items():
                container_name = container_info.get('name', container_id[:12])
                restart_count = container_info.get('restart_count', 0)
                started_time = container_info.get('started', 'N/A')
                status = current_states.get(container_id, 'unknown')
                
                logger.info(f"Container {container_name}: status={status}, restart_count={restart_count}, started={started_time}")
            
            logger.info("Restart detection test completed")
            
        except Exception as e:
            logger.error(f"Error during restart detection test: {e}")

    def _log_restart_event(self, change: Dict[str, Any]) -> None:
        """Log restart event details for debugging."""
        container_info = change.get('container_info', {})
        container_name = container_info.get('name', change['container_id'][:12])
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