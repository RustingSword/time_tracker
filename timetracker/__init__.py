"""Time tracker application for monitoring and analyzing user activity."""

import logging.config
from pathlib import Path

from .config import LOGGING_CONFIG
from .logger import ActivityLogger
from .analyzer import ActivityAnalyzer
from .models import WindowInfo, ActivitySummary
from .visualization import ActivityVisualizer

# Configure logging
logging.config.dictConfig(LOGGING_CONFIG)

__version__ = "1.0.0"
__all__ = [
    'ActivityLogger',
    'ActivityAnalyzer',
    'ActivityVisualizer',
    'WindowInfo',
    'ActivitySummary',
]
