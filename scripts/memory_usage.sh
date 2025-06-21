#!/bin/bash

# Duration to monitor in seconds
DURATION=302
LOG_FILE="mem_usage_final.log"

# Initialize variables
TOTAL_MEM_USAGE=0
SAMPLES=0

# Clear the log file before starting
# > "$LOG_FILE"

#echo "New run" >> "$LOG_FILE"

# Loop to collect memory usage samples
while [ $SAMPLES -lt $DURATION ]; do
    # Get used memory percentage
    MEM_USAGE=$(free -m | awk '/Mem:/ { print $3/$2 * 100.0 }')

    # Add to total memory usage
    TOTAL_MEM_USAGE=$(echo "$TOTAL_MEM_USAGE + $MEM_USAGE" | bc)

    # Increment the sample counter
    ((SAMPLES++))

    # Sleep for 1 second before the next sample
    sleep 1
done

# Calculate the average memory usage
AVERAGE_MEM_USAGE=$(echo "$TOTAL_MEM_USAGE / $DURATION" | bc -l)

# Format output
FINAL_OUTPUT="$(printf "%.2f" $AVERAGE_MEM_USAGE)%"

# Print and save to log file
echo "New run: $FINAL_OUTPUT"
# echo "New run: $FINAL_OUTPUT" >> "$LOG_FILE"
