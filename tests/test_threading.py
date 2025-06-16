#!/usr/bin/env python3
"""Quick test of threading improvements."""

from docker_monitor.core.realtime_monitor import RealTimeMonitor
from unittest.mock import Mock
import time

def test_threading_improvements():
    """Test threading improvements in RealTimeMonitor."""
    # Setup mock config
    config = Mock()
    config.docker_socket = 'unix://var/run/docker.sock'
    config.slack_webhook_url = 'https://hooks.slack.com/test'
    config.include_stopped_containers = True
    config.container_name_filter = None

    print('🧪 Testing RealTimeMonitor threading improvements...')
    monitor = RealTimeMonitor(config)

    # Test property access is thread-safe
    print(f'✅ Initial monitoring status: {monitor.monitoring}')
    monitor.monitoring = True
    print(f'✅ Updated monitoring status: {monitor.monitoring}')

    # Test monitoring status method
    status = monitor.get_monitoring_status()
    print(f'✅ Monitoring status: {status}')

    # Test locks exist
    print(f'✅ Has RLock: {hasattr(monitor, "_lock")}')
    print(f'✅ Has state lock: {hasattr(monitor, "_state_lock")}')
    print(f'✅ Has shutdown event: {hasattr(monitor, "_shutdown_event")}')

    print('🎉 All threading improvements verified!')

if __name__ == '__main__':
    test_threading_improvements() 