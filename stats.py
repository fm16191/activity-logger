#!/usr/bin/env python3

import os
from sys import argv, stdout
import json
from datetime import datetime
from datetime import timedelta
import argparse

from colors import C

def DOK(content):
    print(f"\033[92m{content}\033[0m")
def DINFO(content):
    print(f"\033[93m{content}\033[0m")
def DERROR(content):
    print(f"\033[91m{content}\033[0m")


def get_timestamp(line):
    if not " " in line or len(line.split(" ")[0]) != 16 or not "-" in line:
        # DERROR(f"Incorrect timestamp for line {line}")
        return False
    else:
        return datetime_from_timestamp(line.split(" ")[0][1:-1])


def datetime_from_timestamp(str_timestamp):
    timestamp = int(str_timestamp[:-4])
    microseconds = int(str_timestamp[-3:]) * 1000
    return datetime.fromtimestamp(timestamp) + timedelta(microseconds=microseconds)


def read_data(filename, verbose):
    data = {'data': [], 'start': None, 'end': None, 'filename': filename}

    fo = open(filename, "r", errors='ignore')
    if not fo.readable():
        DERROR(f"Error : {filename} couldn't be read.")
        return data
    foo = fo.readlines()
    fo.close()

    if len(foo) < 4:
        return data

    data['start'] = get_timestamp(foo[3])
    data['end'] = get_timestamp(foo[-1])

    if not data['start'] or not data['end']:
        DERROR(f"{filename} is not a valid logfile")
        return data

    for line in foo[2:]:
        line = line.replace('\n', '')
        sline = line.split(' ')

        ldata = {}

        ldata['timestamp'] = sline[0][1:-1]
        ldata['pid'] = sline[1][1:-1]
        ldata['exe'] = sline[2][1:-1]
        if ldata['exe'] == "Desktop":
            ldata['name'] = "Desktop"
        else:
            ldata['name'] = ' '.join(sline[3:])
        if verbose:
            ldata['filename'] = filename
        data['data'].append(ldata)

    return data


def add_duration(data, last_entry_date):
    start = datetime_from_timestamp(data['data'][0]['timestamp'])
    for i, item in enumerate(data['data'][1:]):
        end = datetime_from_timestamp(item['timestamp'])

        duration = abs(end - start)
        data['data'][i]['duration'] = duration

        start = end
    data['data'][-1]['duration'] = abs(last_entry_date - start)
    return data


def read_files(filenames, verbose):
    tdata = dict()
    tdata['start'] = None
    tdata['end'] = None
    tdata['data'] = []
    for filename in filenames:
        if not os.path.exists(filename):
            DINFO(f"warning : \"{filename}\" : No such file")
            continue

        if verbose and not json:
            DINFO(f"Reading {filename}")
        data = read_data(filename, verbose)
        if not data['data']:
            continue
        tdata['data'].extend(data['data'])

        # Get last timestamp to indicate it wasn't recording besides that point.
        if len(filenames) != 1:
            last_timestamp = data['data'][-1]['timestamp']
            last_timestamp_ms = int(last_timestamp[-3:])
            last_timestamp_s = int(last_timestamp[:-4])
            if last_timestamp_ms > 0:
                last_timestamp_ms = last_timestamp_ms + 1
            else:
                last_timestamp_ms = 0
                last_timestamp_s = last_timestamp_s + 1

            tdata['data'].extend([{
                'timestamp': f"{last_timestamp_s}-{last_timestamp_ms:03d}",
                'pid': "00000",
                'exe': "Shutdown",
                'name': "Shutdown",
                }])

    if not tdata['data']:
        DINFO("No data to be analyzed")
        return tdata

    tt = sorted(tdata['data'], key=lambda sub_data: sub_data['timestamp'])
    tdata['data'] = tt

    tdata['start'] = datetime_from_timestamp(tdata['data'][0]['timestamp'])
    tdata['end'] = datetime_from_timestamp(tdata['data'][-1]['timestamp'])

    return tdata


def print_time(duration):
    if duration / (3600*24) > 1.0:
        return f"{int(duration/(3600*24)):3.0f}d {duration%(3600*24)/3600:3.1f}h"
    elif duration / 3600 > 1.0:
        return f"{int(duration/3600):4.0f}h {duration%3600/60:02.0f}m"
    elif duration / 60 > 1:
        return f"{int(duration/60):8.1f}m"
    else:
        return f"{duration:8.0f}s"


