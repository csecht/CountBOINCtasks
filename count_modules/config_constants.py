"""
Constants used in __main__.
"""
import sys

# MY_OS is used throughout the main program and local modules.
MY_OS = sys.platform[:3]

# strftime formats:
LONG_FMT = '%Y-%b-%d %H:%M:%S'
SHORT_FMT = '%Y %b %d %H:%M'
SHORTER_FMT = '%b %d %H:%M'
DAY_FMT = '%A %H:%M'
NOTICE_INTERVAL = 15  # <- time.sleep() seconds

FONT_MAP = {
    'dar': ('SF Pro', 14),  # macOS
    'lin': ('DejaVu Sans', 10),  # Linux (Ubuntu)
    'win': ('Segoe UI', 10)  # Windows (10, 11)
}

# Defaults to generic font if OS is not recognized
LABEL_FONT = FONT_MAP.get(MY_OS, ('Arial', 10))

# Set colors for row labels and data display.
# These colors are compatible with red-green color-blindness.
ROW_FG = 'LightYellow'  # Row header label fg.
MASTER_BG = 'SteelBlue4'  # app and header label bg.
DATA_BG = 'grey40'  # Data labels and data frame bg.
HIGHLIGHT = 'gold1'  # Notices, compliments, highlight fg.
EMPHASIZE = 'grey90'  # Lighter data label fg, use for grey-out.
DEEMPHASIZE = 'grey60'  # Darker data label fg.
