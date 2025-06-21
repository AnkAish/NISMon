#!/bin/bash

# Set the network interface
IFACE="ens802np1np1"

# Duration to monitor in seconds
DURATION=62

# Log file
LOG_FILE="link_utilization_final.log"
#echo "New run" >> "$LOG_FILE"

# Get timestamp
TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")

# Get initial RX and TX bytes
RX_BYTES_START=$(cat /sys/class/net/$IFACE/statistics/rx_bytes)
TX_BYTES_START=$(cat /sys/class/net/$IFACE/statistics/tx_bytes)

# Wait for the specified duration
sleep $DURATION

# Get final RX and TX bytes
RX_BYTES_END=$(cat /sys/class/net/$IFACE/statistics/rx_bytes)
TX_BYTES_END=$(cat /sys/class/net/$IFACE/statistics/tx_bytes)

# Calculate bytes received and transmitted over the duration
RX_DIFF=$((RX_BYTES_END - RX_BYTES_START))
TX_DIFF=$((TX_BYTES_END - TX_BYTES_START))

# Convert to bits (1 Byte = 8 bits)
RX_BITS=$((RX_DIFF * 8))
TX_BITS=$((TX_DIFF * 8))

# Convert to Gbps (1 Gbps = 10^9 bps)
RX_GBPS=$(echo "scale=2; $RX_BITS / (60 * 10^9)" | bc)
TX_GBPS=$(echo "scale=2; $TX_BITS / (60 * 10^9)" | bc)

# Calculate total utilization
TOTAL_GBPS=$(echo "scale=2; $RX_GBPS + $TX_GBPS" | bc)

# Format output
FINAL_OUTPUT="$TOTAL_GBPS"

# Append to log file
echo "New run: $FINAL_OUTPUT" >> "$LOG_FILE"
