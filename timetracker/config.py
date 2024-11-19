"""Configuration settings for the time tracker application."""

from pathlib import Path
from dataclasses import dataclass
from typing import Dict

# File paths and names
DEFAULT_LOG_FILE = "activity_log.csv"
DEFAULT_CATEGORY_FILE = "app_categories.json"
LOG_FILE = Path(DEFAULT_LOG_FILE)
CATEGORY_FILE = Path(DEFAULT_CATEGORY_FILE)

# Time intervals and thresholds
DEFAULT_LOG_INTERVAL = 10  # seconds
INACTIVITY_THRESHOLD = 600  # 10 minutes in seconds
MIN_DURATION_THRESHOLD = 5  # seconds

# CSV field names
ACTIVITY_FIELDS = ["app_name", "title", "timestamp"]

# Categories
UNKNOWN_CATEGORY = "Unknown"

# Visualization settings
@dataclass
class VisualizationConfig:
    """Configuration for visualization settings."""
    figure_size_bar: tuple[int, int] = (12, 6)
    figure_size_pie: tuple[int, int] = (12, 8)
    small_segment_threshold: float = 3.0  # percentage
    style: str = 'ggplot'
    dpi: int = 300

# Logging configuration
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        },
    },
    'handlers': {
        'file': {
            'class': 'logging.FileHandler',
            'filename': 'timetracker.log',
            'formatter': 'standard',
        },
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'standard',
        },
    },
    'loggers': {
        'timetracker': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True
        }
    }
}
