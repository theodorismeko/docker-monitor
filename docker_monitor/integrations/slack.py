"""Slack integration for Docker Monitor."""

from datetime import datetime
from typing import List, Dict, Any, Optional
import requests
import json

from ..utils.logging_config import get_logger

logger = get_logger(__name__)


class SlackNotifier:
    """Slack notification handler."""
    
    def __init__(self, webhook_url: str):
        """
        Initialize Slack notifier.
        
        Args:
            webhook_url: Slack webhook URL
        """
        self.webhook_url = webhook_url
        if not webhook_url:
            raise ValueError("Slack webhook URL is required")
    
    def send_container_report(
        self,
        container_info: List[Dict[str, Any]],
        system_info: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Send container status report to Slack.
        
        Args:
            container_info: List of container information
            system_info: Optional system information
            
        Returns:
            True if successful, False otherwise
        """
        try:
            message = self._create_status_message(container_info, system_info)
            response = requests.post(
                self.webhook_url,
                json=message,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            response.raise_for_status()
            logger.info("Successfully sent container report to Slack")
            return True
        except Exception as e:
            logger.error(f"Failed to send Slack notification: {e}")
            return False
    
    def send_error_notification(self, error_message: str, context: str = "") -> bool:
        """
        Send error notification to Slack.
        
        Args:
            error_message: Error message to send
            context: Additional context information
            
        Returns:
            True if successful, False otherwise
        """
        try:
            message = self._create_error_message(error_message, context)
            response = requests.post(
                self.webhook_url,
                json=message,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            response.raise_for_status()
            logger.info("Successfully sent error notification to Slack")
            return True
        except Exception as e:
            logger.error(f"Failed to send error notification: {e}")
            return False
    
    def send_custom_message(
        self,
        title: str,
        message: str,
        color: str = "good"
    ) -> bool:
        """
        Send custom message to Slack.
        
        Args:
            title: Message title
            message: Message content
            color: Slack color (good, warning, danger, or hex color)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            slack_message = {
                "attachments": [
                    {
                        "color": color,
                        "title": title,
                        "text": message,
                        "footer": "Docker Monitor",
                        "ts": int(datetime.now().timestamp())
                    }
                ]
            }
            
            response = requests.post(
                self.webhook_url,
                json=slack_message,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            response.raise_for_status()
            logger.info(f"Successfully sent custom message to Slack: {title}")
            return True
        except Exception as e:
            logger.error(f"Failed to send custom message: {e}")
            return False
    
    def _create_status_message(
        self,
        container_info: List[Dict[str, Any]],
        system_info: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create Slack message for container status report."""
        
        # Count containers by status
        status_counts = self._count_containers_by_status(container_info)
        
        # Determine color based on overall health
        if status_counts.get('running', 0) > 0 and status_counts.get('exited', 0) == 0:
            color = "good"
        elif status_counts.get('exited', 0) > 0:
            color = "warning"
        else:
            color = "danger"
        
        # Create main attachment
        main_attachment = {
            "color": color,
            "title": "🐳 Docker Container Status Report",
            "fields": [],
            "footer": "Docker Monitor",
            "ts": int(datetime.now().timestamp())
        }
        
        # Add summary fields
        main_attachment["fields"].append({
            "title": "Total Containers",
            "value": str(len(container_info)),
            "short": True
        })
        
        if system_info:
            main_attachment["fields"].extend([
                {
                    "title": "Docker Version",
                    "value": system_info.get('server_version', 'unknown'),
                    "short": True
                },
                {
                    "title": "System",
                    "value": system_info.get('operating_system', 'unknown'),
                    "short": False
                }
            ])
        
        # Add status counts
        for status, count in status_counts.items():
            emoji = self._get_status_emoji(status)
            main_attachment["fields"].append({
                "title": f"{emoji} {status.title()}",
                "value": str(count),
                "short": True
            })
        
        # Create container details
        container_blocks = []
        for container in container_info:
            container_text = self._format_container_details(container)
            container_blocks.append(container_text)
        
        # Combine all details
        if container_blocks:
            main_attachment["text"] = "\n\n".join(container_blocks)
        
        return {"attachments": [main_attachment]}
    
    def _create_error_message(self, error_message: str, context: str = "") -> Dict[str, Any]:
        """Create Slack message for error notification."""
        error_text = f"**Error occurred during Docker monitoring:**\n\n{error_message}"
        if context:
            error_text += f"\n\n**Context:** {context}"
        
        return {
            "attachments": [
                {
                    "color": "danger",
                    "title": "🚨 Docker Monitor Error",
                    "text": error_text,
                    "footer": "Docker Monitor",
                    "ts": int(datetime.now().timestamp())
                }
            ]
        }
    
    def _count_containers_by_status(self, container_info: List[Dict[str, Any]]) -> Dict[str, int]:
        """Count containers by their status."""
        status_counts = {}
        for container in container_info:
            status = container.get('status', 'unknown')
            status_counts[status] = status_counts.get(status, 0) + 1
        return status_counts
    
    def _format_container_details(self, container: Dict[str, Any]) -> str:
        """Format container details for Slack."""
        status = container.get('status', 'unknown')
        emoji = self._get_status_emoji(status)
        
        details = [
            f"{emoji} **{container.get('name', 'unknown')}**",
            f"Status: {status}",
            f"Image: {container.get('image', 'unknown')}",
            f"ID: {container.get('id', 'unknown')}",
            f"Ports: {container.get('ports', 'None')}"
        ]
        
        # Add health status if available
        health_status = container.get('health_status')
        if health_status:
            details.append(f"Health: {health_status}")
        
        # Add performance stats for running containers
        stats = container.get('stats')
        if stats and status == 'running':
            details.extend([
                f"CPU Usage: {stats.get('cpu_percent', 0)}%",
                f"Memory: {stats.get('memory_usage', {}).get('used', 'N/A')} / "
                f"{stats.get('memory_usage', {}).get('limit', 'N/A')} "
                f"({stats.get('memory_usage', {}).get('percent', 0)}%)"
            ])
            
            # Add network stats if available
            network = stats.get('network', {})
            if network.get('rx_bytes') != 'N/A':
                details.append(f"Network: ↓{network.get('rx_bytes', 'N/A')} ↑{network.get('tx_bytes', 'N/A')}")
        
        # Add restart count if significant
        restart_count = container.get('restart_count', 0)
        if restart_count > 0:
            details.append(f"Restarts: {restart_count}")
        
        return "\n".join(details)
    
    def _get_status_emoji(self, status: str) -> str:
        """Get emoji for container status."""
        emoji_map = {
            'running': '✅',
            'exited': '❌',
            'stopped': '⏹️',
            'paused': '⏸️',
            'restarting': '🔄',
            'removing': '🗑️',
            'dead': '💀',
            'created': '🆕'
        }
        return emoji_map.get(status.lower(), '⚠️')
    
    def test_connection(self) -> bool:
        """
        Test the Slack webhook connection.
        
        Returns:
            True if connection successful, False otherwise
        """
        return self.send_custom_message(
            "🧪 Test Message",
            "Docker Monitor Slack integration is working correctly!",
            "good"
        ) 