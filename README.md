# countBOINCtasks

## count-tasks

A utility for monitoring task data reported by the boinc-client. 
It may be useful for comparing task productivity between different computers or configurations.

Developed with Python 3.8, under Ubuntu 20.04, Windows 10 and Mac OS 10.13. You
 may need to download or update to Python 3.6 or later. Recent Python
  packages can be downloaded from https://www.python.org/downloads/.

### Usage:  
Download the .zip package from the Code download button and extract to your
 favorite folder. From within the resulting countBOINCtasks-master folder
 , open a Terminal or Command Prompt window and call up the utility's help menu. The exact invocation on the command line may slightly differ depending on how your PATH environment variable is set.
<ul>
<li>Linux or Mac OS: ./count-tasks.py --help</li>
<li>Windows: python count-tasks.py --help</li>
</ul>
Depending on your Python path settings in Windows, double-clicking on 
the count-tasks.py file icon may automatically launch the program, with its 
default settings, in a Terminal window.

Default settings assume a default location of the BOINC folder from the
 BOINC installer. If you have put the BOINC folder in a different location,
  then there will be a command line option to enter that custom path to run
   boinc-client's boinccmd (or boinccmd.exe) executable. A custom command
    path can also be added to the countCFG.txt configuration file to avoid
     entering the path on the command line.
```
~/countBOINCtasks-master$ ./count-tasks.py --help
usage: count-tasks [-h] [--about_gui] [--log] [--interval M] [--summary TIMEunit] [--count_lim N]

optional arguments:
  -h, --help          show this help message and exit
  --about_gui             Author, copyright, and GNU license
  --log               Generates or appends reports to a log file
  --interval M        Specify Minutes between task counts (default: 60)
  --summary TIMEunit  Specify time between count summaries, e.g., 12h, 7d (default: 1d)
  --count_lim N       Specify number of count reports until program closes (default: 1008)

```
Options can be abbreviated, e.g., `./count-tasks --l --i 15 --s 1h --c 12`

Running the default settings (no optional arguments), will count the
 number of tasks reported to the BOINC Project server on a repeating
  interval of 1 hour, with summaries provided every 24 hr. Basic statistics
   for task times are also provided for each count interval. The initial
    data report provided immediately upon program launch is for the most recent
     tasks reported by boinc-client during the past hour. Repeating
      counts intervals begin after the initial report (see TIP, below).

Example report results, using default settings:

```
2021-May-19 16:17:32; Number of tasks in the most recent BOINC report: 16
                      Task Times: mean 00:22:55, range [00:22:45 - 00:23:03],
                                                 stdev 00:00:05, total 06:06:46
                      Total tasks in queue: 90
                      Number of scheduled count intervals: 1008
                      Counts every 60m, summaries every 1d
                      Timed intervals beginning now...

2021-May-19 17:17:36; Tasks reported in the past 60m: 16
                      Task Times: mean 00:22:54, range [00:22:45 - 00:23:01],
                                                 stdev 00:00:04, total 06:06:36
                      Total tasks in queue: 74
                      Counts remaining until exit: 1007

10m ||||||||||< ~time to next count
```

A countdown timer displays, in a colored bar, the approximate time remaining until the next task count.
 
Running with the `--log` option will save the reports to a log file in the
 working folder. This file is appended to or created when the program is
  launched.

You can let `count-tasks.py` run in an open terminal window with negligible
 impact on system resources. Stop it with *Ctrl-C* or let it stop
  automatically.  With default settings, it will stop after 6 weeks (1008
   1hr count cycles). A different count cycle limit can be set with the
    `--count_lim` option.

NOTE: Summary counts may be less than the sum of individual counts because
 of persistence of reported tasks between count intervals. This can be
  expected when the `--interval`option is set to less than the default 60
   (minutes). The boinc-client command that provides reported task data
   , `boinccmd  --get_old_tasks`, retrieves tasks reported for the past hour
   , independent of the utility's count interval. To avoid missing any
    reported tasks, the `--interval` option has a 60 minutes maximum count
     interval.

TIP: To get the only the most recent task count and time metrics without
 running count intervals, run:  `count-tasks.py --c 0`
 
### Development Plans
* Improve Python code
* Add GUI

### Known Issues
* BOINC version 7.16.14 for Mac OSX. released 1 Dec 2020, has a different 
  boinccmd path from the default path used by count-tasks.py. I've yet to 
  figure out the new path. (Any help would be appreciated.) As a work-around, 
  if you archived a prior BOINC package, you can copy the boinccmd 
  executable file into the default location: 
  Users/<you>/Application Support/BOINC/ , or follow the 
  prompts to enter a custom path to boinccmd (assuming you have figured 
  that out!)
