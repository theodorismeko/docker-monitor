"""Notification content creation and formatting."""

from typing import Dict, Any

from ..utils.logging_config import get_logger

logger = get_logger(__name__)


class NotificationFormatter:
    """Creates notification content and formatting."""
    
    def create_notification(self, change: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a notification message for a change.
        
        Args:
            change: Change information dictionary
            
        Returns:
            Formatted notification dictionary
        """
        change_type = change['type']
        container_info = change.get('container_info', {})
        container_name = container_info.get('name', change['container_id'][:12])
        timestamp = change['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
        
        if change_type == 'state_change':
            return self._create_state_change_notification(change, container_name, timestamp)
        elif change_type == 'container_restarted':
            return self._create_restart_notification(change, container_name, timestamp)
        elif change_type == 'container_started':
            return self._create_start_notification(change, container_name, timestamp)
        elif change_type == 'container_stopped':
            return self._create_stop_notification(change, container_name, timestamp)
        elif change_type == 'container_removed':
            return self._create_removal_notification(change, container_name, timestamp)
        elif change_type == 'container_added':
            return self._create_addition_notification(change, container_name, timestamp)
        else:
            return self._create_generic_notification(change, container_name, timestamp)
    
    def _create_state_change_notification(self, change: Dict[str, Any], container_name: str, timestamp: str) -> Dict[str, Any]:
        """Create notification for state changes."""
        previous_status = change['previous_status']
        current_status = change['current_status']
        container_info = change.get('container_info', {})
        
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
        
        return self._build_notification(alert_level, emoji, title, description, timestamp, 
                                      container_name, change['container_id'], color, container_info)
    
    def _create_restart_notification(self, change: Dict[str, Any], container_name: str, timestamp: str) -> Dict[str, Any]:
        """Create notification for container restarts."""
        restart_type = change.get('restart_type', 'unknown')
        current_status = change['current_status']
        container_info = change.get('container_info', {})
        
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
        
        return self._build_notification(alert_level, emoji, title, description, timestamp,
                                      container_name, change['container_id'], color, container_info)
    
    def _create_start_notification(self, change: Dict[str, Any], container_name: str, timestamp: str) -> Dict[str, Any]:
        """Create notification for container starts."""
        previous_status = change['previous_status']
        container_info = change.get('container_info', {})
        
        alert_level = 'info'
        emoji = '✅'
        color = '#00AA00'  # Green
        title = f"Container {container_name} STARTED"
        description = f"Container started successfully (transitioned from `{previous_status}` to `running`)"
        
        return self._build_notification(alert_level, emoji, title, description, timestamp,
                                      container_name, change['container_id'], color, container_info)
    
    def _create_stop_notification(self, change: Dict[str, Any], container_name: str, timestamp: str) -> Dict[str, Any]:
        """Create notification for container stops."""
        current_status = change['current_status']
        container_info = change.get('container_info', {})
        
        alert_level = 'critical'
        emoji = '🚨'
        color = '#FF0000'  # Red
        title = f"Container {container_name} STOPPED"
        description = f"Container stopped (transitioned from `running` to `{current_status}`)"
        
        return self._build_notification(alert_level, emoji, title, description, timestamp,
                                      container_name, change['container_id'], color, container_info)
    
    def _create_removal_notification(self, change: Dict[str, Any], container_name: str, timestamp: str) -> Dict[str, Any]:
        """Create notification for container removal."""
        alert_level = 'critical'
        emoji = '🚨'
        color = '#FF0000'  # Red
        title = f"Container {container_name} REMOVED"
        description = f"Container was unexpectedly removed (was `{change['previous_status']}`)"
        
        return self._build_notification(alert_level, emoji, title, description, timestamp,
                                      container_name, change['container_id'], color, {})
    
    def _create_addition_notification(self, change: Dict[str, Any], container_name: str, timestamp: str) -> Dict[str, Any]:
        """Create notification for container addition."""
        container_info = change.get('container_info', {})
        
        alert_level = 'info'
        emoji = '✅'
        color = '#00AA00'  # Green
        title = f"Container {container_name} ADDED"
        description = f"New container detected with status: `{change['current_status']}`"
        
        return self._build_notification(alert_level, emoji, title, description, timestamp,
                                      container_name, change['container_id'], color, container_info)
    
    def _create_generic_notification(self, change: Dict[str, Any], container_name: str, timestamp: str) -> Dict[str, Any]:
        """Create notification for unknown change types."""
        change_type = change['type']
        container_info = change.get('container_info', {})
        
        alert_level = 'info'
        emoji = 'ℹ️'
        color = '#0099CC'  # Blue
        title = f"Container {container_name} Event"
        description = f"Unknown change type: {change_type}"
        
        return self._build_notification(alert_level, emoji, title, description, timestamp,
                                      container_name, change['container_id'], color, container_info)
    
    def _build_notification(self, alert_level: str, emoji: str, title: str, description: str, 
                           timestamp: str, container_name: str, container_id: str, color: str, 
                           container_info: Dict[str, Any]) -> Dict[str, Any]:
        """Build the final notification dictionary."""
        notification = {
            'alert_level': alert_level,
            'title': f"{emoji} {title}",
            'description': description,
            'timestamp': timestamp,
            'container_name': container_name,
            'container_id': container_id,
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