def longuest_sessions(data, json_dump=None, stdout_size_max=None):
    sessions = sorted(data['data'], key=lambda sub_data: sub_data['duration'], reverse=True)
    if json_dump:
        for i in range(len(sessions[:10])):
            # sessions[i]['timstamp2'] = float(sessions[i]['timestamp'].replace("-","."))
            sessions[i]['duration'] = sessions[i]['duration'].total_seconds()
        print(json.dumps(sessions[:10], ensure_ascii=False))
        return

    print("\n> Longest sessions")
    print(f"{C.BOLD}{C.GREEN}{' Duration':8}{C.YELLOW}{'   Executable'}\t{C.CYAN}{'Window Name'}{C.END}\n")
    for item in sessions[:10]:
        name = item['name']
        if stdout_size_max and len(name) > stdout_size_max - 24 - 1:
            name = name[:stdout_size_max - 24 - 1] + "…"
        exe = item['exe']
        if len(exe) > 8:
            exe = f"{exe[:7]}…"
        print(f"{print_time(item['duration'].total_seconds()):10s}   {exe:8}\t{name}")


def history(data, max_print=None, json_dump=None, stdout_size_max=None):
    if max_print == None:
        max_print = len(data['data'])

    print("\n> Sessions history by latest")
    print(f"{C.BOLD}{C.GREEN}{' Date':9}{' Duration':8}{C.YELLOW}{'   Executable'}\t{C.CYAN}{'Window Name'}{C.END}\n")

    for item in data['data'][::-1][:max_print]:
        name = item['name']
        if stdout_size_max and len(name) > stdout_size_max - 24 - 1:
            name = name[:stdout_size_max - 24 - 1] + "…"
        exe = item['exe']
        if len(exe) > 8:
            exe = f"{exe[:7]}…"
        date = datetime_from_timestamp(item['timestamp']).strftime("%H:%M:%S") # %d/%m/%y
        print(f"{date}{print_time(item['duration'].total_seconds()):10s}   {exe:8}\t{name}")


def data_by_activity_name(data, json_dump=None, stdout_size_max=None):
    activities = {}

    for item in data['data']:
        if item['name'] not in activities:
            activities[item['name']] = {
                'total_duration': item['duration'],
                'occurrences': 1,
                }
        else:
            activities[item['name']]['total_duration'] += item['duration']
            activities[item['name']]['occurrences'] += 1

    activities_by_duration = sorted(activities.items(), key=lambda sub_data: sub_data[1]['total_duration'], reverse=True)

    print("\n> Window names by time spent on")
    print(f"{C.BOLD}{C.GREEN}{'Times':5}{C.YELLOW}{'        Time'}\t{C.CYAN}{'Window Name'}{C.END}\n")

    for item in activities_by_duration[:20]:
        (name, d) = item
        if stdout_size_max and len(name) > stdout_size_max - 24 - 1:
            name = name[:stdout_size_max - 24 - 1] + "…"
        print(f"{d['occurrences']:5}   {print_time(d['total_duration'].total_seconds()):10s}\t{name}")


def get_active_time(data):
    exes = {}

    for item in data['data']:
        if item['exe'] not in exes:
            exes[item['exe']] = {
                'total_duration': item['duration'],
                'occurrences': 1,
                }
        else :
            exes[item['exe']]['total_duration'] += item['duration']
            exes[item['exe']]['occurrences'] += 1

    return exes["Shutdown"]['total_duration']


def data_by_exe(data, json_dump=None, stdout_size_max=None):
    exes = {}

    for item in data['data']:
        if item['exe'] not in exes:
            exes[item['exe']] = {
                'total_duration': item['duration'],
                'occurrences': 1,
                }
        else:
            exes[item['exe']]['total_duration'] += item['duration']
            exes[item['exe']]['occurrences'] += 1

    exes_by_duration = sorted(exes.items(), key=lambda sub_data: sub_data[1]['total_duration'], reverse=True)

    print("\n> Programs executable by time spent on")
    print(f"{C.BOLD}{C.GREEN}{'Times':5}{C.YELLOW}{'        Time'}\t{C.CYAN}{'Executable'}{C.END}\n")

    for item in exes_by_duration[:20]:
        (exe, d) = item
        if stdout_size_max and len(exe) > stdout_size_max - 24 - 4:
            exe = exe[:stdout_size_max - 24 - 4] + "..."
        print(f"{d['occurrences']:5}   {print_time(d['total_duration'].total_seconds()):10s}\t{exe}")


def filter_data(data, fl, ex):
    # Filtering keywords
    if len(fl) >= 1:
        lss = []
        for x in data['data']:
            for item in fl:
                item = item.lower()
                if item in x['exe'].lower() or item in x['name'].lower():
                    lss.append(x)
                    break
        data['data'] = lss

    # Excluding keywords
    imax = len(data['data'])
    i = 0
    while i < imax:
        x = data['data'][i]
        exe = x['exe'].lower()
        name = x['name'].lower()
        for item in ex:
            if item in exe or item in name:
                # del data['data'][i]
                data['data'].pop(i)
                i = i - 1
                imax = imax - 1
                break
        i = i + 1
    return data

