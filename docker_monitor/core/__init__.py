"""Core monitoring components."""

from .realtime_monitor import RealTimeMonitor
from .state_tracker import StateTracker
from .change_detector import ChangeDetector
from .notification_manager import NotificationManager
from .notification_formatter import NotificationFormatter
from .cooldown_manager import CooldownManager
from .monitoring_thread import MonitoringThread
from .docker_client import DockerClient
from .docker_monitor import DockerMonitor

# Backward compatibility alias
Monitor = DockerMonitor

__all__ = [
    'RealTimeMonitor',
    'StateTracker',
    'ChangeDetector',
    'NotificationManager',
    'NotificationFormatter',
    'CooldownManager',
    'MonitoringThread',
    'DockerClient',
    'DockerMonitor',
    'Monitor'  # Backward compatibility
]
