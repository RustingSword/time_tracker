"""Data models for the time tracker application."""

from dataclasses import dataclass
from typing import Optional, Dict
import time

@dataclass
class WindowInfo:
    """Information about a window activity."""
    app_name: str
    title: str
    timestamp: Optional[int] = None

    def to_dict(self) -> Dict[str, str]:
        """Convert the window info to a dictionary for CSV storage."""
        return {
            "app_name": self.app_name,
            "title": self.title,
            "timestamp": str(self.timestamp or int(time.time()))
        }

@dataclass
class ActivitySummary:
    """Summary of activity data."""
    category: str
    minutes: float
    count: int
    percentage: float

    @classmethod
    def from_series(cls, category: str, series: 'pd.Series') -> 'ActivitySummary':
        """Create an ActivitySummary from a pandas Series."""
        return cls(
            category=category,
            minutes=series['minutes'],
            count=series['count'],
            percentage=series['percentage']
        )
