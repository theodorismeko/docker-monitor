"""
Docker Monitor - Legacy entry point

This file provides backward compatibility for existing scripts.
The main functionality has been moved to a properly structured package.

For new implementations, please use:
- docker_monitor.cli.main for CLI functionality
- docker_monitor.core.monitor.DockerMonitor for the main class
- scripts/run_monitor.py for the recommended script execution
"""

import sys
import warnings

# Issue deprecation warning
warnings.warn(
    "Using docker_monitor.py directly is deprecated. "
    "Please use 'scripts/run_monitor.py' or install the package and use 'docker-monitor' command.",
    DeprecationWarning,
    stacklevel=2
)

try:
    from cli.main import main
    
    if __name__ == "__main__":
        print("⚠️  Using deprecated entry point. Please use 'scripts/run_monitor.py' instead.")
        sys.exit(main())
        
except ImportError:
    print("❌ New module structure not found. Please run 'scripts/run_monitor.py' instead.")
    sys.exit(1)
