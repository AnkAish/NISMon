#!/usr/bin/env bash
####################### CPU Interference #########################
#set -euo pipefail

SSH_DUT=netx4
DUR=2000                    # test duration (s)
CPU_WORKERS=(1 2 4 8 16 32)  # pure‐CPU stressor counts
SWITCH_WORKERS=2            # context-switch stressor count
SIGQ_WORKERS=2              # signal-syscall stressor count (optional)
IPERF_PARALLEL=4            # streams inside the single iperf2 client
SERVER_IP="30.0.0.2"        # DUT’s NIC IP
IFACE_STATS="ens802np1np1"  # interface to sample drops/stats

for N in "${CPU_WORKERS[@]}"; do
  echo "=== Run: $N CPU workers + $SWITCH_WORKERS switchers + $SIGQ_WORKERS sigq + 1×iperf2 ($IPERF_PARALLEL streams) for $DUR s ==="

  # 1) start pure‐CPU load on DUT (auto‐kills after $DUR)
  ssh "$SSH_DUT" "echo 123 | sudo -S stress-ng --cpu $N --cpu-method all --timeout ${DUR}s" >/dev/null 2>&1 &  
  CPU_PID=$!

  # 2) force context switches (lots of light‐weight syscalls)
  ssh "$SSH_DUT" "echo 123 | sudo -S stress-ng --switch $SWITCH_WORKERS --timeout ${DUR}s" >/dev/null 2>&1 &  
  SWITCH_PID=$!

  # 3) (optional) rapid signal syscalls via sigqueue()/sigwaitinfo()
  ssh "$SSH_DUT" "echo 123 | sudo -S stress-ng --sigq $SIGQ_WORKERS --timeout ${DUR}s" >/dev/null 2>&1 &  
  SIGQ_PID=$!

  # 5) launch single iperf2 client with -P streams
  iperf -c "$SERVER_IP" -p 5001 -t "$DUR" -P "$IPERF_PARALLEL" >/dev/null 2>&1 &  
  CLIENT_PID=$!

  # 6) kick off your monitor (background)
  ./metrics_collector.sh "$SSH_DUT" "$N" 300 "$IFACE_STATS" &

  # 7) wait for all stressors and client to finish
  wait "$CPU_PID" "$SWITCH_PID" "$SIGQ_PID" "$CLIENT_PID"

  # iperf server auto‐exits after one test
  echo ">>> Completed run for CPU=$N workers <<<"
done
