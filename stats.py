import os
from sys import argv
import json
from datetime import datetime
from datetime import timedelta
import argparse

from colors import C

def DOK(content):
    # [{datetime.now().strftime('%Y %b.%d %H:%M:%S')}]
    print(f"\033[92m{content}\033[0m")
def DINFO(content):
    # [{datetime.now().strftime('%Y %b.%d %H:%M:%S')}]
    print(f"\033[93m{content}\033[0m")
def DERROR(content):
    # [{datetime.now().strftime('%Y %b.%d %H:%M:%S')}]
    print(f"\033[91m{content}\033[0m")

def get_timestamp(line):
    if not " " in line or len(line.split(" ")[0]) != 16 or not "-" in line:
        DERROR(f"Incorrect timestamp for line {line}")
        return False
    else:
        return datetime_from_timestamp(line.split(" ")[0][1:-1])

def datetime_from_timestamp(str_timestamp):
    timestamp = int(str_timestamp[:-4])
    microseconds = int(str_timestamp[-3:])*1000
    return datetime.fromtimestamp(timestamp) + timedelta(microseconds=microseconds)

def read_data(filename):
    fo = open(filename, "r")
    foo = fo.readlines()
    fo.close()

    data = {
        'data': [],
        'start': None,
        'end': None
    }

    if len(foo) < 4:
        return data

    data['start'] = get_timestamp(foo[3])
    data['end'] = get_timestamp(foo[-1])

    if not data['start'] or not data['end']:
        DERROR(f"Logfile {filename} corrupted")
        return data

    for i, line in enumerate(foo[2:]):
        line = line.replace("\n","")
        sline = line.split(" ")

        ldata = {}

        ldata['timestamp'] = sline[0][1:-1]
        ldata['pid'] = sline[1][1:-1]
        ldata['exe'] = sline[2][1:-1]
        if ldata['exe'] == "Desktop":
            ldata['name'] = "Desktop"
        else:
            ldata['name'] = " ".join(sline[3:])
        data['data'].append(ldata)

    return data

def add_duration(data):
    start = datetime_from_timestamp(data['data'][0]['timestamp'])
    for i, item in enumerate(data['data'][1:]):
        end = datetime_from_timestamp(item['timestamp'])

        duration = end - start
        if duration < timedelta(microseconds=0): duration = - duration

        data['data'][i]['duration'] = duration
        # print(data['data'][i+1])

        start = end
    data['data'][-1]['duration'] = timedelta(microseconds=0)
    return data


def print_time(duration):
    if duration/3600 > 1:
        return f"{duration/3600:4.0f}h {duration%3600/60:02.0f}m"
    else :
        return f"{duration/60:8.1f}m"

def longuest_sessions(data, terminal_size_max=None):
    sessions = sorted(data['data'], key=lambda sub_data:sub_data['duration'], reverse=True)

    print("\n> Longest sessions")
    print(f"{C.BOLD}{C.GREEN}{' Duration':8}{C.YELLOW}{'   Executable'}\t{C.CYAN}{'Window Name'}{C.END}\n")
    for item in sessions[:10]:
        # print(f"{item['duration']:5}   {d['total_duration'].seconds/60:8.1f}m\t{name}")
        name = item['name']
        if terminal_size_max and len(name) > terminal_size_max - 24 - 1:
            name = name[: terminal_size_max - 24 - 1] + "…"
        exe = item['exe']
        if len(exe) > 8:
            exe = f"{exe[:7]}…"
        # print(f"{item['duration'].seconds/60:8.1f}m   {exe:8}\t{name}")
        print(f"{print_time(item['duration'].seconds):10s}   {exe:8}\t{name}")

