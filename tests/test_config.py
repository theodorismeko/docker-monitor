"""Tests for configuration module."""

import pytest
import os
from unittest.mock import patch, MagicMock
from docker_monitor.utils.config import Config


class TestConfig:
    """Test cases for Config class."""
    
    def test_config_initialization_with_required_env(self):
        """Test config initialization with required environment variables."""
        with patch.dict(os.environ, {'SLACK_WEBHOOK_URL': 'https://hooks.slack.com/test'}, clear=True):
            config = Config()
            assert config.slack_webhook_url == 'https://hooks.slack.com/test'
    
    def test_config_missing_required_env_raises_error(self):
        """Test that missing required environment raises ValueError."""
        with patch.dict(os.environ, {}, clear=True):
            with patch('docker_monitor.utils.config.load_dotenv'):  # Prevent .env loading
                with pytest.raises(ValueError, match="Missing required environment variables"):
                    Config()
    
    def test_default_values(self):
        """Test default configuration values."""
        with patch.dict(os.environ, {'SLACK_WEBHOOK_URL': 'https://hooks.slack.com/test'}, clear=True):
            config = Config()
            assert config.daily_check_time == "09:00"
            assert config.log_level == "INFO"
            assert config.notification_enabled is True
            assert config.include_stopped_containers is True
    
    def test_custom_values(self):
        """Test custom configuration values."""
        env_vars = {
            'SLACK_WEBHOOK_URL': 'https://hooks.slack.com/test',
            'DAILY_CHECK_TIME': '14:30',
            'LOG_LEVEL': 'DEBUG',
            'NOTIFICATION_ENABLED': 'false',
            'INCLUDE_STOPPED_CONTAINERS': 'false'
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            config = Config()
            assert config.daily_check_time == "14:30"
            assert config.log_level == "DEBUG"
            assert config.notification_enabled is False
            assert config.include_stopped_containers is False
    
    def test_get_all_returns_dict(self):
        """Test that get_all returns configuration as dictionary."""
        with patch.dict(os.environ, {'SLACK_WEBHOOK_URL': 'https://hooks.slack.com/test'}, clear=True):
            config = Config()
            config_dict = config.get_all()
            assert isinstance(config_dict, dict)
            assert 'slack_webhook_url' in config_dict
            assert 'log_level' in config_dict 