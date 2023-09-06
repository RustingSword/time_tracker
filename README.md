# Time Tracker

A cross-platform desktop time tracker based on active window tracking.

## Dependency

- [PyMonCtl](https://pypi.org/project/PyMonCtl/)
- [PyWinCtl](https://pypi.org/project/PyWinCtl/)

If you want to differentiate each webpage and track fine-grained time usage in browsers, you'll need to install extensions to insert URL to tab titles.

- For Chrome, there's [URL in title](https://chrome.google.com/webstore/detail/url-in-title/ignpacbgnbnkaiooknalneoeladjnfgb)
- For Firefox, there's [Add URL to Window Title](https://addons.mozilla.org/en-US/firefox/addon/add-url-to-window-title/)

## Usage

- Track your time usage: run `python track.py`, and the tracked activity logs will be written into `activity_log.csv`.
- Analyze your time usage: run `python analyze.py`, and it will plot the time spent in each activity category (requires `matplotlib` and `pandas`). The mapping from active window name to activity category is saved in `app_categories.json`, which can be manually edited. If a window has no mapping found, the script will ask for it, then save the mapping automatically in the file.

## Todo

- More advanced data analysis features, such as by each day/week/month etc.
