"""Custom exceptions for Docker Monitor."""


class DockerMonitorError(Exception):
    """Base exception for Docker Monitor."""
    pass


class ConnectionError(DockerMonitorError):
    """Connection-related errors."""
    pass


class ConfigurationError(DockerMonitorError):
    """Configuration-related errors."""
    pass


class NotificationError(DockerMonitorError):
    """Notification-related errors."""
    pass


class MonitoringError(DockerMonitorError):
    """Monitoring operation errors."""
    pass