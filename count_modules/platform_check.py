"""

"""
import sys
# Copyright (C) 2021 C. Echt under GNU General Public License'

MY_OS = sys.platform[:3]


def check_platform():
    if MY_OS not in 'lin, win, dar':
        print(f'Platform <{sys.platform}> is not supported.\n'
              'Windows, Linux, and MacOS (darwin) are supported.')
        sys.exit(1)

    # Need to account for scaling in Windows.
    if MY_OS == 'win':
        import ctypes
        ctypes.windll.user32.SetProcessDPIAware()