def data_by_activity_name(data, terminal_size_max=None):
    activities = {}

    for i, item in enumerate(data['data']):
        if item['name'] not in activities:
            activities[item['name']] = {
                'total_duration' : item['duration'],
                'occurrences' : 1
                }
        else :
            activities[item['name']]['total_duration'] += item['duration']
            activities[item['name']]['occurrences'] += 1

    activities_by_duration = sorted(activities.items(), key=lambda sub_data:sub_data[1]['total_duration'], reverse=True)

    print("\n> Window names by time spent on")
    print(f"{C.BOLD}{C.GREEN}{'Times':5}{C.YELLOW}{'        Time'}\t{C.CYAN}{'Window Name'}{C.END}\n")

    for item in activities_by_duration[:20]:
        (name, d) = item
        if terminal_size_max and len(name) > terminal_size_max - 24 - 1:
            name = name[: terminal_size_max - 24 - 1] + "…"
        # print(f"{d['occurrences']:5}   {d['total_duration'].seconds/60:8.1f}m\t{name}")
        print(f"{d['occurrences']:5}   {print_time(d['total_duration'].seconds):10s}\t{name}")

def data_by_exe(data, terminal_size_max=None):
    exes = {}

    for i, item in enumerate(data['data']):
        if item['exe'] not in exes:
            exes[item['exe']] = {
                'total_duration' : item['duration'],
                'occurrences' : 1
                }
        else :
            exes[item['exe']]['total_duration'] += item['duration']
            exes[item['exe']]['occurrences'] += 1

    exes_by_duration = sorted(exes.items(), key=lambda sub_data:sub_data[1]['total_duration'], reverse=True)

    print("\n> Programs executable by time spent on")
    print(f"{C.BOLD}{C.GREEN}{'Times':5}{C.YELLOW}{'        Time'}\t{C.CYAN}{'Executable'}{C.END}\n")

    for item in exes_by_duration[:20]:
        (exe, d) = item
        if terminal_size_max and len(exe) > terminal_size_max-24-4:
            exe = exe[:terminal_size_max-24-4] + "..."
        # print(f"{d['occurrences']:5}   {d['total_duration'].seconds/60:8.1f}m\t{exe}")
        print(f"{d['occurrences']:5}   {print_time(d['total_duration'].seconds):10s}\t{exe}")




if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Displays logged X11 activity')
    parser.add_argument('-x', '--exe', action='store', nargs='*', type=int, default=True,
        # required=False,
        # metavar='EXE',
        help='sort logged activities by executable name')
    parser.add_argument('-w', '--windows', action='store_true', default=True,
        help='sort logged activities by windows name')
    parser.add_argument('-s', '--longuest-sessions', action='store_true',
        help='sort logged activities by longuest time spent on without switching')
    parser.add_argument('-v', '--verbose', action='store_true', default=0)
    parser.add_argument('-f', '--file',
        action='store', nargs='*') # type=argparse.FileType('r')

    args = parser.parse_args()

    filename = None
    if args.file:
        filename = args.file[0]
    else:
        ll = sorted(os.listdir("."), key=os.path.getmtime, reverse=True)
        for file in ll:
            if file.endswith(".wins"):
                filename = file
                break
    if not filename:
        print("No window log file specified")
        exit

    terminal_size_max = os.get_terminal_size().columns
    if terminal_size_max < 40:
        print(f"{C.ITALIC}Warning : Terminal size {terminal_size_max} too short (40 requested){C.END}")
        terminal_size_max = None
        exit()



    print("====== X11 Activity logger ======")
    print(f"Reading {filename} ...\n") # , end="\r"
    data = read_data(filename)
    if not data['start']:
        DERROR('Empty or invalid file')
        exit()

    print(f"Started    on   {C.YELLOW}{str(data['start'])[:-7]}{C.END}")
    print(f"Last entry on   {C.YELLOW}{str(data['end'])[:-7]}{C.END}")
    print(f"Total duration  {C.GREEN}{str(data['end'] - data['start'])[:-7]}{C.END}")
    data = add_duration(data)

    if args.longuest_sessions != False:
        longuest_sessions(data, terminal_size_max)
    if args.exe != False:
        data_by_exe(data, terminal_size_max)
    if args.windows != False:
        data_by_activity_name(data, terminal_size_max)
