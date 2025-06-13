"""Main Docker monitoring orchestrator."""

import schedule
import time
from typing import Optional, Dict, Any

from .docker_client import DockerClient
from .realtime_monitor import RealTimeMonitor
from ..integrations.slack import SlackNotifier
from ..utils.config import Config
from ..utils.logging_config import get_logger, setup_logging

logger = get_logger(__name__)


class DockerMonitor:
    """Main Docker monitoring orchestrator."""
    
    def __init__(self, config: Optional[Config] = None):
        """
        Initialize Docker Monitor.
        
        Args:
            config: Configuration instance. If None, creates a new one.
        """
        self.config = config or Config()
        
        # Set up logging
        setup_logging(
            log_level=self.config.log_level,
            console_output=True
        )
        
        # Initialize components
        self.docker_client = DockerClient(self.config.docker_socket)
        self.slack_notifier = SlackNotifier(self.config.slack_webhook_url)
        
        logger.info("Docker Monitor initialized successfully")
    
    def run_check(self) -> bool:
        """
        Run a single monitoring check.
        
        Returns:
            True if check completed successfully, False otherwise
        """
        logger.info("Starting Docker container check...")
        
        try:
            # Check Docker connection
            if not self.docker_client.is_connected():
                logger.warning("Docker client disconnected, attempting to reconnect...")
                if not self.docker_client.reconnect():
                    raise ConnectionError("Failed to reconnect to Docker daemon")
            
            # Get container information
            container_info = self.docker_client.get_containers(
                include_stopped=self.config.include_stopped_containers,
                name_filter=self.config.container_name_filter
            )
            
            # Get system information
            system_info = self.docker_client.get_system_info()
            
            # Send notification if enabled
            if self.config.notification_enabled:
                success = self.slack_notifier.send_container_report(
                    container_info, system_info
                )
                if not success:
                    logger.error("Failed to send Slack notification")
                    return False
            else:
                logger.info("Notifications disabled, skipping Slack notification")
            
            logger.info("Container check completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error during container check: {e}")
            
            # Try to send error notification
            if self.config.notification_enabled:
                try:
                    self.slack_notifier.send_error_notification(
                        str(e), "Docker container monitoring check"
                    )
                except Exception as notification_error:
                    logger.error(f"Failed to send error notification: {notification_error}")
            
            return False
    
    def run_scheduled(self) -> None:
        """
        Run with scheduled execution.
        
        This method will run indefinitely, executing checks at the configured time.
        """
        logger.info("Starting Docker monitor with scheduled execution...")
        
        # Schedule the daily check
        schedule.every().day.at(self.config.daily_check_time).do(self.run_check)
        
        # Don't run initial check - wait for scheduled time
        logger.info(f"Scheduler started. Next check scheduled for {self.config.daily_check_time}")
        
        # Main scheduling loop
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            logger.info("Scheduled monitoring stopped by user")
        except Exception as e:
            logger.error(f"Scheduler error: {e}")
            raise
    
    def test_connections(self) -> Dict[str, bool]:
        """
        Test all connections (Docker and Slack).
        
        Returns:
            Dictionary with test results
        """
        results = {}
        
        # Test Docker connection
        logger.info("Testing Docker connection...")
        try:
            results['docker'] = self.docker_client.is_connected()
            if results['docker']:
                logger.info("✅ Docker connection successful")
            else:
                logger.error("❌ Docker connection failed")
        except Exception as e:
            logger.error(f"❌ Docker connection test failed: {e}")
            results['docker'] = False
        
        # Test Slack connection
        logger.info("Testing Slack webhook...")
        try:
            results['slack'] = self.slack_notifier.test_connection()
            if results['slack']:
                logger.info("✅ Slack webhook successful")
            else:
                logger.error("❌ Slack webhook failed")
        except Exception as e:
            logger.error(f"❌ Slack webhook test failed: {e}")
            results['slack'] = False
        
        return results
    
    def get_status_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the current system status.
        
        Returns:
            Dictionary with status information
        """
        try:
            # Get container info
            containers = self.docker_client.get_containers(
                include_stopped=self.config.include_stopped_containers,
                name_filter=self.config.container_name_filter
            )
            
            # Get system info
            system_info = self.docker_client.get_system_info()
            
            # Count containers by status
            status_counts = {}
            for container in containers:
                status = container.get('status', 'unknown')
                status_counts[status] = status_counts.get(status, 0) + 1
            
            return {
                'total_containers': len(containers),
                'status_counts': status_counts,
                'system_info': system_info,
                'config': self.config.get_all(),
                'connections': self.test_connections()
            }
            
        except Exception as e:
            logger.error(f"Error getting status summary: {e}")
            return {
                'error': str(e),
                'connections': self.test_connections()
            }
    
    def send_test_notification(self) -> bool:
        """
        Send a test notification to Slack.
        
        Returns:
            True if successful, False otherwise
        """
        return self.slack_notifier.send_custom_message(
            "🧪 Docker Monitor Test",
            "This is a test notification from Docker Monitor to verify the integration is working correctly.",
            "good"
        )
    
    def test_restart_detection(self) -> bool:
        """
        Test restart detection functionality.
        
        Returns:
            True if successful, False otherwise
        """
        logger.info("Testing restart detection functionality...")
        
        try:
            # Create a temporary real-time monitor instance
            realtime_monitor = RealTimeMonitor(self.config)
            realtime_monitor.test_restart_detection()
            return True
        except Exception as e:
            logger.error(f"Error testing restart detection: {e}")
            return False
    
    def monitor_containers_continuously(self, interval_minutes: int = 5) -> None:
        """
        Monitor containers continuously at specified intervals.
        
        Args:
            interval_minutes: Check interval in minutes
            
        Note:
            This is different from scheduled execution - it runs checks continuously
            at the specified interval instead of once per day.
        """
        logger.info(f"Starting continuous monitoring with {interval_minutes} minute intervals...")
        
        try:
            while True:
                self.run_check()
                logger.info(f"Sleeping for {interval_minutes} minutes...")
                time.sleep(interval_minutes * 60)
        except KeyboardInterrupt:
            logger.info("Continuous monitoring stopped by user")
        except Exception as e:
            logger.error(f"Continuous monitoring error: {e}")
            raise
    
    def monitor_containers_realtime(self, interval_seconds: int = 10) -> None:
        """
        Monitor containers in real-time for immediate failure detection.
        
        Args:
            interval_seconds: Check interval in seconds
            
        Note:
            This monitors for container state changes and sends immediate notifications
            when containers go down, restart, or have issues.
        """
        logger.info(f"Starting real-time monitoring with {interval_seconds} second intervals...")
        
        try:
            # Import here to avoid circular imports
            from .realtime_monitor import RealTimeMonitor
            
            realtime_monitor = RealTimeMonitor(self.config)
            realtime_monitor.start_monitoring(interval_seconds)
            
            # Keep the main thread alive
            try:
                while realtime_monitor.monitoring:
                    time.sleep(1)
            except KeyboardInterrupt:
                logger.info("Real-time monitoring interrupted by user")
            finally:
                realtime_monitor.stop_monitoring()
                
        except Exception as e:
            logger.error(f"Real-time monitoring error: {e}")
            raise 