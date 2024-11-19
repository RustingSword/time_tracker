#!/usr/bin/env python3

import os
import sys
import contextlib

# Redirect stderr to suppress IMK messages before importing matplotlib
with contextlib.redirect_stderr(open(os.devnull, 'w')):
    import matplotlib.pyplot as plt
    import matplotlib
    matplotlib.use('Agg')  # Use non-interactive backend

import argparse
import json
import logging
import re
import urllib.parse
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional, Tuple

import numpy as np
import pandas as pd
import seaborn as sns
from rich.console import Console
from rich.table import Table

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='activity_analysis.log'
)

console = Console()

# Constants
DEFAULT_CATEGORY_FILE = "app_categories.json"
DEFAULT_LOG_FILE = "activity_log.csv"
UNKNOWN_CATEGORY = "Unknown"
MIN_DURATION_THRESHOLD = 5  # seconds

class ActivityAnalyzer:
    def __init__(self, log_file: str = DEFAULT_LOG_FILE, category_file: str = DEFAULT_CATEGORY_FILE):
        """Initialize the ActivityAnalyzer.

        Args:
            log_file: Path to the activity log CSV file
            category_file: Path to the category mapping JSON file
        """
        self.log_file = Path(log_file)
        self.category_file = Path(category_file)
        self.app_categories = self._load_categories()
        
    def _load_categories(self) -> Dict[str, str]:
        """Load category mappings from JSON file."""
        try:
            if self.category_file.exists():
                with open(self.category_file, "r") as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logging.error(f"Error loading categories: {str(e)}")
            return {}

    def _save_categories(self) -> None:
        """Save category mappings to JSON file."""
        try:
            with open(self.category_file, "w") as f:
                json.dump(self.app_categories, f, indent=4, ensure_ascii=False)
        except Exception as e:
            logging.error(f"Error saving categories: {str(e)}")

    def parse_title(self, row: pd.Series) -> str:
        """Parse the window title to extract meaningful information."""
        if pd.isnull(row["title"]):
            return UNKNOWN_CATEGORY
            
        if "Google Chrome" in row["app_name"]:
            # Extract domain from Chrome window titles
            url_match = re.search(r"https?://[^\s]*", row["title"])
            if url_match:
                try:
                    return urllib.parse.urlparse(url_match.group()).netloc
                except Exception:
                    return "Unknown URL"
            # Handle other Chrome windows (e.g. New Tab, Settings)
            return "Chrome - " + row["title"].split(" - ")[-1]
        elif "Visual Studio Code" in row["app_name"]:
            # Extract file name from VS Code window titles
            parts = row["title"].split(" - ")
            return f"VSCode - {parts[0]}" if parts else "VSCode"
        else:
            return row["app_name"]

    def map_activity_to_category(self, activity: str) -> str:
        """Map an activity to its category, prompting for input if unknown."""
        if activity in self.app_categories:
            return self.app_categories[activity]

        # Show existing categories to help user choose
        existing_categories = set(self.app_categories.values())
        if existing_categories:
            console.print("\nExisting categories:", style="bold blue")
            console.print(", ".join(sorted(existing_categories)))

        category = console.input(f"\n[yellow]Enter the category for activity '{activity}'[/yellow]: ")
        self.app_categories[activity] = category
        self._save_categories()
        return category

    def process_data(self, date: Optional[datetime] = None) -> Tuple[pd.DataFrame, pd.Series]:
        """Process activity data for the specified date.
        
        Args:
            date: Date to analyze. If None, uses today's date.
            
        Returns:
            Tuple of (detailed activity DataFrame, category summary Series)
        """
        try:
            activity_df = pd.read_csv(self.log_file)
        except Exception as e:
            logging.error(f"Error reading activity log: {str(e)}")
            raise

        # Convert timestamp to datetime
        activity_df["date"] = pd.to_datetime(activity_df["timestamp"], unit="s")
        
        # Filter by date
        target_date = pd.Timestamp(date or pd.Timestamp.today()).normalize()
        activity_df = activity_df[activity_df["date"].dt.date == target_date.date()]
        
        if activity_df.empty:
            logging.warning(f"No data found for date: {target_date}")
            return pd.DataFrame(), pd.Series()

        # Calculate durations
        activity_df["duration"] = activity_df["timestamp"].shift(-1) - activity_df["timestamp"]
        activity_df = activity_df[:-1]  # Remove last row (no duration)
        
        # Filter out very short durations (likely noise)
        activity_df = activity_df[activity_df["duration"] >= MIN_DURATION_THRESHOLD]

        # Parse activities and map to categories
        activity_df["activity"] = activity_df.apply(self.parse_title, axis=1)
        activity_df["category"] = activity_df["activity"].apply(self.map_activity_to_category)
        
        # Remove unknown categories if user requested
        activity_df = activity_df[activity_df["category"] != UNKNOWN_CATEGORY]

        # Calculate summary statistics
        category_summary = (
            activity_df.groupby("category")["duration"]
            .agg(['sum', 'count'])
            .sort_values('sum', ascending=False)
        )
        
        category_summary['minutes'] = category_summary['sum'] / 60
        category_summary['percentage'] = (category_summary['sum'] / category_summary['sum'].sum()) * 100

        return activity_df, category_summary

    def generate_insights(self, activity_df: pd.DataFrame) -> None:
        """Generate and print insights from the activity data."""
        if activity_df.empty:
            console.print("No data available for insights", style="yellow")
            return

        console.print("\n[bold blue]Activity Insights:[/bold blue]")
        
        # Most used applications
        top_apps = (
            activity_df.groupby("app_name")["duration"]
            .sum()
            .sort_values(ascending=False)
            .head(5)
        )
        
        console.print("\nTop 5 Applications:")
        for app, duration in top_apps.items():
            console.print(f"  • {app}: {duration/60:.1f} minutes")

        # Time distribution
        activity_df['hour'] = activity_df['date'].dt.hour
        hourly_usage = activity_df.groupby('hour')['duration'].sum() / 60
        
        console.print("\nPeak Activity Hours:")
        peak_hours = hourly_usage.nlargest(3)
        for hour, duration in peak_hours.items():
            console.print(f"  • {hour:02d}:00 - {hour:02d}:59: {duration:.1f} minutes")

    def plot_data(self, category_summary: pd.Series, plot_type: str = "bar") -> None:
        """Create visualizations of the activity data.
        
        Args:
            category_summary: Series containing category summary data
            plot_type: Type of plot ('bar', 'pie', or 'both')
        """
        if category_summary.empty:
            console.print("No data available for plotting", style="yellow")
            return

        # Set style
        plt.style.use('ggplot')  # Using a built-in style that's clean and modern
        
        # Set color palette
        colors = plt.cm.Set3(np.linspace(0, 1, len(category_summary)))
        
        today = pd.Timestamp.today().normalize().date()

        if plot_type in ['bar', 'both']:
            self._plot_bar_chart(category_summary, colors, today)
            if plot_type == 'both':
                self._plot_pie_chart(category_summary, colors, today)

        elif plot_type == 'pie':
            self._plot_pie_chart(category_summary, colors, today)

    def _plot_bar_chart(self, category_summary: pd.Series, colors: np.ndarray, date: datetime.date) -> None:
        """Create a horizontal bar chart of time spent per category."""
        plt.figure(figsize=(12, 6))
        
        # Sort the data for horizontal bar chart
        sorted_data = category_summary['minutes'].sort_values()
        
        # Create bar chart
        ax = plt.gca()
        bars = ax.barh(range(len(sorted_data)), sorted_data.values, color=colors)
        
        # Set category labels
        ax.set_yticks(range(len(sorted_data)))
        ax.set_yticklabels(sorted_data.index)
        
        # Add value labels on bars
        for i, bar in enumerate(bars):
            width = bar.get_width()
            ax.text(width, bar.get_y() + bar.get_height()/2, 
                   f' {width:.1f}m', 
                   va='center')
        
        plt.title(f"Time Spent per Category - {date}", pad=20)
        plt.xlabel("Time (minutes)")
        plt.ylabel("Category")
        
        # Improve grid appearance
        plt.grid(axis="x", alpha=0.3, linestyle='--')
        plt.tight_layout()

        plt.savefig('activity_bar.png', bbox_inches='tight', dpi=300)
        plt.close()

    def _plot_pie_chart(self, category_summary: pd.Series, colors: np.ndarray, date: datetime.date) -> None:
        """Create a pie chart of time distribution by category."""
        plt.figure(figsize=(12, 8))
        
        # Calculate percentages
        total = category_summary['minutes'].sum()
        percentages = (category_summary['minutes'] / total) * 100
        
        # Determine which segments to explode and which to group
        small_threshold = 3  # percentage threshold for small segments
        explode = []
        values = []
        labels = []
        colors_filtered = []
        other_sum = 0
        other_activities = []
        main_categories = []
        
        for i, (cat, minutes) in enumerate(category_summary['minutes'].items()):
            pct = (minutes / total) * 100
            if pct < small_threshold:
                other_sum += minutes
                other_activities.append(f"{cat} ({minutes:.1f}m)")
            else:
                values.append(minutes)
                labels.append(cat)
                colors_filtered.append(colors[i])
                explode.append(0.1 if pct < 10 else 0)
                main_categories.append(f"{cat} ({minutes:.1f}m)")
        
        # Add the "Other" category if there are small segments
        if other_sum > 0:
            values.append(other_sum)
            labels.append("Other")
            colors_filtered.append(plt.cm.Greys(0.5))  # Use grey for "Other"
            explode.append(0.1)
            main_categories.append(f"Other ({other_sum:.1f}m)")

        # Create a mapping of wedge angles to values for accurate labeling
        def make_autopct(values):
            def autopct(pct):
                total_sum = sum(values)
                val = pct * total_sum / 100.0
                return f'{pct:.1f}%\n({val:.1f}m)'
            return autopct
        
        # Create the pie chart
        patches, texts, autotexts = plt.pie(
            values,
            explode=explode,
            labels=labels,
            autopct=make_autopct(values),
            startangle=90,
            colors=colors_filtered,
            shadow=True,
            labeldistance=1.1,  # Move labels further out
            pctdistance=0.75,   # Move percentage labels slightly in
        )
        
        # Enhance the appearance of labels
        plt.setp(autotexts, size=8, weight="bold")
        plt.setp(texts, size=9)
        
        # Create legend with main categories and other details
        legend_labels = main_categories.copy()
        if other_activities:
            legend_labels.append("Small categories:")
            legend_labels.extend([f"  • {act}" for act in other_activities])
        
        plt.legend(
            patches,  # Use all patches including "Other"
            legend_labels,
            title="Categories",
            loc="center left",
            bbox_to_anchor=(1, 0, 0.5, 1),
            fontsize=8
        )
        
        plt.title(f"Time Distribution by Category - {date}", pad=20)
        plt.axis('equal')
        
        # Adjust layout to make room for legend
        plt.tight_layout()

        plt.savefig('activity_pie.png', bbox_inches='tight', dpi=300)
        plt.close()

    def print_summary(self, category_summary: pd.DataFrame) -> None:
        """Print a formatted summary of the activity data."""
        if category_summary.empty:
            console.print("No data available for summary", style="yellow")
            return

        table = Table(title="Activity Summary", show_header=True, header_style="bold magenta")
        table.add_column("Category", style="dim")
        table.add_column("Time (min)", justify="right")
        table.add_column("Activities", justify="right")
        table.add_column("Percentage", justify="right")

        for category, row in category_summary.iterrows():
            table.add_row(
                category,
                f"{row['minutes']:.1f}",
                str(row['count']),
                f"{row['percentage']:.1f}%"
            )

        console.print(table)


