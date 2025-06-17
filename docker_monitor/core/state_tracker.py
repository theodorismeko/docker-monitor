"""Container state tracking for monitoring."""

import threading
from typing import Dict, Any, Optional
from datetime import datetime

from .docker_client import DockerClient
from ..utils.logging_config import get_logger

logger = get_logger(__name__)


class StateTracker:
    """Manages container state persistence and retrieval."""
    
    def __init__(self, docker_client: DockerClient, container_name_filter: Optional[str] = None):
        """
        Initialize state tracker.
        
        Args:
            docker_client: Docker client instance
            container_name_filter: Optional container name filter
        """
        self.docker_client = docker_client
        self.container_name_filter = container_name_filter
        
        # Thread-safe state storage
        self._state_lock = threading.Lock()
        self._previous_states: Dict[str, str] = {}
        self._container_info: Dict[str, Dict[str, Any]] = {}
        self._previous_restart_counts: Dict[str, int] = {}
        self._previous_started_times: Dict[str, str] = {}
    
    def get_current_states(self) -> Dict[str, str]:
        """
        Get current container states.
        
        Returns:
            Dictionary mapping container names to their current states
        """
        try:
            containers = self.docker_client.get_containers(
                include_stopped=True,
                name_filter=self.container_name_filter
            )
            
            states = {}
            container_info = {}
            
            for container in containers:
                container_id = container.get('id', '')
                container_name = container.get('name', '')
                status = container.get('status', 'unknown')
                
                if container_name:  # Use container name as key instead of ID
                    states[container_name] = status
                    container_info[container_name] = container
            
            # Update container info safely
            with self._state_lock:
                self._container_info = container_info
            
            return states
            
        except Exception as e:
            logger.error(f"Error getting container states: {e}")
            return {}
    
    def get_previous_states(self) -> Dict[str, str]:
        """
        Get previous container states (thread-safe).
        
        Returns:
            Copy of previous states dictionary
        """
        with self._state_lock:
            return self._previous_states.copy()
    
    def update_previous_states(self, states: Dict[str, str]) -> None:
        """
        Update previous states (thread-safe).
        
        Args:
            states: New states to store as previous
        """
        with self._state_lock:
            self._previous_states = states.copy()
    
    def get_container_info(self, container_name: str) -> Dict[str, Any]:
        """
        Get container info for a specific container (thread-safe).
        
        Args:
            container_name: Container name
            
        Returns:
            Container info dictionary
        """
        with self._state_lock:
            return self._container_info.get(container_name, {})
    
    def get_all_container_info(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all container info (thread-safe).
        
        Returns:
            Copy of container info dictionary
        """
        with self._state_lock:
            return self._container_info.copy()
    
    def get_previous_restart_count(self, container_name: str) -> int:
        """
        Get previous restart count for a container (thread-safe).
        
        Args:
            container_name: Container name
            
        Returns:
            Previous restart count
        """
        with self._state_lock:
            return self._previous_restart_counts.get(container_name, 0)
    
    def update_restart_count(self, container_name: str, count: int) -> None:
        """
        Update restart count for a container (thread-safe).
        
        Args:
            container_name: Container name
            count: New restart count
        """
        with self._state_lock:
            self._previous_restart_counts[container_name] = count
    
    def get_previous_started_time(self, container_name: str) -> str:
        """
        Get previous started time for a container (thread-safe).
        
        Args:
            container_name: Container name
            
        Returns:
            Previous started time
        """
        with self._state_lock:
            return self._previous_started_times.get(container_name, '')
    
    def update_started_time(self, container_name: str, started_time: str) -> None:
        """
        Update started time for a container (thread-safe).
        
        Args:
            container_name: Container name
            started_time: New started time
        """
        with self._state_lock:
            self._previous_started_times[container_name] = started_time
    
    def remove_container_tracking(self, container_name: str) -> None:
        """
        Remove tracking data for a container (thread-safe).
        
        Args:
            container_name: Container name to remove
        """
        with self._state_lock:
            self._previous_restart_counts.pop(container_name, None)
            self._previous_started_times.pop(container_name, None)
    
    def initialize_states(self) -> None:
        """Initialize container states."""
        current_states = self.get_current_states()
        self.update_previous_states(current_states)
        
        # Initialize restart counts and started times
        for container_name, container_info in self.get_all_container_info().items():
            restart_count = container_info.get('restart_count', 0)
            self.update_restart_count(container_name, restart_count)
            
            started_time = container_info.get('started', '')
            if started_time:
                self.update_started_time(container_name, started_time)
        
        logger.info(f"Initialized state tracking for {len(current_states)} containers") 