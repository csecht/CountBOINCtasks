#!/usr/bin/env python3
"""
Basic file handling methods used by CountBOINCtasks project.
Functions: append_it, backup, erase, update

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
__copyright__ = 'Copyright (C) 2021 C. Echt'
__license__ = 'GNU General Public License'
__program_name__ = 'time_convert.py'
__version__ = '0.1.0'
__maintainer__ = 'cecht'
__docformat__ = 'reStructuredText'
__status__ = 'Development Status :: 4 - Beta'

import sys
import tkinter as tk
from datetime import datetime
from tkinter import messagebox, filedialog
from pathlib import Path
from platform import node
from shutil import copy2

MY_OS = sys.platform[:3]


def append_it(dest: Path, savetxt: str, showmsg=True, parent=None) -> None:
    """
    Appends text to the destination file.

    :param dest: Path object of destination file.
    :param savetxt: Text to be written to dest.
    :param showmsg: Flag for messagebox write confirmation; suppress
                    confirmation msg when call option is False.
    :param parent: Toplevel object over which messagebox appears.
    """

    try:
        with open(dest, 'a', encoding='utf-8') as saved:
            saved.write(savetxt)
            if showmsg:
                messagebox.showinfo(message='Results saved to:',
                                    detail=dest, parent=parent)
    except PermissionError:
        perr = (f'On {node()}, {dest}\n could not be opened because\n'
                'of insufficient permissions.')
        messagebox.showerror(title='FILE PERMISSION ERROR',
                             detail=perr, parent=parent)
    except UnicodeError as err:
        messagebox.showerror(title='Wrong file encoding',
                             detail=err, parent=parent)
        print(err)
    except FileNotFoundError:
        fnferr = (f'On {node()}, file is missing:\n{dest}\n'
                  'Have any analysis results been saved yet?\n'
                  'Was file deleted, moved or renamed?')
        messagebox.showerror(title='FILE NOT FOUND',
                             detail=fnferr, parent=parent)
        return


def backup(source: Path, parent=None) -> None:
    """
    Copy source file to a timestamped destination in the same folder.

    :param source: A Path object of the file to backup.
    :param parent: Toplevel object over which messagebox appears;
                   defaults to app/master window.
    """

    if not Path.exists(source):
        fnf_detail = (f'On {node()}, cannot back up:\n'
                      f'{source}\nHas it been moved or renamed?')
        messagebox.showerror(title='FILE NOT FOUND', detail=fnf_detail,
                             parent=parent)
        return

    # Offer to use a timestamp for each backup file saved.
    _ts = datetime.now().strftime("%d%m%Y_%H%M")
    backupname = f'{source.stem}({_ts}){source.suffix}'
    backupfile = filedialog.asksaveasfilename(
        initialfile=backupname, parent=parent,
        filetypes=[('TEXT', '*.txt'), ],
        title=f'Backup {source.name} as')
    # Need to avoid raising a TypeError when "Cancel" is selected from
    # filedialog and returns a null Tuple as the file path string.
    if not backupfile:
        return
    destination = Path(backupfile).resolve()
    try:
        copy2(source, destination)
        messagebox.showinfo(title='Backup completed', parent=parent,
                            message='Log file has been copied to: ',
                            detail=str(destination))
    except PermissionError:
        messagebox.showinfo(title='Log copy error',
                            message="Permission denied",
                            detail=f'Cannot open {source}')
        print(f'Log file backup: Permission to open {source} denied.')


def erase(file: Path, tktext: tk.Text, parent=None) -> None:
    """
    Delete file contents and its displayed window text.

    :param file: Path object of file from which to erase content.
    :param tktext: A tkinter.ScrolledText or tkinter.Text insert.
    :param parent: The parent window over which to place messagebox,
           usually the tktext Toplevel. Defaults to app window.
    """

    if not Path.exists(file):
        info = (f'On {node()}, could not erase contents of\n'
                f'{file}\nbecause file is missing.\n'
                'Was it deleted, moved or renamed?')
        messagebox.showerror(title='FILE NOT FOUND',
                             detail=info, parent=parent)
        return

    if MY_OS == 'dar':
        msgdetail = (f"'Enter/Return' will also delete "
                     f"content of file {file}.")
    else:
        msgdetail = (f"'Enter/Return' or space bar will also delete "
                     f"content of file {file}.")
    okay = messagebox.askokcancel(title='Confirmation needed',
                                  message='Delete file content?',
                                  detail=msgdetail, parent=parent)
    if okay:
        try:
            with open(file, 'w') as _f:
                _f.close()
            tktext.delete('1.0', tk.END)
        except PermissionError:
            info = (f'On {node()}, could not erase contents of\n'
                    f'{file}\nbecause it could not be opened.')
            messagebox.showerror(title='FILE PERMISSION ERROR',
                                 detail=info, parent=parent)


def update(tktext: tk.Text, file: Path, parent=None) -> None:
    """
    Replace text in open log window with (new) log file content.

    :param tktext: A tkinter.scrolledtext.ScrolledText or
           tkinter.Text insert.
    :param file: Path object of file from which to replace content.
    :param parent: The parent window over which to place messagebox;
           usually a Toplevel(). Defaults to app window.
    """

    if not Path.exists(file):
        msg = (f'On {node()}, cannot update file:\n{file}\n'
               'Was file deleted, moved or renamed?')
        messagebox.showerror(title='FILE NOT FOUND',
                             detail=msg, parent=parent)
        return

    with open(file, encoding='utf-8') as new_text:
        tktext.delete('1.0', tk.END)
        tktext.insert('1.0', new_text.read())
        tktext.see(tk.END)
        tktext.pack(fill=tk.BOTH, side=tk.LEFT, expand=True)


def about() -> None:
    """
    Print details about_gui this module.
    """
    print(__doc__)
    print('Author: ', __author__)
    print('Copyright: ', __copyright__)
    print('License: ', __license__)
    print('Version: ', __version__)
    print('Maintainer: ', __maintainer__)
    print('Status: ', __status__)
    sys.exit(0)


if __name__ == '__main__':
    about()