def parse_date(date_str: Optional[str] = None) -> Optional[datetime]:
    """Parse date string into datetime object.
    
    Args:
        date_str: Date string in YYYY-MM-DD format, or 'today', 'yesterday'
        
    Returns:
        datetime object or None if date_str is None
    """
    if not date_str or date_str.lower() == 'today':
        return datetime.now()
    elif date_str.lower() == 'yesterday':
        return datetime.now() - timedelta(days=1)
    
    try:
        return datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError as e:
        raise ValueError("Date must be in YYYY-MM-DD format, 'today', or 'yesterday'") from e


def main():
    # Set up argument parser
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
        '--log-file',
        default=DEFAULT_LOG_FILE,
        help=f'Path to activity log file (default: {DEFAULT_LOG_FILE})'
    )
    parser.add_argument(
        '--category-file',
        default=DEFAULT_CATEGORY_FILE,
        help=f'Path to category mapping file (default: {DEFAULT_CATEGORY_FILE})'
    )

    args = parser.parse_args()

    try:
        # Parse the date
        target_date = parse_date(args.date)
        
        # Initialize analyzer with specified files
        analyzer = ActivityAnalyzer(
            log_file=args.log_file,
            category_file=args.category_file
        )
        
        # Process data for the specified date
        activity_df, category_summary = analyzer.process_data(date=target_date)
        
        if not activity_df.empty:
            # Print summary
            console.print(f"\n[bold green]Analysis for {target_date.date()}:[/bold green]")
            analyzer.print_summary(category_summary)
            
            # Generate insights
            analyzer.generate_insights(activity_df)
            
            # Create visualizations
            analyzer.plot_data(category_summary, plot_type=args.output)
        else:
            console.print(f"[yellow]No activity data found for {target_date.date()}[/yellow]")
            
    except ValueError as e:
        console.print(f"[red]Error: {str(e)}[/red]")
    except Exception as e:
        logging.error(f"Error in analysis: {str(e)}")
        console.print(f"[red]Error during analysis: {str(e)}[/red]")


if __name__ == "__main__":
    main()
