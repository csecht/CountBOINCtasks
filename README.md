# countBOINCtasks

## count-tasks

A utility for monitoring task data reported by the boinc-client. 
It may be useful for comparing task productivity between different computers or configurations.

Developed with Python 3.8, under Ubuntu 20.04, Windows 10 and Mac OS 10.13. You
 may need to download or update to Python 3.6 or later. Recent Python
  packages can be downloaded from https://www.python.org/downloads/.

### Usage:  
Download the .zip package from the Code download button and extract to your favorite folder. From within the resutling countBOINCtasks-master folder, open a Terminal or Command Prompt window and call up the utility's help menu. The exact invocation on the command line may slightly differ depending on how your PATH environment variable is set.
<ul>
<li>Linux or Mac OS: ./count-tasks.py --help</li>
<li>Windows: python count-tasks.py --help</li>
</ul>

Default settings assume a default location of the BOINC folder from the
 BOINC installer. If you have put the BOINC folder in a different location,
  then there will be a command line option to enter that custom path to run
   boinc-client's boimccmd (or boinccmd.exe) executable. A custom command
    path can also be added to the countCFG.txt configuration file to avoid
     entering the path on the command line. These custom path options have
      not yet been tested for Mac OS (as of ver. 0.4.5).
```
~/countBOINCtasks-master$ ./count-tasks.py --help
usage: count-tasks [-h] [--about] [--log] [--interval M] [--summary TIMEunit] [--count_lim N]

optional arguments:
  -h, --help          show this help message and exit
  --about             Author, copyright, and GNU license
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

Example report results, using option --summary 2h:

```
2020-Nov-01 11:17:33; Tasks reported in the past hour: 18
                      Task Times: mean 00:25:31, range [00:25:02 - 00:25:52],
                                                 stdev 00:00:13, total 07:39:23
2020-Nov-01 12:17:36; Tasks reported in the past 60m: 13
                      Task Times: mean 00:25:28, range [00:25:05 - 00:25:51],
                                                 stdev 00:00:11, total 05:31:15
2020-Nov-01 13:17:40; Tasks reported in the past 60m: 8
                      Task Times: mean 00:26:25, range [00:25:20 - 00:26:51],
                                                 stdev 00:00:39, total 03:31:25
2020-Nov-01 13:17:40; >>> SUMMARY count for past 2h: 21
                      Task Times: mean 00:26:17, range [00:25:05 - 00:26:51],
                                                 stdev 00:00:40, total 09:02:40
10m          |< ~time to next count
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
     interval, but even that, as well as shorter intervals, can re-count
      tasks that carry over between intervals. Summary counts do not
       included re-counted tasks.

TIP: To get the only the most recent task count and time metrics without
 running count intervals, run:  
 `count-tasks.py --c 0`
```
2020-Nov-01 11:17:33; Tasks reported in the past hour: 18
                      Task Times: mean 00:25:31, range [00:25:02 - 00:25:52],
                                                 stdev 00:00:13, total 07:39:23
```
 
### Development Plans
* Improve Python code
* Improve handling of default and custom paths to execute boinccmd
* Add configuration file option
