"""
Check that support system platform is present. Is called from __init__
at startup. Constant MY_OS used throughout main program.
Functions: check_platform
"""
# Copyright (C) 2021 C. Echt under GNU General Public License'

import sys
import platform

MY_OS = sys.platform[:3]


def check_platform():
    if MY_OS not in 'lin, win, dar':
        print(f'Platform <{sys.platform}> is not supported.\n'
              'Windows, Linux, and MacOS (darwin) are supported.')
        sys.exit(1)

    # Need to account for scaling in Windows10 and earlier releases.
    if MY_OS == 'win':
        from ctypes import windll

        if platform.release() < '10':
            windll.user32.SetProcessDPIAware()
        else:
            windll.shcore.SetProcessDpiAwareness(1)



