#!/usr/bin/env python3
"""
Executes BOINC commands and parsing task data through boinccmd.
.. note: Not all boinc-client commands are supported.

    Copyright (C) 2020  C. Echt

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program. If not, see https://www.gnu.org/licenses/.
"""

__author__ = 'cecht, BOINC ID: 990821'
__copyright__ = 'Copyright (C) 2020 C. Echt'
__credits__ = ['Inspired by rickslab-gpu-utils',
               'Keith Myers - Testing, debug']
__license__ = 'GNU General Public License'
__program_name__ = 'count-tasks.py'
__version__ = '0.4.6.1'
__maintainer__ = 'cecht'
__docformat__ = 'reStructuredText'
__status__ = 'Development Status :: 4 - Beta'

import os
import subprocess
import sys
from pathlib import Path
from subprocess import PIPE


class BoincCommand:
    """
    Execute boinc-client commands and parse data.
    """
    # These __init__ tag tuples are not currently used.
    def __init__(self):
        self.tasktags = ('name', 'WU name', 'project URL', 'received',
                         'report deadline', 'ready to report', 'state',
                         'scheduler state',  'active_task_state',
                         'app version num', 'resources', 'final CPU time',
                         'final elapsed time', 'final elapsed time',
                         'exit status', 'signal', 'estimated CPU time '
                         'remaining', 'slot', 'PID', 'current CPU time',
                         'CPU time at last checkpoint', 'fraction done',
                         'swap size', 'working set size')
        self.reportedtags = ('task', 'project URL', 'app name', 'exit status',
                             'elapsed time', 'completed time',
                             'get_reported time')
        self.gettasktags = ('name', 'state', 'scheduler state',
                            'fraction done', 'active_task_state')

    @staticmethod
    def set_boincpath() -> str:
        """
        Define an OS-specific path for BOINC's boinccmd executable.

        :return: Correct path string for executing boinccmd commands.
        """
        # Need to first check for custom path in the configuration file.
        # .split to remove the tag, .join to re-form the path with any spaces.
        if os.path.isfile('countCFG.txt'):
            with open('countCFG.txt', 'r') as cfg:
                for line in cfg:
                    if '#' not in line and 'custom_path' in line:
                        parts = line.split()
                        del parts[0]
                        custom_path = " ".join(parts)
                        return custom_path

        # Need to accommodate win32 and win36, so slice [:3] for all platforms.
        my_os = sys.platform[:3]

        win_path = Path('/Program Files/BOINC/boinccmd.exe')
        lin_path = Path('/usr/bin/boinccmd')
        dar_path = Path.home()/'Library'/'Application Support'/'BOINC'/'boinccmd'
        default_path = {
                        'win': win_path,
                        'lin': lin_path,
                        'dar': dar_path
        }

        if my_os in default_path:
            if Path.is_file(default_path[my_os]) is False:
                custom_path = input(
                    f'\nboinccmd is not in its default path: '
                    f'{default_path[my_os]}\n'
                    f'You may set your custom path in countCFG.txt, or\n'
                    f'Enter your custom path here to execute boinccmd: ')
                if os.path.isfile(custom_path) is False:
                    raise OSError(f'Oops. {custom_path} will not work.\n'
                                  f'Be sure to include \\boinccmd or '
                                  f'/boinccmd.exe, depending on your system.\n'
                                  f'Try again. Exiting now...\n')
                cmd_tail = os.path.split(custom_path)[1]
                if cmd_tail not in ('\\boinccmd.exe', 'boinccmd.exe'):
                    raise OSError(f'The entered command path, {custom_path},'
                                  f' must end with \\boinccmd.exe or '
                                  f'/boinccmd, depending on your system.\n'
                                  f'Try again. Exiting now...\n')
                return custom_path
            boinccmd = str(default_path[my_os])
            return boinccmd
        raise KeyError(f"Platform <{my_os}> is not recognized.\n"
                       f"Expecting win (win32 or win64), lin (linux), or dar "
                       f"(darwin =>Mac OS).")

    @staticmethod
    def run_boinc(cmd_str: str) -> list:
        """
        Run a boinc-client command line.

        :param cmd_str: Complete boinccmd command line, with arguments.
        :return: Data from boinc-client command specified in cmd_str.
        """
        # Works with Python 3.6 and up. shell=True not necessary in Windows.
        try:
            output = subprocess.run(cmd_str,
                                    shell = True,
                                    stdout = PIPE,
                                    encoding = 'utf8',
                                    check = True).stdout.split('\n')
            return output
        except subprocess.CalledProcessError as cpe:
            msg = 'If the boinccmd usage stdout is displayed, then '\
                   'boinccmd has an error in its command line argument.'
            print(f'\n{msg}\n{cpe}')
            sys.exit(1)
        # TODO: Are more subprocess exceptions needed?.

        # Works with Windows, Python 3.8 and 3.9.
        # if sys.platform[:3] == 'win':
        #     output = subprocess.run(cmd_str,
        #                             capture_output=True,
        #                             text=True,
        #                             check=True).stdout.split('\n')
        #     return output
        # Works with Linux, Python 3.7 and up.
        # if sys.platform in ('linux', 'darwin'):
        #     output = subprocess.run(cmd_str,
        #                             shell=True,
        #                             capture_output=True,
        #                             encoding='utf8',
        #                             check=True).stdout.split('\n')
        #     return output

    # This method is not used by count_tasks.py.
    def get_tasks(self, boincpath: str, tag: str) -> list:
        """
        Get data from current boinc-client tasks.

        :param boincpath: boinccmd path, defined by set_boincpath().
        :param tag: Used by taskXDF: 'name', 'state', 'scheduler
                    state', 'fraction done', 'active_task_state'
        :return: List of specified data from current tasks.
        """

        # This path string format is required for MacOS folder names that
        # have spaces.
        cmd_str = f'"{boincpath}"' + ' --get_tasks'
        output = self.run_boinc(cmd_str)

        data = ['stub_boinc_data']
        tag_str = f'{" " * 3}{tag}: '  # boinccmd output format for a data tag.
        # if tag in self.taskXDFtags:  # Not currently used by count-tasks.
        if tag in self.tasktags:
            data = [dat.replace(tag_str, '') for dat in output if tag in dat]
            return data
        print(f'Unrecognized data tag: {tag}')
        return data

    def get_reported(self, boincpath: str, tag: str) -> list:
        """
        Get data from reported boinc-client tasks.

        :param boincpath: boinccmd path, defined by set_boincpath().
        :param tag: 'task' returns reported task names.
                    'elapsed time' returns final task times, sec.000000.
        :return: List of specified data from reported tasks.
        """

        # This path string format is required for MacOS folder names that
        # have spaces.
        cmd_str = f'"{boincpath}"' + ' --get_old_tasks'
        output = self.run_boinc(cmd_str)

        # Need to get only data from tagged data lines.
        data = ['stub_boinc_data']
        if tag == 'elapsed time':
            tag_str = f'{" " * 3}{tag}: '
            data = [dat.replace(tag_str, '') for dat in output if tag in dat]
            data = [float(seconds.replace(' sec', '')) for seconds in data]
            return data
        if tag == 'task':
            tag_str = 'task '
            data = [dat.replace(tag_str, '') for dat in output if tag in dat]
            data = [name.rstrip(':') for name in data]
            return data

        print(f'Unrecognized data tag: {tag}')
        return data


def about() -> None:
    """
    Print details about this module.
    """
    print(__doc__)
    print('Author: ', __author__)
    print('Copyright: ', __copyright__)
    print('Credits: ', *[f'\n      {item}' for item in __credits__])
    print('License: ', __license__)
    print('Version: ', __version__)
    print('Maintainer: ', __maintainer__)
    print('Status: ', __status__)
    sys.exit(0)


if __name__ == '__main__':
    about()
