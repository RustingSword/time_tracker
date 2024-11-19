#!/usr/bin/env python3

import atexit
import argparse
from pathlib import Path

from timetracker import ActivityLogger
from timetracker.config import DEFAULT_LOG_FILE, DEFAULT_LOG_INTERVAL

def main():
    """Main entry point for the activity tracker."""
    parser = argparse.ArgumentParser(description='Track user activity.')
    parser.add_argument(
        '--interval', '-i',
        type=int,
        default=DEFAULT_LOG_INTERVAL,
        help=f'Logging interval in seconds (default: {DEFAULT_LOG_INTERVAL})'
    )
    parser.add_argument(
        '--log-file', '-l',
        type=Path,
        default=DEFAULT_LOG_FILE,
        help=f'Path to log file (default: {DEFAULT_LOG_FILE})'
    )
    args = parser.parse_args()

    try:
        logger = ActivityLogger(args.log_file, args.interval)
        atexit.register(logger.exit)
        logger.run()
    except KeyboardInterrupt:
        print("\nStopping activity tracker...")
    except Exception as e:
        print(f"Error: {str(e)}")
        raise

if __name__ == "__main__":
    main()
