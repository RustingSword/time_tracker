# Time Tracker

A cross-platform desktop time tracker based on active window tracking. This tool helps you understand how you spend your time by monitoring active windows and generating insightful visualizations.

## Features

- Automatic window activity tracking
- Categorization of activities with interactive prompts
- Rich visualizations (pie charts and bar charts)
- Detailed activity summaries and insights
- Browser URL tracking support
- Inactivity detection and logging

## Installation

### Prerequisites

If you want to track URLs in browsers, install these extensions:
- Chrome: [URL in title](https://chrome.google.com/webstore/detail/url-in-title/ignpacbgnbnkaiooknalneoeladjnfgb)
- Firefox: [Add URL to Window Title](https://addons.mozilla.org/en-US/firefox/addon/add-url-to-window-title/)

### Install from Source

```bash
git clone https://github.com/RustingSword/time_tracker.git
cd time_tracker
pip install -e .
```

## Usage

### Track Your Time

Start the activity tracker:
```bash
track
```

Options:
- `-i, --interval`: Set logging interval in seconds (default: 10)
- `-l, --log-file`: Specify log file path (default: activity_log.csv)

### Analyze Your Time

Analyze tracked activities:
```bash
analyze
```

Options:
- `-d, --date`: Date to analyze (YYYY-MM-DD, 'today', or 'yesterday')
- `-o, --output`: Visualization type ('bar', 'pie', or 'both')
- `-l, --log-file`: Input log file path
- `-c, --category-file`: Category mapping file path

The tool will:
1. Generate an activity summary table
2. Show insights about most used applications
3. Display peak activity hours
4. Create visualizations (saved as PNG files)

### Configuration

Activity categories are stored in `app_categories.json`. When a new application is encountered, you'll be prompted to categorize it. You can also manually edit this file:

```json
{
    "Google Chrome": "browsing",
    "Visual Studio Code": "programming",
    "Terminal": "development"
}
```

## Development

The project is structured as follows:
```
timetracker/
├── timetracker/
│   ├── __init__.py
│   ├── analyzer.py     # Activity analysis logic
│   ├── config.py       # Configuration settings
│   ├── logger.py       # Activity tracking logic
│   ├── models.py       # Data models
│   └── visualization.py # Visualization tools
├── analyze.py          # Analysis CLI
├── track.py           # Tracking CLI
├── setup.py          # Package setup
└── README.md
```

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
