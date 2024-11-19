"""Activity logging module for the time tracker application."""

import csv
import logging
import time
from pathlib import Path
from typing import Optional, Tuple

import pymonctl as pmc
import pywinctl as pwc

from .config import (
    ACTIVITY_FIELDS,
    DEFAULT_LOG_INTERVAL,
    INACTIVITY_THRESHOLD,
    LOGGING_CONFIG
)
from .models import WindowInfo

logger = logging.getLogger('timetracker.logger')


class ActivityLogger:
    """Logs user activity by tracking active windows and mouse movement."""
    
    def __init__(self, log_file: Path, log_interval: int = DEFAULT_LOG_INTERVAL):
        """Initialize the activity logger.
        
        Args:
            log_file: Path to the CSV log file
            log_interval: Time between checks in seconds
        """
        self.log_file = log_file
        self.log_interval = log_interval
        self.prev_info: Optional[WindowInfo] = None
        self.prev_mouse_pos: Optional[Tuple[int, int]] = None
        self.prev_action_ts: Optional[int] = None
        
        logger.info("ActivityLogger initialized with interval: %d seconds", log_interval)

    def get_window_info(self) -> Optional[WindowInfo]:
        """Get information about the currently active window."""
        try:
            window = pwc.getActiveWindow()
            if window is not None:
                return WindowInfo(
                    app_name=window.getAppName(),
                    title=pwc.getActiveWindowTitle()
                )
        except Exception as e:
            logger.error("Error getting window info: %s", str(e))
        return None

    def log_window_info(self, info: WindowInfo) -> None:
        """Log window information to the CSV file."""
        try:
            with open(self.log_file, "a", newline="") as file:
                writer = csv.DictWriter(file, fieldnames=ACTIVITY_FIELDS)
                writer.writerow(info.to_dict())
            self.prev_action_ts = int(time.time())
            logger.info("Logged activity: %s - %s", info.app_name, info.title)
        except Exception as e:
            logger.error("Error logging window info: %s", str(e))

    def initialize_log_file(self) -> None:
        """Initialize the log file if it doesn't exist."""
        try:
            if not self.log_file.exists():
                with open(self.log_file, "w", newline="") as file:
                    writer = csv.DictWriter(file, fieldnames=ACTIVITY_FIELDS)
                    writer.writeheader()
                logger.info("Created new log file: %s", str(self.log_file))
        except Exception as e:
            logger.error("Error initializing log file: %s", str(e))
            raise

    def is_user_inactive(self, current_mouse_pos: Tuple[int, int], current_time: int) -> bool:
        """Check if the user is inactive based on mouse movement and time."""
        if current_mouse_pos == self.prev_mouse_pos:
            if self.prev_action_ts and current_time - self.prev_action_ts > INACTIVITY_THRESHOLD:
                return True
        return False

    def run(self) -> None:
        """Main loop to track and log window activity."""
        self.initialize_log_file()
        self.prev_mouse_pos = pmc.getMousePos()
        
        logger.info("Starting activity tracking")
        
        while True:
            try:
                current_mouse_pos = pmc.getMousePos()
                current_time = int(time.time())

                if self.is_user_inactive(current_mouse_pos, current_time):
                    self.pause()
                    time.sleep(self.log_interval)
                    continue

                self.prev_mouse_pos = current_mouse_pos
                current_info = self.get_window_info()

                if current_info and (not self.prev_info or 
                                   current_info.app_name != self.prev_info.app_name or 
                                   current_info.title != self.prev_info.title):
                    current_info.timestamp = current_time
                    self.log_window_info(current_info)
                    self.prev_info = current_info

            except Exception as e:
                logger.error("Error in main loop: %s", str(e))
                time.sleep(self.log_interval)
            else:
                time.sleep(self.log_interval)

    def pause(self) -> None:
        """Log a pause in activity."""
        if self.prev_info and self.prev_info.app_name == "_pause":
            return
            
        pause_info = WindowInfo(app_name="_pause", title="", timestamp=int(time.time()))
        self.log_window_info(pause_info)
        self.prev_info = pause_info
        logger.info("Activity paused due to inactivity")

    def exit(self) -> None:
        """Log program exit."""
        exit_info = WindowInfo(app_name="_exit", title="", timestamp=int(time.time()))
        self.log_window_info(exit_info)
        logger.info("ActivityLogger shutting down")
