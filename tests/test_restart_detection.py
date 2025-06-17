#!/usr/bin/env python3
"""
Test script to demonstrate restart detection functionality.
"""

import time
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from docker_monitor.core.docker_monitor import DockerMonitor
from docker_monitor.utils.config import Config

def main():
    """Test restart detection functionality."""
    print("🔄 Docker Monitor - Restart Detection Test")
    print("=" * 50)
    
    try:
        # Initialize monitor
        config = Config()
        monitor = DockerMonitor(config)
        
        # Test restart detection
        print("\n1. Testing restart detection functionality...")
        success = monitor.test_restart_detection()
        
        if success:
            print("✅ Restart detection test completed successfully")
        else:
            print("❌ Restart detection test failed")
            return 1
        
        print("\n2. Current container status:")
        status = monitor.get_status_summary()
        
        total = status.get('total_containers', 0)
        print(f"   Total containers: {total}")
        
        status_counts = status.get('status_counts', {})
        for status_name, count in status_counts.items():
            print(f"   {status_name}: {count}")
        
        print("\n3. To test restart notifications:")
        print("   - Start real-time monitoring: docker compose --profile realtime up -d")
        print("   - Restart a container: docker restart <container_name>")
        print("   - Check Slack for restart notification")
        
        print("\n✅ Test completed successfully!")
        return 0
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 