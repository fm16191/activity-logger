import os
from sys import argv
import json
from datetime import datetime
from datetime import timedelta

from colors import C

def read_data(filename):
    fo = open(filename, "r")
    foo = fo.readlines()
    fo.close()

    data = dict()
    data['starting_date_str'] = foo[0][:1]
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
    timestamp = int(data['data'][0]['timestamp'][:-4])
    microseconds = int(data['data'][0]['timestamp'][-3:])*1000
    start = datetime.fromtimestamp(timestamp)+ timedelta(microseconds=microseconds)
    for i, item in enumerate(data['data'][1:]):
        timestamp = int(item['timestamp'][:-4])
        microseconds = int(item['timestamp'][-3:])*1000
        end = datetime.fromtimestamp(timestamp) + timedelta(microseconds=microseconds)

        duration = end - start
        if duration < timedelta(microseconds=0): duration = - duration

        data['data'][i]['duration'] = duration
        # print(data['data'][i+1])

        start = end
    data['data'][-1]['duration'] = timedelta(microseconds=0)
    return data

def data_by_activity_name(data):
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
        print(f"{d['occurrences']:5}   {d['total_duration'].seconds/60:8.1f}m\t{name}")


def data_by_exe(data):
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

    print(f"Reading {filename} ...")
    data = read_data(filename)
    data = add_duration(data)
    data_by_exe(data)
    data_by_activity_name(data)
