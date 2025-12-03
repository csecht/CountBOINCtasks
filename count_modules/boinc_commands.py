#!/usr/bin/env python3
"""
Executes BOINC commands and parsing task data through boinccmd.
Not all boinc-client commands are supported.
Functions:
set_boinc_path - Return OS-specific path for BOINC's boinccmd binary.
run_boinc - Execute a boinc-client command line; returns output.
get_version - Get version number of boinc client; return list of one.
check_boinc - Check whether BOINC client is running; exit if not.
boinccmd_not_found - Display message for a bad boinccmd path; for standalone app.
check_boinc_tk - Check whether BOINC client is running, quit if not.
get_reported - Get data for reported boinc-client tasks.
get_tasks - Get data for current boinc-client tasks.
get_state - Get state of all boinc-client Projects and tasks.
get_runningtasks - Get names of running boinc-client tasks for a specified app.
project_url - Return dictionary of BOINC project NAMES and server urls.
get_project_url - Return current local host boinc-client Project URLs.
project_action - Execute a boinc-client action for a specified Project.
no_new_tasks - Get Project status for "Don't request more work".
"""
# Copyright (C) 2021 C. Echt under GNU General Public License'

import shlex
import sys
from pathlib import Path
from subprocess import Popen, PIPE, STDOUT
from tkinter import messagebox

CFGFILE = Path('countCFG.txt').resolve()

# Only win, lin, and dar values are accommodated here.
MY_OS = sys.platform[:3]

# Tuples that may be used in various functions:
TASK_TAGS = ('name', 'WU name', 'project URL', 'received',
             'report deadline', 'ready to report', 'state',
             'scheduler state', 'active_task_state',
             'app version num', 'resources', 'final CPU time',
             'final elapsed time',
             'exit status', 'signal', 'estimated CPU time remaining',
             'slot', 'PID', 'current CPU time',
             'CPU time at time_now checkpoint', 'fraction done',
             'swap size', 'working set size', 'master URL'
             )

PROJECT_CMD = ('reset', 'detach', 'update', 'suspend', 'resume',
               'nomorework', 'allowmorework', 'detach_when_done',
               'dont_detach_when_done'
               )

REPORTED_TAGS = ('task', 'project URL', 'app name', 'exit status',
                'elapsed time', 'completed time', 'get_reported time')

# GETTASKS_TAGS = ('name', 'state', 'scheduler state',  'fraction done',
#                'active_task_state')


def set_boincpath() -> str:
    """
    Define an OS-specific path for BOINC's boinccmd executable.

    :return: Correct path string for executing boinccmd commands;
        exit if not correct.
    """
    # Need to first check for custom path in the configuration file.
    # Do split to remove the "custom_path" tag, then join to restore the
    #   path with any spaces it might have.
    if Path.is_file(CFGFILE):
        cfg_text = Path(CFGFILE).read_text()
        for line in cfg_text.splitlines():
            if '#' not in line and 'custom_path' in line:
                custom_path = " ".join(line.split()[1:])
                if not Path.is_file(Path(custom_path)):
                    sys.exit(f'The custom path: {custom_path}\n'
                             'is not a recognized file or path.\n')
                return f'"{custom_path}"'

    default_path = {
        'win': Path('/Program files/BOINC/boinccmd.exe'),
        'lin': Path('/usr/local/bin/boinccmd'), # or /usr/bin/boinccmd on older versions.
        'dar': Path.home() / 'Library' / 'Application Support' / 'BOINC' / 'boinccmd'
    }
    # Note: On macOS, the Terminal command line would be entered as:
    # /Users/youtheuser/Library/Application\ Support/BOINC/boinccmd

    if MY_OS not in default_path or not Path.is_file(default_path[MY_OS]):
        sys.exit(
            f'Error: The application boinccmd is not in its expected default path: '
            f'{default_path.get(MY_OS, "Unknown OS")}\n'
            'Please enter your custom path for boinccmd in the configuration file:\n'
            f'{CFGFILE}.')

    return f'"{default_path[MY_OS]}"'


def run_boinc(cmd_str: str) -> list:
    """
    Execute a boinc-client command line.

    :param cmd_str: A boinccmd action, command with arguments.
    :return: Data from a boinc-client command specified in cmd_str.
    """
    # source: https://stackoverflow.com/questions/33560364/
    cmd: str = cmd_str if MY_OS == 'win' else shlex.split(cmd_str)

    with Popen(cmd, stdout=PIPE, stderr=STDOUT, text=True) as output:
        data_output: list = output.communicate()[0].split('\n')

    # When boinc-client is running, the specified cmd option from a get_ method
    #   will fill the first element of the text list with its output. When not
    #   running, boinccmd stderr will fill the first list element.
    #   Is stderr "can't connect to local host" exclusive to BOINC not running?
    if "can't connect to local host" in data_output:
        print(f"\nOOPS! There is a boinccmd error: {data_output[0]}\n"
              f"The BOINC client associated with {cmd[0]} is not running.\n"
              "You need to quit now and get the client running.")

    # If boinc not running, then text will be a null list.
    return data_output


