#!/bin/bash

# Output file to store CPU usage
#OUTPUT_FILE="cpu_usage_final.log"

# Duration for which to collect CPU usage
duration=302

# Collect CPU usage statistics each second.
# Extract the idle CPU percentage and calculate active CPU usage.
cpu_usage=$(mpstat 1 "$duration" | awk '$NF ~ /[0-9.]+/ { print 100 - $NF }')

# Calculate the average CPU usage over all measurements.
average_cpu_usage=$(echo "$cpu_usage" | awk '{ total += $1 } END { if (NR > 0) print total/NR; else print 0 }')

# Get the current timestamp
timestamp=$(date +"%Y-%m-%d %H:%M:%S")

# Append the results to the output file
#echo "$timestamp -> $(printf "%.2f" "$average_cpu_usage")%" >> "$OUTPUT_FILE"

# Optional: Print the result to the console as well
echo "Average CPU usage recorded: $(printf "%.2f" "$average_cpu_usage")%"
