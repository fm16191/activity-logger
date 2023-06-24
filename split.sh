#!/bin/bash

input="$1"
timestamp="$2"

# Separate a log file in two : every logged activity after $timestamp will now be in a separate file
# as if activity-logger had restarted

([ ! -f "$input" ] || [ -z $timestamp ]) && { echo "Usage : $0 input.wins timestamp"; exit; }

output="$(LC_ALL=en_US.utf8 date --date=@$timestamp +"%d-%m-%Y_%Hh%Mm%S").wins"
echo -en "Starting at $(LC_ALL=en_US.utf8 date --date=@$timestamp +"%a %b %d %T %Y")\n\n" > $output

# Print to new file
sed -n "/^\[$timestamp/,\$p" $input >> $output

# Delete from first file
sed -n "/^\[$timestamp/q;p" -i $input

echo "New file : echo $output"

touch -d @$timestamp $output
stat $output

# If change 'change' time :
# NOW=$(date) && date -s "@$timestamp" && touch $filename && date -s "$NOW"
# Would be better with ntp ... but system-dependant