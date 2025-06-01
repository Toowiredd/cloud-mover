#!/usr/bin/env python3
"""
Cloud Mover - Main Entry Point
Free up disk space by moving folders to Google Drive
"""

import sys
import os

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from ui.main_window import CloudMoverUI


def main():
    """Main application entry point."""
    try:
        app = CloudMoverUI()
        app.run()
    except Exception as e:
        print(f"Error starting Cloud Mover: {e}")
        input("Press Enter to exit...")
        sys.exit(1)


if __name__ == '__main__':
    main()