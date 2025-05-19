#!/usr/bin/env bash
####################### Memory Contention #########################
#set -euo pipefail

SSH_DUT=netx4
DUR=2000                  # test duration (s)
WORKERS=(1 2 4 8 16 32)  # memory‐stressor counts
IPERF_PARALLEL=4        # streams inside the single iperf2 client
SERVER_IP="30.0.0.2"     # DUT’s NIC IP
IFACE_STATS="ens802np1np1"  # interface to sample drops/stats

for N in "${WORKERS[@]}"; do
  echo "=== Run: $N stress workers + 1×iperf2 ($IPERF_PARALLEL streams) for $DUR s ==="

  # 1) start memory stress on DUT (auto‐kills itself after $DUR)
  ssh "$SSH_DUT" "echo 123 | sudo -S stress-ng --vm $N --vm-bytes 4G --vm-method write64 --timeout ${DUR}s" >/dev/null 2>&1 &  
  STRESS_PID=$!

    # 4) launch single iperf2 client with -P streams
  iperf -c "$SERVER_IP" -p 5001 -t "$DUR" -P "$IPERF_PARALLEL" >/dev/null 2>&1 &
  CLIENT_PID=$!

  # 4) kick off your monitor (in background)
  ./metrics_collector.sh "$SSH_DUT" "$N" 300 "$IFACE_STATS" &

  # 5) wait for both stress-ng and iperf client to finish
  wait "$STRESS_PID" "$CLIENT_PID"

  # (the iperf server process will have already exited due to -1)
  echo ">>> Completed run for N=$N <<<"
done

