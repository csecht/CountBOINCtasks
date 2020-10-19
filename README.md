# countBOINCtasks

## count-tasks

A utility for monitoring task data reported by the boinc-client. 
It may be useful for comparing task/workunit productivity between hosts or host 
configurations.

Developed with Python 3.8, under Ubuntu 20.04. Intended for use on all 
operating systems, but so far only tested in the development environment. 
The latest Python package can be downloaded from https://www.python.org/downloads/

To use (in Linux), open a terminal from within the countBOINCtasks-master 
directory and call up the help menu: 
```
~/countBOINCtasks-master$ ./count-tasks --help
usage: count-tasks [-h] [--about] [--log] [--interval M] [--summary TIMEunit] [--count_lim N]

optional arguments:
  -h, --help          show this help message and exit
  --about             Author, copyright, and GNU license
  --log               Generates or appends reports to a log file
  --interval M        Specify Minutes between task counts (default: 60)
  --summary TIMEunit  Specify time between count summaries, e.g., 12h, 7d (default: 1d)
  --count_lim N       Specify number of count reports until program closes (default: 1008)

```
(Options can accept abbreviations, e.g., `./count-tasks --l --int 15 --sum 1h`)

Running with the default settings, it will count reported completed tasks
for currently running BOINC Projects on a repeating interval of 1 hour, with 
summaries every 24 hr. Basic statistics on task times are proved along with 
each count. The initial data that is immediately provided is for the most 
recently reported tasks.

Example, default execution:
```
$ ./count-tasks
2020-Oct-19 06:03:54; Tasks reported in past hour: 9
                      (task times total 02:19:47, mean 00:15:31, stdev 00:00:05)
2020-Oct-19 07:03:58; Tasks reported in past 60m: 8
                      (task times total 02:04:46, mean 00:15:35, stdev 00:00:05)
2020-Oct-19 08:04:01; No tasks reported in past 1 60m interval(s).
2020-Oct-19 09:04:05; Tasks reported in past 60m: 19
                      (task times total 07:42:13, mean 00:24:19, stdev 00:02:15)
2020-Oct-19 10:04:09; Tasks reported in past 60m: 8
                      (task times total 03:26:29, mean 00:25:48, stdev 00:00:07)
27m                           |< ~time to next count
```
A countdown timer displays, in a colored bar, the approximate time remaining
 until the next task count.
 
Running with the `--log` option will save the reports to a log file in the 
current folder. This file is appended to each time the program is launched or 
will be created if needed.

You can let count-tasks run in an open terminal window with negligible impact 
on system resources. Stop it with *ctrl-c* or just let it run. With default 
settings, it will stop after 6 weeks (1008 1hr count cycles).

NOTE: Summary counts may be less than the sum of individual counts because of 
persistence of reported tasks between count intervals. This can be expected
 when the `--interval` option is set to less than the default 60m. 
 The command that provides reported tasks data used by `count-tasks`: 
 ```
$ boinccmd  --get_old_tasks 
```
retrieves tasks reported for the past hour, independent of the utility's 
count interval. To avoid missing any reported tasks, the `--interval` option 
has a 60 minutes (60m) maximum, but that and shorter intervals can re-count 
tasks that carry over from one interval to the next or next several.
