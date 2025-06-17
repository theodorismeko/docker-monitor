"""Real-time Docker container monitoring for immediate failure detection."""

from typing import Dict, Optional, Any

from .docker_client import DockerClient
from .state_tracker import StateTracker
from .change_detector import ChangeDetector
from .notification_manager import NotificationManager
from .monitoring_thread import MonitoringThread
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
        
        # Initialize components
        self.state_tracker = StateTracker(self.docker_client, self.config.container_name_filter)
        self.change_detector = ChangeDetector(self.state_tracker)
        self.notification_manager = NotificationManager(self.slack_notifier, 120)  # 2 minutes cooldown
        self.monitoring_thread = MonitoringThread(self._check_for_changes)
        
        logger.info("Real-time monitor initialized")
    
    @property
    def monitoring(self) -> bool:
        """Thread-safe monitoring status getter."""
        return self.monitoring_thread.monitoring
    
    def start_monitoring(self, check_interval: int = 10) -> None:
        """
        Start real-time monitoring in a background thread.
        
        Args:
            check_interval: Check interval in seconds (default: 10)
        """
        logger.info(f"Setting up real-time monitoring with {check_interval}s interval...")
        
        # Update monitoring thread interval
        self.monitoring_thread.check_interval = check_interval
        
        # Initialize container states
        logger.info("Initializing container states...")
        self.state_tracker.initialize_states()
        
        # Start monitoring thread
        self.monitoring_thread.start()
        
        logger.info(f"Real-time monitoring started (interval: {check_interval}s)")
    
    def stop_monitoring(self) -> None:
        """Stop real-time monitoring gracefully."""
        logger.info("Stopping real-time monitoring...")
        self.monitoring_thread.stop()
        logger.info("Real-time monitoring stopped")
    
    def _check_for_changes(self) -> None:
        """Check for container state changes and send notifications."""
        try:
            # Get current and previous container states
            current_states = self.state_tracker.get_current_states()
            previous_states = self.state_tracker.get_previous_states()
            
            # Detect changes
            changes = self.change_detector.detect_changes(current_states, previous_states)
            
            # Debug logging
            if changes:
                logger.info(f"Detected {len(changes)} changes")
                for change in changes:
                    container_name = change.get('container_name', change.get('container_info', {}).get('name', change.get('container_id', 'unknown')[:12]))
                    logger.info(f"Change: {change['type']} for {container_name}")
            else:
                logger.info("No changes detected")
            
            # Process changes and send notifications
            self.notification_manager.process_changes(changes)
            
            # Update previous states
            self.state_tracker.update_previous_states(current_states)
            
        except Exception as e:
            logger.error(f"Error checking for changes: {e}")
    
    def get_monitoring_status(self) -> Dict[str, Any]:
        """Get current monitoring status (thread-safe)."""
        return self.monitoring_thread.get_status()

    def test_restart_detection(self) -> None:
        """Test restart detection functionality."""
        logger.info("Testing restart detection...")
        
        try:
            # Get current container states
            current_states = self.state_tracker.get_current_states()
            
            # Log current restart counts
            for container_id, container_info in self.state_tracker.get_all_container_info().items():
                container_name = container_info.get('name', container_id[:12])
                restart_count = container_info.get('restart_count', 0)
                started_time = container_info.get('started', 'N/A')
                status = current_states.get(container_id, 'unknown')
                
                logger.info(f"Container {container_name}: status={status}, restart_count={restart_count}, started={started_time}")
            
            logger.info("Restart detection test completed")
            
        except Exception as e:
            logger.error(f"Error during restart detection test: {e}")