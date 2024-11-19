#!/usr/bin/env python3

import argparse
from datetime import datetime, timedelta
from pathlib import Path

from timetracker import ActivityAnalyzer
from timetracker.config import DEFAULT_LOG_FILE, DEFAULT_CATEGORY_FILE


def parse_date(date_str: str = 'today') -> datetime:
    """Parse date string into datetime object."""
    if not date_str or date_str.lower() == 'today':
        return datetime.now()
    elif date_str.lower() == 'yesterday':
        return datetime.now() - timedelta(days=1)
    
    try:
        return datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError as e:
        raise ValueError("Date must be in YYYY-MM-DD format, 'today', or 'yesterday'") from e


def main():
    """Main entry point for activity analysis."""
    parser = argparse.ArgumentParser(description='Analyze time tracking data.')
    parser.add_argument(
        '--date', '-d',
        help="Date to analyze (YYYY-MM-DD format, 'today', or 'yesterday'). Defaults to today.",
        default='today'
    )
    parser.add_argument(
        '--output', '-o',
        choices=['bar', 'pie', 'both'],
        default='both',
        help='Type of visualization output (default: both)'
    )
    parser.add_argument(
        '--log-file', '-l',
        type=Path,
        default=DEFAULT_LOG_FILE,
        help=f'Path to activity log file (default: {DEFAULT_LOG_FILE})'
    )
    parser.add_argument(
        '--category-file', '-c',
        type=Path,
        default=DEFAULT_CATEGORY_FILE,
        help=f'Path to category mapping file (default: {DEFAULT_CATEGORY_FILE})'
    )
    args = parser.parse_args()

    try:
        target_date = parse_date(args.date)
        analyzer = ActivityAnalyzer(args.log_file, args.category_file)
        analyzer.analyze(target_date.date(), args.output)
    except Exception as e:
        print(f"Error: {str(e)}")
        raise


if __name__ == "__main__":
    main()
