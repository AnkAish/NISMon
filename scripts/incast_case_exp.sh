#!/usr/bin/env bash
####################### INCAST #########################
set -euo pipefail

# 0) Customize these
SERVER="30.0.0.2"         # iperf server IP (DUT)
PORT=5001                # iperf port (default for iperf2)
DUR=300                  # seconds per run
IFACE=ens802np1np1        # interface to monitor on DUT
SSH_DUT=netx4    # how incast_exp.sh SSHs to the DUT

# 1) Incast degrees to test
SENDERS=(4 8 16 32 64 128)

for N in "${SENDERS[@]}"; do
  echo "=== $N‐sender incast @ $SERVER:$PORT for $DUR s ==="

  # 2) launch N iperf clients in background
  for i in $(seq 1 "$N"); do
    iperf -c "$SERVER" -t 2500 > /dev/null 2>&1 &
  done

  # 3) start your metrics collector in parallel
  ./metrics_collector.sh $SSH_DUT $N $DUR $IFACE &

  # 4) wait for all the iperf processes to finish
  wait
  echo ">>> Completed $N‐sender run <<<"
  echo
done

echo "All incast scenarios complete."
