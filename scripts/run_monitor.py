#!/usr/bin/env python3
"""
Docker Monitor - Main execution script

This script provides the main entry point for running the Docker Monitor.
It can be executed directly or used with the package structure.
"""

import sys
import os
from pathlib import Path

# Add the project root to Python path to allow imports
script_dir = Path(__file__).parent
project_root = script_dir.parent

if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

try:
    from docker_monitor.cli.main import main
except ImportError as e:
    print(f"❌ Failed to import Docker Monitor: {e}")
    print(f"Current working directory: {os.getcwd()}")
    print(f"Script directory: {script_dir}")
    print(f"Project root: {project_root}")
    print("\nPossible solutions:")
    print("1. Install dependencies: pip install -r requirements.txt")
    print("2. Run from project root directory")
    print("3. Install the package: pip install -e .")
    sys.exit(1)

if __name__ == "__main__":
    sys.exit(main()) 