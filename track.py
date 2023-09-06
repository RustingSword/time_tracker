import atexit
import csv
import os
import time

import pymonctl as pmc
import pywinctl as pwc


class ActivityLogger:
    def __init__(self, log_interval=10, log_file="activity_log.csv"):
        self.log_interval = log_interval
        self.log_file = log_file
        self.active_window = None
        self.prev_info = None
        self.prev_mouse_pos = None  # HACK use mouse position to check if user's away
        self.prev_action_ts = None

    def get_window_info(self):
        window = pwc.getActiveWindow()
        if window is not None:
            app_name = window.getAppName()
            title = pwc.getActiveWindowTitle()
            return {"app_name": app_name, "title": title}

    def log_window_info(self, info):
        with open(self.log_file, "a", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=info.keys())
            writer.writerow(info)
        self.prev_action_ts = int(time.time())

    def initialize_log_file(self):
        if os.path.isfile(self.log_file):
            return
        with open(self.log_file, "w", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=["app_name", "title", "timestamp"])
            writer.writeheader()

    def run(self):
        self.initialize_log_file()
        self.prev_mouse_pos = pmc.getMousePos()
        while True:
            mouse_pos = pmc.getMousePos()
            current_action_ts = int(time.time())
            if mouse_pos == self.prev_mouse_pos:
                if self.prev_action_ts is not None and current_action_ts - self.prev_action_ts > 600:
                    self.pause()
                    time.sleep(self.log_interval)
                    continue
            self.prev_mouse_pos = mouse_pos

            current_info = self.get_window_info()
            if current_info is not None and current_info != self.prev_info:
                timestamp = int(time.time())
                info = current_info.copy()
                info["timestamp"] = int(time.time())
                self.log_window_info(info)
                self.prev_info = current_info
            time.sleep(self.log_interval)

    def pause(self):
        if self.prev_info["app_name"] == "_pause":  # only pause once
            return
        pause_info = {"app_name": "_pause", "title": "", "timestamp": int(time.time())}
        self.log_window_info(pause_info)
        self.prev_info = pause_info

    def exit(self):
        final_info = {"app_name": "_exit", "title": "", "timestamp": int(time.time())}
        self.log_window_info(final_info)


if __name__ == "__main__":
    logger = ActivityLogger()
    atexit.register(logger.exit)
    logger.run()