def sort_files(filename):
    fo = open(filename, "r", errors='ignore')
    if not fo.readable():
        DERROR(f"{filename} cannot be read.")
    foo = fo.readlines()
    fo.close()
    try:
        return foo[3].split(' ')[0][1:-5]
    except:
        return "[9999999999-999]"

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Displays logged X11 activity')
    parser.add_argument('-i', '--input',
        action='store', nargs='*', help='specify input files to be read') # type=argparse.FileType('r')
    parser.add_argument('-l', '--last', nargs=1, metavar="L", type=int, default=[1], # Has to be a list ??
        help='Get the L latests log files')
    parser.add_argument('--folder', nargs=1, metavar="F", default=["data"],
        help='Set folder')

    parser.add_argument('-a', '--all', action='store_true', default=False,
        help='show every sort outputs')
    parser.add_argument('-f', '--filter', action='append', type=str, default=[],
        help='filter data. Usage : -f\"[+keyword to filter] [-keyword to exclude]...\"')
    parser.add_argument('-x', '--exe', action='store', nargs='*', default=False,
        # required=False,
        # metavar='EXE',
        help='sort logged activities by executable name')
    parser.add_argument('-w', '--windows', action='store_true', default=False,
        help='sort logged activities by windows name')
    parser.add_argument('-s', '--longuest-sessions', action='store_true',
        help='sort logged activities by longuest time spent on without switching')
    parser.add_argument('--history', action='store', type=int, default=[0],
        help='list latests sessions entry')
    parser.add_argument('--json', action='store_true', default=False,
        help='display in JSON format')

    parser.add_argument('-v', '--verbose', action='store_true', default=False)

    args = parser.parse_args()
    # args, unknown = parser.parse_known_args()
    if not args.json and args.verbose:
        DINFO(f"Arguments : {args}")

    filenames = []
    if args.input:
        filenames = args.input
    else:
        args.last = args.last[0]
        if args.last < 0: args.last = 1
        folder = args.folder[0]

        ll = sorted([os.path.join(folder, file) for file in os.listdir(folder) if file.endswith(".wins")], key=lambda x: sort_files(x), reverse=True)
        filenames = ll[:args.last] if args.last else ll
        if args.verbose :
            DINFO(f"Filenames : {filenames}")

    if len(filenames) == 0:
        print("No log files specified")
        exit()

    if stdout.isatty():
        stdout_size_max = os.get_terminal_size().columns
        if stdout_size_max < 40:
            print(f"{C.ITALIC}Warning : Terminal size {stdout_size_max} too short (at least 40){C.END}")
            exit()
    else:
        stdout_size_max = None

    if not args.json:
        print("======= X11 Activity logger =======")
    if not args.json and args.verbose:
        DINFO(len(filenames))
    data = read_files(filenames, args.verbose)
    if not data['start']:
        exit()

    if not args.json:
        print(f"Started    on   {C.YELLOW}{str(data['start']).split('.')[0]}{C.END}")
        print(f"Last entry on   {C.YELLOW}{str(data['end']).split('.')[0]}{C.END}")
        print(f"Total duration  {C.GREEN}{str(data['end'] - data['start']).split('.')[0]}{C.END}")
    data = add_duration(data, data['end'])
    if len(filenames) > 1:
        shutdown_time = get_active_time(data)
        active_time = (data['end'] - data['start'] - shutdown_time)
        if not args.json:
            print(f"Active time     {C.GREEN}{str(active_time)[:-7]} {C.RED}[{active_time/(data['end'] - data['start'])*100:2.1f}%]{C.END}")

        if args.verbose and not args.json:
            print(f"Files           {len(filenames)}")
            print(f"Entries         {len(data['data'])}")

    if args.filter:
        args.filter = " ".join(args.filter)
        fl = [] # +keyword
        ex = [] # -keyword
        for f in args.filter.split(" "):
            if f[0] == "+":
                fl.append(f[1:].lower())
            elif f[0] == "_":
                ex.append(f[1:].lower())

        if not args.json and args.verbose:
            DINFO(f"Filtering{' '.join([f'+{f}' for f in fl])} {' '.join([f'-{e}' for e in ex])}")

        data = filter_data(data, fl, ex)

    if args.all or args.longuest_sessions != False:
        longuest_sessions(data, args.json, stdout_size_max)
    if args.all or args.exe != False:
        data_by_exe(data, args.json, stdout_size_max)
    if args.all or args.windows != False:
        data_by_activity_name(data, args.json, stdout_size_max)
    if args.history != [0]:
        history(data, args.history, args.json, stdout_size_max)
