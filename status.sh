#!/bin/sh

path=$(dirname "$(realpath $0)")

start() {
    "$path"/status & disown
}

is_running(){
    pgrep -x status >/dev/null
}

is_running_echo(){
    is_running && echo "./status is running" || echo "./status is not running"
}

stop(){
    killall status && echo "Stopped instances"
}

daemon(){
    echo "Starting daemon..."
    while :
    do
        is_running && sleep 10 || start > /dev/null
    done & disown
    sleep 0.1
    is_running && echo "Daemon started !" || echo "Daemon failed"
}

daemon_running(){
    processes=($(pgrep -x status.sh))
    if [ ${#processes[@]} = 1 ];
    then
        false
    else
        true
    fi
    # return $(echo "${#processes[@]/$$}" | bc)
}

daemon_running_echo(){
    daemon_running && echo "./status daemon is running" || is_running_echo
}

daemon_kill(){
    # for all status.sh process except it's own pid
    processes=($(pgrep -x status.sh))
    if [ ${#processes[@]} = 1 ];
    then
        echo "No daemon is running"
        exit
    fi
    for p in "${processes[@]/$$}"
    do
        [ "$p" = "" ] && continue
        kill "$p"
        echo "Killing daemon $p"
    done && printf "\r" || echo "No daemon terminated"
    # killall status.sh
}

print_help(){
  echo "Usage : $0 [status | start | stop | restart | daemon | kill]"
}

if  ! pgrep -x "Xorg" >/dev/null;
then
    echo "Xorg needs to be started first"
fi

if [ "$1" = '' ];
then
    daemon_running_echo
    print_help
    exit
fi

case "$1" in
    "status")
        daemon_running_echo
        exit
    ;;
    "start")
        is_running && echo "./status is already running" || start
        exit
    ;;
    "restart")
        is_running && stop
        start
        exit
    ;;
    "stop")
        stop
        exit
    ;;
    "daemon")
        daemon_running && echo "Daemon already running" || daemon
        exit
    ;;
    "kill")
        daemon_kill
        exit
    ;;
    *)
        echo "Unknown command."
        print_help
        exit
    ;;
esac

exit


while true
do
    "$path"/status
done
