"""Configuration management for Docker Monitor."""

import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from dotenv import load_dotenv

logger = logging.getLogger(__name__)


class Config:
    """Configuration manager for Docker Monitor."""
    
    def __init__(self, env_file: Optional[str] = None):
        """
        Initialize configuration.
        
        Args:
            env_file: Path to environment file. If None, looks for .env in project root.
        """
        self._load_environment(env_file)
        self._validate_required_settings()
    
    def _load_environment(self, env_file: Optional[str] = None) -> None:
        """Load environment variables from file."""
        if env_file:
            env_path = Path(env_file)
            if env_path.exists():
                load_dotenv(env_path)
                logger.info(f"Loaded environment from {env_path}")
                return
            else:
                logger.warning(f"Specified environment file not found: {env_path}")
        
        # Try multiple common locations for .env file
        possible_locations = [
            # Current working directory
            Path.cwd() / ".env",
            # Project root (from script execution)
            Path(__file__).parent.parent.parent / ".env",
            # Two levels up from this file (old structure)
            Path(__file__).parent.parent.parent.parent / ".env",
            # Home directory universal location
            Path.home() / "docker-services-monitoring" / ".env",
        ]
        
        for env_path in possible_locations:
            if env_path.exists():
                load_dotenv(env_path)
                logger.info(f"Loaded environment from {env_path}")
                return
        
        # Log all attempted locations
        attempted_paths = [str(path) for path in possible_locations]
        logger.warning(f"No environment file found. Tried: {', '.join(attempted_paths)}")
    
    def _validate_required_settings(self) -> None:
        """Validate that required settings are present."""
        required_settings = ["SLACK_WEBHOOK_URL"]
        
        missing_settings = []
        for setting in required_settings:
            if not self.get(setting):
                missing_settings.append(setting)
        
        if missing_settings:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing_settings)}"
            )
    
    @property
    def slack_webhook_url(self) -> str:
        """Get Slack webhook URL."""
        return self.get("SLACK_WEBHOOK_URL", required=True)
    
    @property
    def daily_check_time(self) -> str:
        """Get daily check time in HH:MM format."""
        return self.get("DAILY_CHECK_TIME", "09:00")
    
    @property
    def log_level(self) -> str:
        """Get logging level."""
        return self.get("LOG_LEVEL", "INFO")
    
    @property
    def docker_socket(self) -> str:
        """Get Docker socket path."""
        return self.get("DOCKER_SOCKET", "unix://var/run/docker.sock")
    
    @property
    def timezone(self) -> str:
        """Get timezone setting."""
        return self.get("TIMEZONE", "UTC")
    
    @property
    def notification_enabled(self) -> bool:
        """Check if notifications are enabled."""
        return self.get("NOTIFICATION_ENABLED", "true").lower() == "true"
    
    @property
    def include_stopped_containers(self) -> bool:
        """Check if stopped containers should be included."""
        return self.get("INCLUDE_STOPPED_CONTAINERS", "true").lower() == "true"
    
    @property
    def container_name_filter(self) -> Optional[str]:
        """Get container name filter regex pattern."""
        value = self.get("CONTAINER_NAME_FILTER")
        return value if value else None
    
    def get(self, key: str, default: Optional[str] = None, required: bool = False) -> str:
        """
        Get configuration value from environment.
        
        Args:
            key: Environment variable key
            default: Default value if not found
            required: Whether the value is required
            
        Returns:
            Configuration value
            
        Raises:
            ValueError: If required value is not found
        """
        value = os.getenv(key, default)
        
        if required and not value:
            raise ValueError(f"Required environment variable '{key}' not found")
        
        return value or ""
    
    def get_all(self) -> Dict[str, Any]:
        """Get all configuration as dictionary."""
        return {
            "slack_webhook_url": self.slack_webhook_url,
            "daily_check_time": self.daily_check_time,
            "log_level": self.log_level,
            "docker_socket": self.docker_socket,
            "timezone": self.timezone,
            "notification_enabled": self.notification_enabled,
            "include_stopped_containers": self.include_stopped_containers,
            "container_name_filter": self.container_name_filter,
        }