def boinccmd_not_found(default_path: str) -> None:
    """
    Display a popup message for a bad boinccmd path for a
    standalone program; exits program once user acknowledges.

    :param default_path: The expected path for the boinccmd command.
    """
    okay = messagebox.askokcancel(
        title='BOINC ERROR: bad cmd path',
        detail='The application boinccmd is not in its expected default path:\n'
               f'{default_path}\n'
               'Edit the configuration file, countCFG.txt,\n'
               'in the CountBOINCtasks-main folder.\n'
               'Exit now.')

    sys.exit(0) if okay else sys.exit(0)


def get_version(cmd=' --client_version') -> list:
    """
    Get version number of the boinc client.
    Returns 'can't connect to local host' if boinc-client not running.

    :param cmd: The boinc command to get the client version.
    :return: version info, as a list of one string.
    """

    # Note: run_boinc() always returns a list.
    return run_boinc(set_boincpath() + cmd)


def check_boinc():
    """
    Check whether BOINC client is running at startup;
    exit if not running.
    """

    # Note: Any bcmd boinccmd will return this string (as a list)
    #   if boinc-client is not running; use get_version() b/c it is short.
    if "can't connect to local host" in get_version():
        sys.exit('BOINC ERROR: BOINC commands cannot be executed.\n'
                 'Is the BOINC client running?   Exiting now...')


def check_boinc_tk(mainloop) -> None:
    """
    Check whether BOINC client has stopped during Tk mainloop;
    exit if not running.
    """
    if "can't connect to local host" in get_version():
        messagebox.askokcancel(
            title='BOINC ERROR',
            detail='BOINC commands cannot be executed.\n'
                   'Is the BOINC client running?\nExiting now...')
        mainloop.update_idletasks()
        mainloop.after(100)
        mainloop.destroy()
        sys.exit(0)


def get_reported(tag: str, cmd=' --get_old_tasks') -> list:
    """
    Get data from reported boinc-client tasks. Returns empty list if
    *tag* is not recognized or if boinc-client has not yet reported tasks.

    :param tag: e.g., 'task' returns reported task names.
                'elapsed time' returns final task times, sec.000000.
                Use 'all' to get full output from cmd
    :param cmd: The boinccmd command for tasks reported to boinc server.
    :return: List of tagged data parsed from *cmd* output.
    """

    output = run_boinc(set_boincpath() + cmd)
    tag_str = f'{" " * 3}{tag}: ' if tag == 'elapsed time' else 'task '
    data = [line.replace(tag_str, '') for line in output if tag in line]

    try:
        if tag == 'all':
            return output

        if tag == 'elapsed time':
            data = [float(e_time.replace(' sec', '')) for e_time in data]
        elif tag == 'task':
            data = [name.rstrip(':') for name in data]

        return data

    except ValueError:
        print(f'Unrecognized data tag: {tag}. Expecting one of these: \n'
              f'{REPORTED_TAGS}')
        return []


def get_tasks(tag: str, cmd=' --get_tasks') -> list:
    """
    Get data from current boinc-client tasks.

    :param tag: Examples: 'name', 'state', 'scheduler
                state', 'fraction done', 'active_task_state'
                Use 'all' to get full output from *cmd*.
    :param cmd: The boinccmd command to get queued tasks information.
    :return: List of tagged data parsed from *cmd* output.
    """

    output = run_boinc(set_boincpath() + cmd)
    tag_str = f'{" " * 3}{tag}: '  # boinccmd output format for a data tag.
    data = [line.replace(tag_str, '') for line in output if tag_str in line]

    if tag == 'all':
        return output

    if tag in TASK_TAGS:
        return data

    print(f'Unrecognized data tag: {tag}. Expecting one of these: \n{TASK_TAGS}')
    return []


def get_state(cmd=' --get_state') -> list:
    """
    Get the state of all boinc-client Projects, apps, and tasks.

    :param cmd: The boinccmd command to get full status output.
    :return: The full state output, as a list.
    """

    return run_boinc(set_boincpath() + cmd)


def get_runningtasks(tag: str, app_type: str,
                     cmd=' --get_simple_gui_info') -> list:
    """
    Get names of running boinc-client tasks of the specified app.

    :param tag: boinccmd output line tag, e.g., 'name', 'WU name'.
                Use 'all' to get full output from cmd
    :param app_type: The app type present in all target task names,
                    e.g. O3AS, LATeah, etc.
    :param cmd: The boinccmd command to get task information.
    :return: List of tagged data parsed from *cmd* output.
    """

    # NOTE: cmd=' --get_tasks' will also work, but
    #   get_simple_gui_info lists only active tasks.
    output = run_boinc(set_boincpath() + cmd)
    tag_str = f'{" " * 3}{tag}: '  # boinccmd output format for a tag line of data.
    task_name = None
    data = []

    if tag == 'all':
        return output

    # Need to determine whether a task's task state line following its name line
    #    specifies that it is a running task (active_task_state: EXECUTING).
    # Each loop, need to clear task name to ensure target task name is paired
    #    with its active state and not that of a prior non-EXECUTING task.
    for line in output:
        if app_type in line and tag_str in line:
            task_name = line.replace(tag_str, '')
            if 'EXECUTING' in output[output.index(line) + 1]:
                data.append(task_name)

    return data


