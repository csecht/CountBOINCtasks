"""
Constants used in __main__.
"""

import count_modules.platform_check as chk

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
LABEL_FONT = FONT_MAP.get(chk.MY_OS, ('Arial', 10))
