#!/bin/bash

# re='^[0-9]+$'
# if ! [[ $yournumber =~ $re ]] ; then
#    echo "error: Not a number" >&2; exit 1
# fi

folder_path="$PWD"

if [ -f "$1" ]; then
    output=$(python3 stats.py -i "$1" -s --json)
else
    output=$(python3 stats.py --folder "$folder_path" -s --json)
fi

IFS=" " read -ra durations <<< "$(echo "$output" | jq '.[].duration' | xargs)"
IFS=" " read -ra timestamps <<< "$(echo "$output" | jq '.[].timestamp|=(split("-")|join(".")) | .[].timestamp' | xargs)" # tonumber removes last digit if 0
IFS=$'\n' read -d '' -r -a names <<< "$(echo "$output" | jq '.[].name')"
IFS=" " read -ra pids <<< "$(echo "$output" | jq '.[].pid' | xargs)"
IFS=" " read -ra exes <<< "$(echo "$output" | jq '.[].exe' | xargs)"

contents=()
count=${#pids[@]}
for it in $(seq 0 1 $((count-1))); do
    dur=${durations[$it]}
    dur=$(bc -l <<< "$dur")
    dur=$(printf "%.0d" $dur 2>/dev/null)
    h=$((dur/3600))
    m=$((dur/60%60))
    s=$((dur%60))

    contents[${#contents[@]}]=$(printf "%dh%02dm%02ds | $(date -d "@${timestamps[$it]}" --rfc-3339=seconds | sed 's/+.*//g') [${exes[$it]}] ${names[$it]}" $h $m $s 2>/dev/null)

done 

cmd=(dialog --keep-tite --separate-output --checklist "Select options:" 16 120 8)
options=(
    0 "${contents[0]}" off
    1 "${contents[1]}" off
    2 "${contents[2]}" off
    3 "${contents[3]}" off
    4 "${contents[4]}" off
    5 "${contents[5]}" off
    6 "${contents[6]}" off
    7 "${contents[7]}" off
    8 "${contents[8]}" off
    9 "${contents[9]}" off
)
choices=$("${cmd[@]}" "${options[@]}" 2>&1 >/dev/tty)

[ -n "$choices" ] || exit

count=${#choices}
count=$((count - count/2))
# echo $count

answer=$(dialog --title "Replace time" --inputbox "Are you sure ? Type yes to continue" 8 40 --output-fd 1 --keep-tite)

[ $answer != "yes" ] && { echo "Exiting (answer \"$answer\" != yes)"; exit; }

for c in $choices; do
    tr=${timestamps[$c]//./-}
    file="$(find "$folder_path" -maxdepth 1 -name "*.wins" | xargs grep -l "$tr")"
    tr_start="$(grep "$tr" -A1 "$file" | tail -n 1 | sed 's/\[\([0-9]*\)-.*/\1/')" # Search for [0123456-789] and print it without the []
    ./split.sh "$file" "$tr_start"
done
