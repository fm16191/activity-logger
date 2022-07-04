import os
from sys import argv, stdout
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
        # DERROR(f"Incorrect timestamp for line {line}")
        return False
    else:
        return datetime_from_timestamp(line.split(" ")[0][1:-1])

def datetime_from_timestamp(str_timestamp):
    timestamp = int(str_timestamp[:-4])
    microseconds = int(str_timestamp[-3:])*1000
    return datetime.fromtimestamp(timestamp) + timedelta(microseconds=microseconds)

def read_data(filename):
    data = {
        'data': [],
        'start': None,
        'end': None
    }

    fo = open(filename, "r")
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

def read_files(filenames):
    tdata = dict()
    tdata['start'] = None
    tdata['end'] = None
    tdata['data'] = []
    for filename in filenames:
        if not os.path.exists(filename):
            DINFO(f"warning : \"{filename}\" : No such file")
            continue
        data = read_data(filename)
        if not data['data']:
            continue
        # with open("test.json", "w") as fo:
        #     json.dump(data['data'], fo, indent=2)
        tdata['data'].extend(data['data'])

        # Get last timestamp to indicate it wasn't recording besides that point.
        if len(filenames) != 1:
            last_timestamp = data['data'][-1]['timestamp']
            ltimestamp_ms = int(last_timestamp[-3:])
            ltimestamp_s = int(last_timestamp[:-4])
            if ltimestamp_ms > 0:
                ltimestamp_ms = ltimestamp_ms + 1
            else:
                ltimestamp_ms = 0
                ltimestamp_s = ltimestamp_s + 1

            tdata['data'].extend([{
                'timestamp': f"{ltimestamp_s}-{ltimestamp_ms:03d}",
                'pid': "00000",
                'exe': "Shutdown",
                'name': "Shutdown"
            }])

    if not tdata['data']:
        DINFO("No data to be analyzed")
        return tdata

    tt = sorted(tdata['data'], key=lambda sub_data: sub_data['timestamp'])
    tdata['data'] = tt

    tdata['start'] = datetime_from_timestamp(tdata['data'][0]['timestamp'])
    tdata['end'] = datetime_from_timestamp(tdata['data'][-1]['timestamp'])

    return tdata
    # print(json.dumps(tdata['data'], indent=2))

def print_time(duration):
    if duration/(3600*24) > 1:
        # return f"{duration/(3600*24):2.0f}d {duration%(3600*24)/3600:02.0f}h {duration%3600/60:02.0f}m"
        return f"{duration/(3600*24):3.0f}d {duration%(3600*24)/3600:02.1f}h"
    elif duration/3600 > 1:
        return f"{duration/3600:4.0f}h {duration%3600/60:02.0f}m"
    else :
        return f"{duration/60:8.1f}m"

def longuest_sessions(data, stdout_size_max=None):
    sessions = sorted(data['data'], key=lambda sub_data:sub_data['duration'], reverse=True)

    print("\n> Longest sessions")
    print(f"{C.BOLD}{C.GREEN}{' Duration':8}{C.YELLOW}{'   Executable'}\t{C.CYAN}{'Window Name'}{C.END}\n")
    for item in sessions[:10]:
        # print(f"{item['duration']:5}   {d['total_duration'].total_seconds()/60:8.1f}m\t{name}")
        name = item['name']
        if stdout_size_max and len(name) > stdout_size_max - 24 - 1:
            name = name[: stdout_size_max - 24 - 1] + "…"
        exe = item['exe']
        if len(exe) > 8:
            exe = f"{exe[:7]}…"
        # print(f"{item['duration'].total_seconds()/60:8.1f}m   {exe:8}\t{name}")
        print(f"{print_time(item['duration'].total_seconds()):10s}   {exe:8}\t{name}")

def data_by_activity_name(data, stdout_size_max=None):
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
        if stdout_size_max and len(name) > stdout_size_max - 24 - 1:
            name = name[: stdout_size_max - 24 - 1] + "…"
        # print(f"{d['occurrences']:5}   {d['total_duration'].total_seconds()/60:8.1f}m\t{name}")
        print(f"{d['occurrences']:5}   {print_time(d['total_duration'].total_seconds()):10s}\t{name}")

