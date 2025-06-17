"""Background monitoring thread management."""

import threading
import time
from typing import Callable, Optional

from ..utils.logging_config import get_logger

logger = get_logger(__name__)


class MonitoringThread:
    """Manages the background monitoring loop."""
    
    def __init__(self, check_function: Callable[[], None], check_interval: int = 10):
        """
        Initialize monitoring thread.
        
        Args:
            check_function: Function to call on each monitoring cycle
            check_interval: Check interval in seconds (default: 10)
        """
        self.check_function = check_function
        self.check_interval = check_interval
        
        # Thread management
        self._lock = threading.RLock()
        self._monitoring = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._shutdown_event = threading.Event()
    
    @property
    def monitoring(self) -> bool:
        """Thread-safe monitoring status getter."""
        with self._lock:
            return self._monitoring
    
    @monitoring.setter
    def monitoring(self, value: bool) -> None:
        """Thread-safe monitoring status setter."""
        with self._lock:
            self._monitoring = value
    
    def start(self) -> None:
        """Start the monitoring thread."""
        with self._lock:
            if self._monitoring:
                logger.warning("Monitoring thread is already running")
                return
            
            logger.info(f"Starting monitoring thread with {self.check_interval}s interval...")
            self._monitoring = True
            self._shutdown_event.clear()
        
        logger.info(f"Monitoring flag set to: {self.monitoring}")
        
        # Start monitoring thread
        logger.info("Creating monitoring thread...")
        with self._lock:
            self._monitor_thread = threading.Thread(
                target=self._monitoring_loop,
                daemon=True,
                name="DockerRealTimeMonitor"
            )
        
        logger.info(f"Thread created: {self._monitor_thread}")
        
        logger.info("Starting monitoring thread...")
        self._monitor_thread.start()
        logger.info(f"Thread started. Is alive: {self._monitor_thread.is_alive()}")
        
        logger.info(f"Monitoring thread started (interval: {self.check_interval}s)")
    
    def stop(self) -> None:
        """Stop the monitoring thread gracefully."""
        logger.info("Stopping monitoring thread...")
        
        with self._lock:
            if not self._monitoring:
                logger.warning("Monitoring thread is not running")
                return
            
            self._monitoring = False
            monitor_thread = self._monitor_thread
        
        # Signal shutdown
        self._shutdown_event.set()
        
        # Wait for thread to finish
        if monitor_thread and monitor_thread.is_alive():
            logger.info("Waiting for monitoring thread to stop...")
            monitor_thread.join(timeout=10)
            
            if monitor_thread.is_alive():
                logger.warning("Monitoring thread did not stop gracefully within timeout")
            else:
                logger.info("Monitoring thread stopped successfully")
        
        logger.info("Monitoring thread stopped")
    
    def _monitoring_loop(self) -> None:
        """Main monitoring loop that runs in background thread."""
        try:
            logger.info("Monitoring loop started")
            logger.info(f"Initial monitoring flag value: {self.monitoring}")
            
            if not self.monitoring:
                logger.error("Monitoring flag is False! Loop will not start.")
                return
            
            cycle_count = 0
            logger.info("Entering monitoring while loop...")
            
            while self.monitoring and not self._shutdown_event.is_set():
                try:
                    cycle_count += 1
                    logger.info(f"Starting monitoring cycle #{cycle_count}...")
                    self.check_function()
                    logger.info(f"Monitoring cycle #{cycle_count} completed")
                    
                    # Use shutdown event for interruptible sleep
                    if self._shutdown_event.wait(timeout=self.check_interval):
                        logger.info("Shutdown event received, stopping monitoring loop")
                        break
                        
                except Exception as e:
                    logger.error(f"Error in monitoring loop cycle #{cycle_count}: {e}")
                    # Still sleep on error to avoid tight error loop
                    if self._shutdown_event.wait(timeout=self.check_interval):
                        break
            
            logger.info(f"Monitoring loop stopped (monitoring flag: {self.monitoring})")
        except Exception as e:
            logger.error(f"Fatal error in monitoring loop: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
        finally:
            # Ensure monitoring flag is set to False
            with self._lock:
                self._monitoring = False
    
    def get_status(self) -> dict:
        """Get current thread status."""
        with self._lock:
            return {
                'monitoring': self._monitoring,
                'thread_alive': self._monitor_thread.is_alive() if self._monitor_thread else False,
                'check_interval': self.check_interval,
                'shutdown_event_set': self._shutdown_event.is_set()
            } 