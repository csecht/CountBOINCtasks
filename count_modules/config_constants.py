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

# Fonts for various widgets. Make it os-specific instead of using
#  Tkinter's default named fonts because they can change and affect spacing.
if chk.MY_OS == 'dar':  # macOS
    LABEL_FONT = ('SF Pro', 14)
elif chk.MY_OS == 'lin':  # Linux (Ubuntu)
    LABEL_FONT = ('DejaVu Sans', 10)
else:  # platform is 'win'  # Windows (10, 11)
    LABEL_FONT = ('Segoe UI', 10)
