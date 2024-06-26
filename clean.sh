#!/bin/bash

if [ ! -x "$(command -v dialog)" ]; then
    echo "dialog is not installed on your system"
    exit
fi

echo "Usage : $0 [file]"
echo "        ./stats.py [options] --json | $0"

if [ -t 0 ]; then # Has stuff in input
    if [ "$1" = '' ]; then
        file=$(find . -name "*.wins" -printf "%T@ %p\n" | sort -n -r | sed -E "s/[0-9]+\.[0-9]+\ //" | head -n 1)
    else
        file="$1"
    fi

    if [ ! -f "$file" ]; then echo "File cannot be accessed"; exit; fi
    output=$(python3 stats.py -i "$file" -s -f "_=Desktop" --json)
else
    read -r output
fi

# IFS=$'\r\n' GLOBIGNORE='*' command eval 'testt=("$(echo "$output" | jq '.[].name')")'
# IFS=$'\n' read -d '' -r -a testt <<< "$(echo "$output" | jq '.[].name')"
# # echo "$(echo "$output" | jq '.[].name')"
# echo "all elements : "
# echo "${testt[@]}"
# echo "size : ${#testt[@]}"
# exit

IFS=" " read -ra durations <<< "$(echo "$output" | jq '.[].duration' | xargs)"
IFS=" " read -ra timestamps <<< "$(echo "$output" | jq '.[].timestamp|=(split("-")|join(".")) | .[].timestamp' | xargs)" # tonumber removes last digit if 0
# IFS=$'\r\n' read -ra names <<< "$(echo "$output" | jq '.[].name')"
IFS=$'\n' read -d '' -r -a names <<< "$(echo "$output" | jq '.[].name')"
IFS=" " read -ra pids <<< "$(echo "$output" | jq '.[].pid' | xargs)"
IFS=" " read -ra exes <<< "$(echo "$output" | jq '.[].exe' | xargs)"
IFS=" " read -ra filenames <<< "$(echo "$output" | jq '.[].filename' | xargs)"

contents=()
count=${#pids[@]}
for it in $(seq 0 1 $((count-1))); do
    # printf "\nELT : %d\n" "$it"
    # echo "${durations[$it]}"
    # echo "${timestamps[$it]}"
    # date -d "@${timestamps[$it]}"
    # echo "${pids[$it]}"
    # echo "${exes[$it]}"
    # echo "${names[$it]}"
    dur=${durations[$it]}
    dur=$(bc -l <<< "$dur")
    dur=$(printf "%.0d" $dur 2>/dev/null)
    h=$((dur/3600))
    m=$((dur/60%60))
    s=$((dur%60))

    contents[${#contents[@]}]=$(printf "%dh%02dm%02ds | $(date -d "@${timestamps[$it]}" --rfc-3339=seconds | sed 's/+.*//g') [${exes[$it]}] ${names[$it]}" $h $m $s 2>/dev/null)
done
# echo "${contents[@]}"
# py stats.py -i 15-10-2022_14h46m14.wins -s --json | jq 'to_entries[0] | (.value.timestamp)|=(split("-")|join(".")|tonumber) | .value.duration'

cmd=(dialog --keep-tite --separate-output --checklist "Select options:" 16 120 8)
# for _ in (seq ${#pids[@]})
# options=(
#     0 "${contents[0]}" off
#     1 "${contents[1]}" off
#     2 "${contents[2]}" off
#     3 "${contents[3]}" off
#     4 "${contents[4]}" off
#     5 "${contents[5]}" off
#     6 "${contents[6]}" off
#     7 "${contents[7]}" off
#     8 "${contents[8]}" off
#     9 "${contents[9]}" off
# )

options=()

for i in $(seq 0 1 $((count-1))); do
    options+=( "$i" "${contents[$i]}" "off" )
done

choices=$("${cmd[@]}" "${options[@]}" 2>&1 >/dev/tty)

[ -n "$choices" ] || exit

min="${durations[0]}"
for it in $choices; do
    v=${durations[$it]}
    (( $(echo "$v < $min" | bc -l) )) && min=$v
done

while [ -z "$time" ] || ! [ "$time" -ge 0 ] || ! (( $(echo "$time < $min" | bc -l) )) 2>/dev/null; do
    time=$(dialog --title "Replace time" --inputbox "Input a positive integer (0 to delete complete activity. Integer must be lower than $min) : " 8 40 --output-fd 1 --keep-tite)
done

for c in $choices; do
    # tr=$(echo "${timestamps[$c]}" | sed "s/\./-/g")
    tr=${timestamps[$c]//./-}
    file=${filenames[$c]}
    echo "__$c $tr"
    if [ "$time" -gt 0 ]; then
        tr2="$(echo "${timestamps[$c]} + $time" | bc -l)"
        tr2=${tr2//./-}
        sed -i "/\[$tr].*/{n;s/.*/\[$tr2] \[00000] \[Desktop]/}" $file # Add new line
        timestamp=$(tail -n 1 $file | sed 's/\[\([0-9]*\)-.*/\1/')
        touch -d@$timestamp $file
    else 
        sed -i "s/\[$tr].*/\[$tr] \[00000] \[Desktop]/g" $file
        timestamp=$(tail -n 1 $file | sed 's/\[\([0-9]*\)-.*/\1/')
        touch -d@$timestamp $file
    fi
done
