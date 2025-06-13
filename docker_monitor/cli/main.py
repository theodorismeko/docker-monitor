"""Main CLI entry point for Docker Monitor."""

import sys
import argparse
from typing import Optional

from ..core.monitor import DockerMonitor
from ..utils.config import Config
from ..utils.logging_config import get_logger

logger = get_logger(__name__)


def create_argument_parser() -> argparse.ArgumentParser:
    """Create and configure argument parser."""
    parser = argparse.ArgumentParser(
        description="Docker Container Monitoring with Slack Integration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=
        """
                Examples:
                %(prog)s --once                    # Run once and exit
                %(prog)s --scheduled               # Run with daily scheduling
                %(prog)s --continuous 5            # Run continuously every 5 minutes
                %(prog)s --test                    # Test connections only
                %(prog)s --status                  # Show status summary
                %(prog)s --test-notification       # Send test notification
        """
    )
    
    # Execution modes (mutually exclusive)
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument(
        '--once',
        action='store_true',
        help='Run monitoring check once and exit'
    )
    mode_group.add_argument(
        '--scheduled',
        action='store_true',
        help='Run with daily scheduling (default: 09:00)'
    )
    mode_group.add_argument(
        '--continuous',
        type=int,
        metavar='MINUTES',
        help='Run continuously with specified interval in minutes'
    )
    mode_group.add_argument(
        '--test',
        action='store_true',
        help='Test Docker and Slack connections only'
    )
    mode_group.add_argument(
        '--status',
        action='store_true',
        help='Show current status summary'
    )
    mode_group.add_argument(
        '--test-notification',
        action='store_true',
        help='Send test notification to Slack'
    )
    
    # Configuration options
    parser.add_argument(
        '--config',
        type=str,
        metavar='PATH',
        help='Path to environment file (.env)'
    )
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        help='Set logging level (overrides config)'
    )
    parser.add_argument(
        '--no-notifications',
        action='store_true',
        help='Disable Slack notifications'
    )
    parser.add_argument(
        '--include-stopped',
        action='store_true',
        default=True,
        help='Include stopped containers in reports (default: True)'
    )
    parser.add_argument(
        '--exclude-stopped',
        action='store_true',
        help='Exclude stopped containers from reports'
    )
    parser.add_argument(
        '--filter',
        type=str,
        metavar='PATTERN',
        help='Regex pattern to filter container names'
    )
    
    # Verbose output
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose output'
    )
    
    return parser


def handle_test_mode(monitor: DockerMonitor) -> int:
    """Handle test mode execution."""
    print("🧪 Testing Docker Monitor connections...\n")
    
    results = monitor.test_connections()
    
    print("Connection Test Results:")
    print("=" * 50)
    
    for service, success in results.items():
        status = "✅ SUCCESS" if success else "❌ FAILED"
        print(f"{service.title():<15} {status}")
    
    all_success = all(results.values())
    
    if all_success:
        print("\n🎉 All connections successful!")
        return 0
    else:
        print("\n⚠️  Some connections failed. Check configuration and logs.")
        return 1


def handle_status_mode(monitor: DockerMonitor) -> int:
    """Handle status summary mode."""
    print("📊 Docker Monitor Status Summary\n")
    
    status = monitor.get_status_summary()
    
    if 'error' in status:
        print(f"❌ Error getting status: {status['error']}")
        return 1
    
    print("System Information:")
    print("=" * 50)
    
    # System info
    system_info = status.get('system_info', {})
    print(f"Docker Version:     {system_info.get('server_version', 'unknown')}")
    print(f"Operating System:   {system_info.get('operating_system', 'unknown')}")
    print(f"Architecture:       {system_info.get('architecture', 'unknown')}")
    print(f"CPUs:              {system_info.get('cpus', 'unknown')}")
    
    # Container summary
    print(f"\nContainer Summary:")
    print("=" * 50)
    print(f"Total Containers:   {status.get('total_containers', 0)}")
    
    status_counts = status.get('status_counts', {})
    for container_status, count in status_counts.items():
        print(f"{container_status.title():<15} {count}")
    
    # Connection status
    print(f"\nConnections:")
    print("=" * 50)
    connections = status.get('connections', {})
    for service, success in connections.items():
        status_text = "✅ Connected" if success else "❌ Disconnected"
        print(f"{service.title():<15} {status_text}")
    
    return 0


def handle_test_notification_mode(monitor: DockerMonitor) -> int:
    """Handle test notification mode."""
    print("📤 Sending test notification to Slack...")
    
    success = monitor.send_test_notification()
    
    if success:
        print("✅ Test notification sent successfully!")
        return 0
    else:
        print("❌ Failed to send test notification. Check logs for details.")
        return 1


def main(argv: Optional[list] = None) -> int:
    """
    Main CLI entry point.
    
    Args:
        argv: Command line arguments (defaults to sys.argv)
        
    Returns:
        Exit code (0 for success, non-zero for error)
    """
    parser = create_argument_parser()
    args = parser.parse_args(argv)
    
    try:
        # Create configuration
        config = Config(env_file=args.config)
        
        # Override configuration with command line arguments
        if args.log_level:
            import os
            os.environ['LOG_LEVEL'] = args.log_level
            config = Config(env_file=args.config)  # Recreate to pick up changes
        
        if args.no_notifications:
            import os
            os.environ['NOTIFICATION_ENABLED'] = 'false'
            config = Config(env_file=args.config)
        
        if args.exclude_stopped:
            import os
            os.environ['INCLUDE_STOPPED_CONTAINERS'] = 'false'
            config = Config(env_file=args.config)
        
        if args.filter:
            import os
            os.environ['CONTAINER_NAME_FILTER'] = args.filter
            config = Config(env_file=args.config)
        
        # Initialize monitor
        monitor = DockerMonitor(config)
        
        # Handle different execution modes
        if args.test:
            return handle_test_mode(monitor)
        
        elif args.status:
            return handle_status_mode(monitor)
        
        elif args.test_notification:
            return handle_test_notification_mode(monitor)
        
        elif args.once:
            logger.info("Running single monitoring check...")
            success = monitor.run_check()
            return 0 if success else 1
        
        elif args.scheduled:
            logger.info("Starting scheduled monitoring...")
            monitor.run_scheduled()
            return 0
        
        elif args.continuous:
            if args.continuous < 1:
                print("❌ Continuous interval must be at least 1 minute")
                return 1
            
            logger.info(f"Starting continuous monitoring (every {args.continuous} minutes)...")
            monitor.monitor_containers_continuously(args.continuous)
            return 0
        
        else:
            parser.print_help()
            return 1
    
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        return 0
    
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main()) 