def get_active_time(data):
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

    return exes["Shutdown"]['total_duration']

def data_by_exe(data, stdout_size_max=None):
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
        if stdout_size_max and len(exe) > stdout_size_max-24-4:
            exe = exe[:stdout_size_max-24-4] + "..."
        # print(f"{d['occurrences']:5}   {d['total_duration'].total_seconds()/60:8.1f}m\t{exe}")
        print(f"{d['occurrences']:5}   {print_time(d['total_duration'].total_seconds()):10s}\t{exe}")

def exclude(data, exclude, verbose):
    for item in exclude:
        if os.path.exists(item):
            exclude.remove(item)
            if verbose:
                DINFO(f"Removing keywords from '{item}'")
            with open(item, 'r') as fo:
                foo = fo.readlines()
                exclude.extend([line.replace('\n','') for line in foo])

    data['data'] = list(filter(lambda a: a['exe'] not in exclude, data['data']))
    return data

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Displays logged X11 activity')
    parser.add_argument('-f', '--file',
        action='store', nargs='*', help='specify files to be read') # type=argparse.FileType('r')
    parser.add_argument('-l', '--last', action='store', nargs='?', metavar="L",
        type=int, default=1, help='Get the N latest(s) log file(s)')

    parser.add_argument('-a', '--all', action='store_true', default=False,
        help='show every sort outputs')
    parser.add_argument('-e', '--exclude', action='store', nargs='*', default=False,
        help='exclude keywords from argument or filename')
    parser.add_argument('--exclude-desktop', action='store_true',
        help='exclude Desktop from logged activities')
    parser.add_argument('-x', '--exe', action='store', nargs='*', default=False,
        # required=False,
        # metavar='EXE',
        help='sort logged activities by executable name')
    parser.add_argument('-w', '--windows', action='store_true', default=False,
        help='sort logged activities by windows name')
    parser.add_argument('-s', '--longuest-sessions', action='store_true',
        help='sort logged activities by longuest time spent on without switching')

    parser.add_argument('-v', '--verbose', action='store_true', default=False)

    args = parser.parse_args()
    if args.verbose:
        print(args)

    filenames = []
    if args.file:
        filenames = args.file
    else :
        # --last 1 is the default at each program call.
        if args.last <= 0:
            DERROR("--last requires a non null positive integer")
            parser.print_help()
            exit()
        ll = sorted(os.listdir("."), key=os.path.getmtime, reverse=True)
        for file in ll:
            if file.endswith(".wins"):
                filenames.append(file)
                if len(filenames) >= args.last:
                    break
    if len(filenames) == 0:
        print("No log files specified")
        exit()

    if stdout.isatty():
        stdout_size_max = os.get_terminal_size().columns
        if stdout_size_max < 40:
            print(f"{C.ITALIC}Warning : Terminal size {stdout_size_max} too short (at least 40){C.END}")
            stdout_size_max = None
            exit()
    else :
        stdout_size_max = None




    print("====== X11 Activity logger ======")
    if args.verbose:
        print(f"Reading {', '.join(filenames)} ...\n") # , end="\r"
    data = read_files(filenames)
    if not data['start']:
        exit()

    print(f"Started    on   {C.YELLOW}{str(data['start'])[:-7]}{C.END}")
    print(f"Last entry on   {C.YELLOW}{str(data['end'])[:-7]}{C.END}")
    print(f"Total duration  {C.GREEN}{str(data['end'] - data['start'])[:-7]}{C.END}")
    data = add_duration(data)
    if len(filenames) > 1:
        shutdown_time = get_active_time(data)
        print(f"Active time     {C.GREEN}{str(shutdown_time)[:-7]} {C.RED}[{shutdown_time/(data['end'] - data['start'])*100:2.1f}%]{C.END}")

    if args.exclude_desktop: args.exclude.append("Desktop")
    if args.exclude != False:
        data = exclude(data, args.exclude, args.verbose)

    if args.all or args.longuest_sessions != False:
        longuest_sessions(data, stdout_size_max)
    if args.all or args.exe != False:
        data_by_exe(data, stdout_size_max)
    if args.all or args.windows != False:
        data_by_activity_name(data, stdout_size_max)
