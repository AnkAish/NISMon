#!/usr/bin/env bash
####################### Bandwidth Sweep #########################
#set -euo pipefail

SSH_DUT=netx4
DUR=2000                           # test duration (s)
BWS=(100M 200M 500M 1G 2G 5G)     # iperf client target bandwidths
IPERF_PARALLEL=4                  # number of TCP streams per test
SERVER_IP="30.0.0.2"              # DUT’s NIC IP
IFACE_STATS="ens802np1np1"        # interface to sample drops/stats

for BW in "${BWS[@]}"; do
  echo "=== Run: iperf2 @ $BW total across $IPERF_PARALLEL streams for $DUR s ==="

     # 3) launch iperf2 client with target bandwidth and parallel streams
  iperf -c "$SERVER_IP" -p 5001 -t "$DUR" -P "$IPERF_PARALLEL" -b "$BW" \
        >/dev/null 2>&1 &
  CLIENT_PID=$!
  
  # 2) kick off monitor (background)
  ./metrics_collector.sh "$SSH_DUT" "$BW" 300 "$IFACE_STATS" &

  # 4) wait for client & monitor to finish
  wait "$CLIENT_PID"

  echo ">>> Completed run at $BW <<<"
done
