"""Tests for Slack integration module."""

import pytest
from unittest.mock import patch, MagicMock
import requests
from docker_monitor.integrations.slack import SlackNotifier


class TestSlackNotifier:
    """Test cases for SlackNotifier class."""
    
    def test_slack_notifier_initialization(self):
        """Test SlackNotifier initialization with valid webhook URL."""
        webhook_url = "https://hooks.slack.com/services/test"
        notifier = SlackNotifier(webhook_url)
        assert notifier.webhook_url == webhook_url
    
    def test_slack_notifier_initialization_empty_url_raises_error(self):
        """Test that empty webhook URL raises ValueError."""
        with pytest.raises(ValueError, match="Slack webhook URL is required"):
            SlackNotifier("")
    
    @patch('requests.post')
    def test_send_container_report_success(self, mock_post):
        """Test successful container report sending."""
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        notifier = SlackNotifier("https://hooks.slack.com/services/test")
        container_info = [
            {
                "name": "test-container",
                "status": "running",
                "image": "nginx:latest",
                "id": "abc123",
                "ports": "80:80/tcp"
            }
        ]
        
        result = notifier.send_container_report(container_info)
        
        assert result is True
        mock_post.assert_called_once()
        assert mock_post.call_args[0][0] == "https://hooks.slack.com/services/test"
    
    @patch('requests.post')
    def test_send_container_report_failure(self, mock_post):
        """Test container report sending failure."""
        mock_post.side_effect = requests.RequestException("Network error")
        
        notifier = SlackNotifier("https://hooks.slack.com/services/test")
        container_info = [{"name": "test", "status": "running"}]
        
        result = notifier.send_container_report(container_info)
        
        assert result is False
    
    @patch('requests.post')
    def test_send_error_notification_success(self, mock_post):
        """Test successful error notification sending."""
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        notifier = SlackNotifier("https://hooks.slack.com/services/test")
        
        result = notifier.send_error_notification("Test error", "Test context")
        
        assert result is True
        mock_post.assert_called_once()
    
    @patch('requests.post')
    def test_send_custom_message_success(self, mock_post):
        """Test successful custom message sending."""
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        notifier = SlackNotifier("https://hooks.slack.com/services/test")
        
        result = notifier.send_custom_message("Test Title", "Test Message", "good")
        
        assert result is True
        mock_post.assert_called_once()
    
    def test_get_status_emoji(self):
        """Test status emoji mapping."""
        notifier = SlackNotifier("https://hooks.slack.com/services/test")
        
        assert notifier._get_status_emoji("running") == "✅"
        assert notifier._get_status_emoji("exited") == "❌"
        assert notifier._get_status_emoji("stopped") == "⏹️"
        assert notifier._get_status_emoji("unknown") == "⚠️"
    
    def test_count_containers_by_status(self):
        """Test container status counting."""
        notifier = SlackNotifier("https://hooks.slack.com/services/test")
        
        container_info = [
            {"status": "running"},
            {"status": "running"},
            {"status": "exited"},
            {"status": "stopped"}
        ]
        
        result = notifier._count_containers_by_status(container_info)
        
        assert result == {"running": 2, "exited": 1, "stopped": 1}
    
    def test_format_container_details(self):
        """Test container details formatting."""
        notifier = SlackNotifier("https://hooks.slack.com/services/test")
        
        container = {
            "name": "test-container",
            "status": "running",
            "image": "nginx:latest",
            "id": "abc123",
            "ports": "80:80/tcp",
            "health_status": "healthy"
        }
        
        result = notifier._format_container_details(container)
        
        assert "test-container" in result
        assert "running" in result
        assert "nginx:latest" in result
        assert "healthy" in result
    
    @patch('requests.post')
    def test_test_connection(self, mock_post):
        """Test connection testing."""
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        notifier = SlackNotifier("https://hooks.slack.com/services/test")
        
        result = notifier.test_connection()
        
        assert result is True
        mock_post.assert_called_once() 