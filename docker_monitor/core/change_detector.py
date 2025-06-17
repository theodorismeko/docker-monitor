"""Container change detection and classification."""

from typing import Dict, List, Any
from datetime import datetime

from .state_tracker import StateTracker
from ..utils.logging_config import get_logger

logger = get_logger(__name__)


class ChangeDetector:
    """Analyzes state differences and classifies changes."""
    
    def __init__(self, state_tracker: StateTracker):
        """
        Initialize change detector.
        
        Args:
            state_tracker: StateTracker instance
        """
        self.state_tracker = state_tracker
    
    def detect_changes(self, current_states: Dict[str, str], previous_states: Dict[str, str]) -> List[Dict[str, Any]]:
        """
        Detect significant state changes.
        
        Args:
            current_states: Current container states
            previous_states: Previous container states
            
        Returns:
            List of detected changes
        """
        changes = []
        
        # Check for state changes in existing containers
        for container_name, current_status in current_states.items():
            previous_status = previous_states.get(container_name)
            container_info = self.state_tracker.get_container_info(container_name)
            
            # Check for restart count changes first (automatic restarts)
            restart_changes = self._detect_restart_count_changes(container_name, container_info, current_status)
            changes.extend(restart_changes)
            
            # Check for manual restarts (started time changes)
            if previous_status:  # Only check if previous_status is not None
                manual_restart_changes = self._detect_manual_restarts(container_name, container_info, current_status, previous_status)
                changes.extend(manual_restart_changes)
            
            # Only process state changes if no restart was detected
            if not restart_changes and not manual_restart_changes and previous_status and previous_status != current_status:
                logger.debug(f"Container {container_name}: {previous_status} → {current_status}")
                
                # Check for container stop events
                if previous_status == 'running' and current_status in ['stopped', 'exited', 'dead']:
                    logger.info(f"🛑 STOP EVENT DETECTED: {container_name} ({previous_status} → {current_status})")
                    change = {
                        'type': 'container_stopped',
                        'container_id': container_info.get('id', ''),
                        'container_name': container_name,
                        'container_info': container_info,
                        'previous_status': previous_status,
                        'current_status': current_status,
                        'timestamp': datetime.now()
                    }
                    changes.append(change)
                # Check for container start events specifically
                elif previous_status in ['stopped', 'exited', 'created', 'paused'] and current_status == 'running':
                    logger.info(f"✅ START EVENT DETECTED: {container_name} ({previous_status} → {current_status})")
                    change = {
                        'type': 'container_started',
                        'container_id': container_info.get('id', ''),
                        'container_name': container_name,
                        'container_info': container_info,
                        'previous_status': previous_status,
                        'current_status': current_status,
                        'timestamp': datetime.now()
                    }
                    changes.append(change)
                else:
                    # Regular state change for other transitions
                    logger.debug(f"Generic state change: {container_name} ({previous_status} → {current_status})")
                    change = {
                        'type': 'state_change',
                        'container_id': container_info.get('id', ''),
                        'container_name': container_name,
                        'container_info': container_info,
                        'previous_status': previous_status,
                        'current_status': current_status,
                        'timestamp': datetime.now()
                    }
                    changes.append(change)
        
        # Check for new containers
        new_container_changes = self._detect_new_containers(current_states, previous_states)
        changes.extend(new_container_changes)
        
        # Check for removed containers
        removed_container_changes = self._detect_removed_containers(current_states, previous_states)
        changes.extend(removed_container_changes)
        
        return changes
    
    def _detect_restart_count_changes(self, container_name: str, container_info: Dict[str, Any], current_status: str) -> List[Dict[str, Any]]:
        """
        Detect automatic restarts based on restart count changes.
        
        Args:
            container_name: Container name
            container_info: Container information
            current_status: Current container status
            
        Returns:
            List of restart changes detected
        """
        changes = []
        
        current_restart_count = container_info.get('restart_count', 0)
        previous_restart_count = self.state_tracker.get_previous_restart_count(container_name)
        
        # Debug logging for restart count tracking
        logger.debug(f"Restart count check for {container_name}: current={current_restart_count}, previous={previous_restart_count}")
        
        if current_restart_count > previous_restart_count:
            logger.info(f"🔄 AUTO-RESTART DETECTED: {container_name} (restart count: {previous_restart_count} → {current_restart_count})")
            change = {
                'type': 'container_restarted',
                'container_id': container_info.get('id', ''),
                'container_name': container_name,
                'container_info': container_info,
                'previous_restart_count': previous_restart_count,
                'current_restart_count': current_restart_count,
                'current_status': current_status,
                'restart_type': 'automatic',
                'timestamp': datetime.now()
            }
            changes.append(change)
            
            # Update restart count tracking
            self.state_tracker.update_restart_count(container_name, current_restart_count)
        
        return changes
    
    def _detect_manual_restarts(self, container_name: str, container_info: Dict[str, Any], 
                               current_status: str, previous_status: str) -> List[Dict[str, Any]]:
        """
        Detect manual restarts based on started time changes.
        
        Args:
            container_name: Container name
            container_info: Container information
            current_status: Current container status
            previous_status: Previous container status
            
        Returns:
            List of manual restart changes detected
        """
        changes = []
        
        current_started_time = container_info.get('started', '')
        previous_started_time = self.state_tracker.get_previous_started_time(container_name)
        
        # Debug logging for manual restart tracking
        logger.debug(f"Manual restart check for {container_name}: current_status={current_status}, previous_status={previous_status}")
        logger.debug(f"  Started times - current={current_started_time}, previous={previous_started_time}")
        
        # Detect restart if:
        # 1. Container is currently running
        # 2. We have a previous started time recorded
        # 3. The started time has changed (indicating a restart)
        # 4. The previous status was stopped/exited (indicating it went through a restart cycle)
        if (current_status == 'running' and 
            previous_started_time and 
            current_started_time != previous_started_time and
            previous_status in ['stopped', 'exited', 'created', 'restarting']):
            
            logger.info(f"🔄 RESTART DETECTED: {container_name} (started time changed from restart)")
            change = {
                'type': 'container_restarted',
                'container_id': container_info.get('id', ''),
                'container_name': container_name,
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
            self.state_tracker.update_started_time(container_name, current_started_time)
        
        return changes
    
    def _detect_new_containers(self, current_states: Dict[str, str], previous_states: Dict[str, str]) -> List[Dict[str, Any]]:
        """
        Detect new containers.
        
        Args:
            current_states: Current container states
            previous_states: Previous container states
            
        Returns:
            List of new container changes
        """
        changes = []
        
        for container_name in current_states:
            if container_name not in previous_states:
                container_info = self.state_tracker.get_container_info(container_name)
                change = {
                    'type': 'container_added',
                    'container_id': container_info.get('id', ''),
                    'container_name': container_name,
                    'container_info': container_info,
                    'current_status': current_states[container_name],
                    'timestamp': datetime.now()
                }
                changes.append(change)
                
                # Initialize restart count tracking for new containers
                restart_count = container_info.get('restart_count', 0)
                self.state_tracker.update_restart_count(container_name, restart_count)
                
                # Initialize started time tracking for new containers
                started_time = container_info.get('started', '')
                if started_time:
                    self.state_tracker.update_started_time(container_name, started_time)
        
        return changes
    
    def _detect_removed_containers(self, current_states: Dict[str, str], previous_states: Dict[str, str]) -> List[Dict[str, Any]]:
        """
        Detect removed containers.
        
        Args:
            current_states: Current container states
            previous_states: Previous container states
            
        Returns:
            List of removed container changes
        """
        changes = []
        
        for container_name in previous_states:
            if container_name not in current_states:
                change = {
                    'type': 'container_removed',
                    'container_id': '',  # ID not available for removed containers
                    'container_name': container_name,
                    'previous_status': previous_states[container_name],
                    'timestamp': datetime.now()
                }
                changes.append(change)
                
                # Clean up tracking for removed containers
                self.state_tracker.remove_container_tracking(container_name)
        
        return changes 