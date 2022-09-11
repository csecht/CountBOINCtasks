#!/usr/bin/env python3
"""
Basic tkinter file handling functions.
Functions:
    append_txt - Append text_obj to the destination file.
    save_as - Copy source file to destination of choice.
    erase - Delete file content and the displayed window text_obj.
    update - Replace text_obj in window with current file content.
"""
# Copyright (C) 2021 C. Echt under GNU General Public License'

# Standard library import modules
import sys
from datetime import datetime
from pathlib import Path
from platform import node
from shutil import copy2

# Third party imports: tkinter may not be included with some Python distributions.
try:
    import tkinter as tk
    from tkinter import messagebox, ttk
except (ImportError, ModuleNotFoundError) as error:
    sys.exit('This program requires tkinter (tk/tcl), which is usually included with \n'
             'Python 3.7+ distributions.\n'
             'Install the most recent version or re-install Python and include Tk/Tcl.\n'
             '\nOn Linux, first try: $ sudo apt-get install python3-tk\n'
             f'See also: https://tkdocs.com/tutorial/install.html \n'
             f'Error msg: {error}')


def append_txt(dest: Path, savetxt: str, showmsg=True, parent=None) -> None:
    """
    Append text_obj to the destination file.

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
                messagebox.showinfo(message='Results saved (appended) to:',
                                    detail=dest, parent=parent)
            # Need to remove focus from calling Button so can execute any
            #   immediately following rt-click commands in parent.
            if parent:
                parent.focus_set()
    except PermissionError:
        perr = (f'On {node()}, {dest}\n could not be opened because\n'
                'of insufficient permissions.')
        messagebox.showerror(title='FILE PERMISSION ERROR',
                             detail=perr, parent=parent)
    except UnicodeError as unierr:
        messagebox.showerror(title='Wrong file encoding',
                             detail=unierr, parent=parent)
        print(unierr)
    except FileNotFoundError:
        fnferr = (f'On {node()}, file is missing:\n{dest}\n'
                  'Have any analysis results been saved yet?\n'
                  'Was file deleted, moved or renamed?')
        messagebox.showerror(title='FILE NOT FOUND',
                             detail=fnferr, parent=parent)
    except OSError as oserr:
        unkerr = (f'On {node()}, a file append error with:\n{dest}\n'
                  f'Were you working on the file recently?\n')
        messagebox.showerror(title='FILE ERROR',
                             detail=unkerr, parent=parent)
        print(oserr)


def save_as(source: Path, parent=None) -> None:
    """
    Copy source file to a destination of user's choice;
    timestamp provided.

    :param source: A Path object of the file to back up.
    :param parent: Toplevel object over which messagebox appears;
                   defaults to app (master) window.
    """

    if not Path.exists(source):
        fnf_detail = (f'On {node()}, cannot back up:\n'
                      f'{source}\nHas it been moved or renamed?')
        messagebox.showerror(title='FILE NOT FOUND', detail=fnf_detail,
                             parent=parent)
        return

    # Offer to use a timestamp for each save_as file saved.
    _ts = datetime.now().strftime("%d%m%Y_%H%M")
    backupname = f'{source.stem}_{_ts}_{source.suffix}'
    backupfile = filedialog.asksaveasfilename(
        initialfile=backupname, parent=parent,
        filetypes=[('TEXT', '*.txt'), ],
        title=f'Backup {source.name} as')
    # Need to avoid raising a TypeError when "Cancel" is selected from
    #   filedialog and returns a null Tuple as the file path string.
    if not backupfile:
        return
    destination = Path(backupfile).resolve()
    try:
        copy2(source, destination)
        messagebox.showinfo(title='Backup completed', parent=parent,
                            message='Log file has been copied to: ',
                            detail=str(destination))
        # Need to remove focus from calling Button so can execute any
        #   immediately following rt-click commands in parent.
        if parent:
            parent.focus_set()
    except PermissionError:
        messagebox.showinfo(title='Log copy error',
                            message="Permission denied",
                            detail=f'Cannot open {source}')
        print(f'Log file backup: Permission to open {source} denied.')


def erase(text_obj: tk.Text, file: Path, parent=None) -> None:
    """
    Delete file contents and its displayed window text.

    :param text_obj: A tkinter.ScrolledText or tkinter.Text insert.
    :param file: Path object of file from which to erase content.
    :param parent: The parent window over which to place messagebox,
                   usually the *text_obj* Toplevel. Defaults to root
                   as parent window.
    """

    if not Path.exists(file):
        info = (f'On {node()}, could not erase contents of\n'
                f'{file}\nbecause file is missing.\n'
                'Was it deleted, moved or renamed?')
        messagebox.showerror(title='FILE NOT FOUND',
                             detail=info, parent=parent)
        # Need to remove focus from calling Button so can execute any
        #   immediately following rt-click commands in parent.
        if parent:
            parent.focus_set()
        return

    if sys.platform[:3] == 'dar':
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
            text_obj.delete('1.0', tk.END)
            if parent:
                parent.focus_set()
        except PermissionError:
            info = (f'On {node()}, could not erase contents of\n'
                    f'{file}\nbecause it could not be opened.')
            messagebox.showerror(title='FILE PERMISSION ERROR',
                                 detail=info, parent=parent)


def update(text_obj: tk.Text, file: Path, parent=None) -> None:
    """
    Replace text in open log window with (new) log file content.

    :param text_obj: A tkinter.scrolledtext.ScrolledText or
           tkinter.Text to insert.
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

    text_obj.delete(tk.INSERT, tk.END)
    text_obj.insert(tk.INSERT, Path(file).read_text())
    text_obj.see(tk.END)
    text_obj.pack(fill=tk.BOTH, side=tk.LEFT, expand=True)
    # Need to remove focus from calling Button so can execute any
    #   immediately following rt-click commands in parent. Use as a
    #   precaution in case Button is not configured takefocus=False.
    if parent:
        parent.focus_set()
