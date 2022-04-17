# X11 Activity Logger

X11 Activity Logger is a lightweigt activity logger written in C for X11.

# Features

- Sort applications by time spent on them
- Sort windows names by time spent on them

To be added :
- Analyze multiple log files
- Sort windows names by application name
- Longest session without window changing
- Sort applications according to the number of keystrokes made
- Sort applications according to the keyboard typing speed
- Add options for statistics for the number of keystrokes per sessions, window name, applications
- Detect when user is AFK ? (i.e. no mouse or keyboard events for x seconds, which would no longer require the user to need to change the targeted window on the desktop (none) before going AFK).

# Exemple output

![example.png](example.png)

# Usage

First, compile using
`make`

Then sarts the logger
`./status`

At any time, you can watch where a summary of your latest activities by using

`py stats.py` or

`py stats.py <date>.wins`

> By default, if no log file is specified, the last modified .wins file will be read.

# Keylogger feature (not included by default)
In addition, a small keylogger has been implemented, but it is not included by default. It may be used in the future. 

To enable it, `git apply keylogger.diff`.

For each keystroke, a new line will be written in `<date>.keys` including the timestamp in microseconds, the mouse position at that moment, the state and the code of the key.

# Known issues

> This tool is in beta stage. Please don't mind if you you encounter a problem, and feel free to open an Issue for any suggestion or bug !

- The program randomly segfaults. I assume this is due to the X11 library, under certain conditions that I have not yet been able to reproduce.

- A `free(): invalid pointer` and `IOT instruction` errors occurs at program stop. Not sure why they appear ?
