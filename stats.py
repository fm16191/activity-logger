import os
from sys import argv
import json
from datetime import datetime
from datetime import timedelta

from colors import C

def datetime_from_timestamp(str_timestamp):
    timestamp = int(str_timestamp[:-4])
    microseconds = int(str_timestamp[-3:])*1000
    return datetime.fromtimestamp(timestamp) + timedelta(microseconds=microseconds)

def read_data(filename):
    fo = open(filename, "r")
    foo = fo.readlines()
    fo.close()

    data = dict()
    data['starting_date_str'] = datetime_from_timestamp(foo[3].split(" ")[0][1:-1])
    data['ending_date_str'] = datetime_from_timestamp(foo[-1].split(" ")[0][1:-1])

    data['data'] = []

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
    
    print(f"\n{C.BOLD}{C.GREEN}{'Times':5}{C.YELLOW}{'        Time'}\t{C.CYAN}{'Window Name'}{C.END}\n")

    for item in activities_by_duration[:20]:
        (name, d) = item
        if terminal_size_max and len(name) > terminal_size_max - 24 - 4:
            name = name[: terminal_size_max - 24 - 4] + "..."
        print(f"{d['occurrences']:5}   {d['total_duration'].seconds/60:8.1f}m\t{name}")


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
    
    print(f"\n{C.BOLD}{C.GREEN}{'Times':5}{C.YELLOW}{'        Time'}\t{C.CYAN}{'Executable'}{C.END}\n")

    for item in exes_by_duration[:20]:
        (exe, d) = item
        if terminal_size_max and len(exe) > terminal_size_max-24-4:
            exe = exe[:terminal_size_max-24-4] + "..."
        print(f"{d['occurrences']:5}   {d['total_duration'].seconds/60:8.1f}m\t{exe}")




if __name__ == "__main__":
    filename = None
    if len(argv) > 1:
        filename = argv[1]
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
    print(f"Started on      {C.YELLOW}{str(data['starting_date_str'])[:-7]}{C.END}")
    print(f"Ended   on      {C.YELLOW}{str(data['ending_date_str'])[:-7]}{C.END}")
    print(f"Total duration  {C.GREEN}{str(data['ending_date_str'] - data['starting_date_str'])[:-7]}{C.END}")
    data = add_duration(data)

    data_by_exe(data, terminal_size_max)
    data_by_activity_name(data, terminal_size_max)