def project_url() -> dict:
    """Dictionary of BOINC project NAMES and server urls
    """
    return {
        'AMICABLE': 'https://sech.me/boinc/Amicable/',
        'ASTEROID': 'http://asteroidsathome.net/boinc/',
        'TACC': 'https://boinc.tacc.utexas.edu/',
        'CITIZEN': 'https://csgrid.org/csg/',
        'CLIMATE': 'https://www.cpdn.org/',
        'COLLATZ': 'https://boinc.thesonntags.com/collatz/',
        'COSMOL': 'http://www.cosmologyathome.org/',
        'EINSTEIN': 'https://einstein.phys.uwm.edu/',
        'GERASIM': 'http://gerasim.boinc.ru/',
        'GPUGRID': 'https://www.gpugrid.net/',
        'IBERCIVIS': 'https://boinc.ibercivis.es/ibercivis/',
        'ITHENA': 'https://root.ithena.net/usr/',
        'LHC': 'https://lhcathome.cern.ch/lhcathome/',
        'MILKYWAY': 'http://milkyway.cs.rpi.edu/milkyway/',
        'MIND': 'https://mindmodeling.org/',
        'MINECRAFT': 'https://minecraftathome.com/minecrafthome/',
        'MLC': 'https://www.mlcathome.org/mlcathome/',
        'MOO': 'http://moowrap.net/',
        'NANOHUB': 'https://boinc.nanohub.org/nanoHUB_at_home/',
        'NFS': 'https://escatter11.fullerton.edu/nfs/',
        'NUMBER': 'https://numberfields.asu.edu/NumberFields/',
        'ODLK': 'https://boinc.progger.info/odlk/',
        'ODLK1': 'https://boinc.multi-pool.info/latinsquares/',
        'PRIME': 'http://www.primegrid.com/',
        'QUCHEM': 'https://quchempedia.univ-angers.fr/athome/',
        'RADIOACT': 'http://radioactiveathome.org/boinc/',
        'RAKE': 'https://rake.boincfast.ru/rakesearch/',
        'RNA': 'http://www.rnaworld.de/rnaworld/',
        'ROSETTA': 'https://boinc.bakerlab.org/rosetta/',
        'SRBASE': 'http://srbase.my-firewall.org/sr5/',
        'UNIVERSE': 'https://universeathome.pl/universe/',
        'WOLRD': 'https://universeathome.pl/universe/',
        'YOYO': 'http://www.rechenkraft.net/yoyo/'
    }


def get_project_url(tag='master URL', cmd=' --get_project_status') -> list:
    """
    Get all current local host boinc-client Project URLs.

    :param tag: Only need the name of each Project's boinc server URL.
    :param cmd: The boinccmd command to get Project information.
    :return: List of tagged data parsed from *cmd* output.
    """

    output = run_boinc(set_boincpath() + cmd)
    tag_str = f'{" " * 3}{tag}: '  # boinccmd output format for a data tag.

    if tag in TASK_TAGS:
        data = [line.replace(tag_str, '') for line in output if tag in line]
        return data

    print(f'Unrecognized data tag: {tag}. Expecting one of these: \n{TASK_TAGS}')
    return []


def project_action(project: str, action: str) -> list:
    """
    Execute a boinc-client action for a specified Project.

    :param project: A project_url dict key for a BOINC 'PROJECT'
    :param action: Use: 'suspend', 'resume', or 'update'.
    :return: Execution of specified boinc-client *action*.
    """

    # Project commands require the Project URL, others commands don't
    if action in PROJECT_CMD:
        cmd_str = f'{set_boincpath()} --project {project_url()[project]} {action}'
        return run_boinc(cmd_str)
    else:
        print(f'Unrecognized action: {action}. Expecting one of these: \n{PROJECT_CMD}')


def no_new_tasks(cmd=' --get_project_status') -> bool:
    """
    Get BOINC Project status for "Don't request more work".

    :param cmd: The boinccmd command to get Project information.
    :return: True or False indicating status of "No new tasks"
             Project setting.
    """

    output = run_boinc(set_boincpath() + cmd)

    tag_str = f'{" " * 3}don\'t request more work: '
    nnw = [line.replace(tag_str, '') for line in output if tag_str in line]

    if 'yes' in nnw:
        return True

    return False
