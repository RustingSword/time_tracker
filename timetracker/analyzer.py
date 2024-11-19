"""Activity analysis module for the time tracker application."""

import json
import logging
import re
import urllib.parse
from datetime import datetime, date
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd
from rich.console import Console
from rich.table import Table

from .config import (
    UNKNOWN_CATEGORY,
    MIN_DURATION_THRESHOLD,
    VisualizationConfig
)
from .models import ActivitySummary
from .visualization import ActivityVisualizer

logger = logging.getLogger('timetracker.analyzer')
console = Console()


class ActivityAnalyzer:
    """Analyzes time tracking data and generates insights."""

    def __init__(self, log_file: Path, category_file: Path):
        """Initialize the analyzer.
        
        Args:
            log_file: Path to the activity log CSV file
            category_file: Path to the category mapping JSON file
        """
        self.log_file = log_file
        self.category_file = category_file
        self.app_categories = self._load_categories()
        self.visualizer = ActivityVisualizer()

    def _load_categories(self) -> Dict[str, str]:
        """Load category mappings from JSON file."""
        try:
            if self.category_file.exists():
                with open(self.category_file, "r") as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.error("Error loading categories: %s", str(e))
            return {}

    def _save_categories(self) -> None:
        """Save category mappings to JSON file."""
        try:
            with open(self.category_file, "w") as f:
                json.dump(self.app_categories, f, indent=4, ensure_ascii=False)
        except Exception as e:
            logger.error("Error saving categories: %s", str(e))

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

        category = console.input(f"\n[yellow]Enter category for '{activity}'[/yellow]: ")
        self.app_categories[activity] = category
        self._save_categories()
        return category

    def process_data(self, target_date: Optional[date] = None) -> Tuple[pd.DataFrame, List[ActivitySummary]]:
        """Process activity data for the specified date."""
        try:
            activity_df = pd.read_csv(self.log_file)
        except Exception as e:
            logger.error("Error reading activity log: %s", str(e))
            raise

        # Convert timestamp to datetime
        activity_df["date"] = pd.to_datetime(activity_df["timestamp"], unit="s")
        
        # Filter by date
        target_date = target_date or date.today()
        activity_df = activity_df[activity_df["date"].dt.date == target_date]
        
        if activity_df.empty:
            logger.warning(f"No data found for date: {target_date}")
            return pd.DataFrame(), []

        # Calculate durations
        activity_df["duration"] = activity_df["timestamp"].shift(-1) - activity_df["timestamp"]
        activity_df = activity_df[:-1]  # Remove last row (no duration)
        
        # Filter out very short durations
        activity_df = activity_df[activity_df["duration"] >= MIN_DURATION_THRESHOLD]

        # Parse activities and map to categories
        activity_df["activity"] = activity_df.apply(self.parse_title, axis=1)
        activity_df["category"] = activity_df["activity"].apply(self.map_activity_to_category)
        
        # Remove unknown categories
        activity_df = activity_df[activity_df["category"] != UNKNOWN_CATEGORY]

        # Calculate summary statistics
        summary_df = (
            activity_df.groupby("category")["duration"]
            .agg(['sum', 'count'])
            .sort_values('sum', ascending=False)
        )
        
        total_duration = summary_df['sum'].sum()
        summaries = []
        
        for category, row in summary_df.iterrows():
            summaries.append(ActivitySummary(
                category=category,
                minutes=row['sum'] / 60,
                count=row['count'],
                percentage=(row['sum'] / total_duration) * 100
            ))

        return activity_df, summaries

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

        # Time distribution by hour
        activity_df['hour'] = activity_df['date'].dt.hour
        hourly_usage = activity_df.groupby('hour')['duration'].sum() / 60
        
        console.print("\nPeak Activity Hours:")
        peak_hours = hourly_usage.nlargest(3)
        for hour, duration in peak_hours.items():
            console.print(f"  • {hour:02d}:00 - {hour:02d}:59: {duration:.1f} minutes")

    def print_summary(self, summaries: List[ActivitySummary]) -> None:
        """Print a formatted summary of the activity data."""
        if not summaries:
            console.print("No data available for summary", style="yellow")
            return

        table = Table(title="Activity Summary", show_header=True, header_style="bold magenta")
        table.add_column("Category", style="dim")
        table.add_column("Time (min)", justify="right")
        table.add_column("Activities", justify="right")
        table.add_column("Percentage", justify="right")

        for summary in summaries:
            table.add_row(
                summary.category,
                f"{summary.minutes:.1f}",
                str(summary.count),
                f"{summary.percentage:.1f}%"
            )

        console.print(table)

    def analyze(self, target_date: Optional[date] = None, plot_type: str = 'both') -> None:
        """Analyze activity data and generate visualizations."""
        activity_df, summaries = self.process_data(target_date)
        
        if not summaries:
            console.print(f"No activity data found for {target_date or 'today'}")
            return
            
        self.print_summary(summaries)
        self.generate_insights(activity_df)
        self.visualizer.create_visualizations(summaries, target_date or date.today(), plot_type)
