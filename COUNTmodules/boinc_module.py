#!/usr/bin/env python3
"""BOINCmodule - executing BOINC commands and parsing task data.
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
__version__ = '0.4.4'
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

    @staticmethod
    def set_boincpath() -> str:
        """
        Define an OS-specific path for BOINC's boinccmd executable.

        :return: Correct path string for executing boinccmd commands.
        """

        # Need to accommodate win32 and win36, so slice [:3] for all platforms.
        my_os = sys.platform[:3]
        # Using home() does not form valid Windows command path.
        # win_path = str(Path.home().joinpath('Program Files', 'BOINC', 'boinccmd.exe'))
        win_path = Path(r'\Program Files\BOINC\\boinccmd.exe')
        lin_path = Path(r'/usr/bin/boinccmd')
        dar_path = Path(r'$HOME/Library/Application\ Support/BOINC/boinccmd')

        default_path = {
            'win': win_path,
            'lin': lin_path,
            'dar': dar_path
        }
        # if my_os == 'win' or my_os == 'lin':
        if my_os in ('win', 'lin'):
            if Path.is_file(default_path[my_os]) is False:
                custom_path = input(
                    f'\nboinccmd is not in its default path: '
                    f'{default_path[my_os]}\n'
                    f'Enter your custom path to execute boinccmd: ')
                if os.path.isfile(custom_path) is False:
                    raise OSError(f'Oops. {custom_path} will not work.\n'
                                  f'Be sure to include /boinccmd or '
                                  f'\\boinccmd.exe.\n'
                                  f'Try again. Exiting now...\n')
                cmd_tail = os.path.split(custom_path)[1]
                if cmd_tail != 'boinccmd.exe' and my_os == 'win':
                    raise OSError(f'The entered command path, {custom_path},'
                                  f' must end with \\boinccmd.exe.\n'
                                  f'Try again. Exiting now...\n')
                if cmd_tail != 'boinccmd' and (my_os in ('lin', 'dar')):
                    raise OSError(f'The entered command path, {custom_path},'
                                  f' must end with /boinccmd.\n'
                                  f'Try again. Exiting now...\n')
                return custom_path
            boinccmd = str(default_path[my_os])
            return boinccmd

        # No current support for non-default Mac BOINC path.
        if my_os == 'dar':
            if Path.is_file(default_path[my_os]) is False:
                raise OSError('BOINC is not in its expected default path.\n'
                              'Custom paths not yet supported.\n'
                              'Try reinstalling BOINC? Exiting...\n')
            boinccmd = str(default_path[my_os])
            return boinccmd

        raise KeyError(f"Platform <{my_os}> is not recognized.\n"
                       f"Expecting win (win32 or win64), lin (linux), or dar "
                       f"(darwin == Mac OS).")

    @staticmethod
    def run_boinc(cmd_str: str) -> list:
        """
        Run a boinc-client command line for the current system platform.

        :param cmd_str: Complete boinccmd command line, with arguments.
        :return: Data from boinc-client command specified in cmd_str.
        """
        # TODO: Add exceptions for subprocess failure.
        output = ['boinccmd_results_stub']
        # Works with Python 3.6 and up.
        if sys.platform[:3] == 'win':
            output = subprocess.run(cmd_str,
                                    stdout=PIPE,
                                    encoding='utf8',
                                    check=True).stdout.split('\n')
        if sys.platform == 'linux' or sys.platform == 'darwin':
            output = subprocess.run(cmd_str,
                                    shell=True,
                                    stdout=PIPE,
                                    encoding='utf8',
                                    check=True).stdout.split('\n')
        # Works with Windows, Python 3.8 and 3.9.
        # if sys.platform[:3] == 'win':
        #     output = subprocess.run(cmd_str,
        #                             capture_output=True,
        #                             text=True,
        #                             check=True).stdout.split('\n')
        # Works with Linux, Python 3.7 and up.
        # if sys.platform == 'linux' or sys.platform == 'darwin':
        #     output = subprocess.run(cmd_str,
        #                             shell=True,
        #                             capture_output=True,
        #                             encoding='utf8',
        #                             check=True).stdout.split('\n')
        return output

    def get_tasks(self, boincpath: str, tag: str) -> list:
        """
        Get data from current boinc-client tasks.

        :param boincpath: Command line path to execute boinccmd.
        :param tag: Used by taskXDF: 'name', 'state', 'scheduler
                    state', 'fraction done', 'active_task_state'
        :return: List of specified data from current tasks.
        """
        # NOTE: This method not currently used by count-tasks.
        # taskXDF_tag = ['name', 'state', 'scheduler, state', 'fraction done',
        #              'active_task_state']
        cmd_str = boincpath + ' --get_tasks'
        output = self.run_boinc(cmd_str)

        data = ['stub_boinc_data']
        tag_str = f'{" " * 3}{tag}: '  # boinccmd return format for a data tag.
        # if tag in taskXDF_tag:
        if tag in self.tasktags:
            data = [dat.replace(tag_str, '') for dat in output if tag in dat]
            return data
        print(f'Unrecognized data tag: {tag}')
        return data

    def get_reported(self, boincpath: str, tag: str) -> list:
        """
        Get data from reported boinc-client tasks.

        :param boincpath: Command line path to execute boinccmd.
        :param tag: 'task' returns reported task names.
                    'elapsed time' returns final task times, sec.000000.
        :return: List of specified data from reported tasks.
        """

        cmd_str = boincpath + ' --get_old_tasks'
        output = self.run_boinc(cmd_str)

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
