#!/usr/bin/env bash
# random_faults_exp.sh
# Run on the client. Assumes passwordless SSH to DUT or sudo -S.
# Injects incast, memory, or CPU faults at random times over the experiment.
# Usage:
#   ./random_faults_exp.sh <SSH_DUT> <RATE_Gbps> <DURATION_s> <IFACE>

set -euo pipefail

if [[ $# -lt 4 ]]; then
  echo "Usage: $0 <SSH_DUT> <RATE_Gbps> <DURATION_s> <IFACE>"
  exit 1
fi

SSH_DUT=$1
RATE=$2
DUR=$3
IFACE=$4
DUT_PASS=123   # or prompt for it if needed

# Output CSV (single combined file for all fault types)
OUT_CSV="/home/ranjithak/Ankit/${RATE}.csv"
# Probability (percent) to inject a fault each second
FAULT_PROB_PCT=20        # 20% chance per second
# Incast parameters
VM_WORKERS=32
VM_BYTES=4G
VM_METHOD=write64
INCAST_SENDERS=32
FAULT_DURATION=3         # fault lasts this many seconds
SERVER_IP="30.0.0.2"

# Header
cat > "$OUT_CSV" <<EOF
Timestamp,PCIRdCur,ItoM,ItoMCacheNear,WiL,MemRead,MemWrite,MemTotal,drop_pct(%),CPU_busy(%),ksoft_avg,ksoft_max,fault
EOF

# prime drop & rx counters on DUT
set +e
read prev_drop prev_rx < <(
  ssh "$SSH_DUT" \
    "echo '$DUT_PASS' | sudo -S sh -c '
       echo \$(cat /sys/class/net/$IFACE/statistics/rx_dropped) 
            \$(cat /sys/class/net/$IFACE/statistics/rx_packets)'"
)
set -e
prev_drop=${prev_drop:-0}
prev_rx=${prev_rx:-0}

echo "Collecting for $DUR s at ${RATE}Gbps → $OUT_CSV"

for ((i=1; i<=DUR; i++)); do
    ts=$(date +"%Y-%m-%d %H:%M:%S")
    fault=0

    # decide randomly to inject a fault this second
    if (( RANDOM % 100 < FAULT_PROB_PCT )); then
        # choose a random fault type: 1=incast, 2=memory, 3=cpu
        fault=$((RANDOM % 3 + 1))
        case $fault in
            1)
                echo "[$ts] Injecting INCAST fault"
                for ((s=1; s<=INCAST_SENDERS; s++)); do
                    iperf -c "$SERVER_IP" -p 5002 -t "$FAULT_DURATION" -P 2 \
                        >/dev/null 2>&1 &
                done
                ;;
            2)
                echo "[$ts] Injecting MEMORY_CONTENTION fault"
                ssh "$SSH_DUT" "echo '$DUT_PASS' | sudo -S \
                  stress-ng --vm $VM_WORKERS --vm-bytes $VM_BYTES \
                            --vm-method $VM_METHOD --timeout ${FAULT_DURATION}s" \
                  >/dev/null 2>&1 &
                ;;
            3)
                echo "[$ts] Injecting CPU_INTERFERENCE fault"
                ssh "$SSH_DUT" "echo '$DUT_PASS' | sudo -S taskset -c 20-39,60-79 chrt -f 99 stress-ng --cpu 40 --timeout ${FAULT_DURATION}s" >/dev/null 2>&1 &
                ;;
        esac
    fi

    # --- gather metrics ---
    # 1) PCM-PCIE metrics
    read rdcur iom ioc wil < <(
        ssh "$SSH_DUT" \
        "echo '$DUT_PASS' | sudo -S pcm-pcie -i=1 2>/dev/null" \
        | awk '/^[[:space:]]*\*/ { printf "%s %s %s %s\n", $2 $3, $4 $5, $6 $7, $9 $10; exit }'
    )
    rdcur=${rdcur:-0}; iom=${iom:-0}; ioc=${ioc:-0}; wil=${wil:-0}

    # 2) PCM-MEMORY metrics
    set +e
    read mem_read mem_write mem_total < <(
        ssh "$SSH_DUT" \
        "echo '$DUT_PASS' | sudo -S pcm-memory -i=1 2>/dev/null" \
        | awk '/NODE 1 Mem Read/  { r = $16 } /NODE 1 Mem Write/ { w = $14 } /NODE 1 Memory/ { m = $12 } END { printf "%s %s %s", r, w, m }'
    )
    set -e
    mem_read=${mem_read:-0}; mem_write=${mem_write:-0}; mem_total=${mem_total:-0}

    # 3) packet-drop %
    read cur_drop cur_rx < <(
      ssh "$SSH_DUT" \
        "echo \$(cat /sys/class/net/$IFACE/statistics/rx_dropped) \$(cat /sys/class/net/$IFACE/statistics/rx_packets)"
    )
    cur_drop=${cur_drop:-0}; cur_rx=${cur_rx:-0}
    d_drop=$((cur_drop - prev_drop)); d_rx=$((cur_rx - prev_rx))
    prev_drop=$cur_drop; prev_rx=$cur_rx
    if (( d_drop + d_rx > 0 )); then
      drop_pct=$(awk -v d="$d_drop" -v r="$d_rx" 'BEGIN { printf "%.6f", d/(d+r)*100 }')
    else
      drop_pct="0.000000"
    fi

    # 4) CPU busy %
    cpu_busy=$(ssh "$SSH_DUT" \
        "echo '$DUT_PASS' | sudo -S mpstat 1 1" \
        | awk '/all/ { printf "%.2f", 100 - $NF; exit }')

    # 5) Softirq delays
    kraw=$(ssh "$SSH_DUT" \
      "echo '$DUT_PASS' | sudo -S bpftrace /home/ranjithak/Ankit/NISMon/scripts/cpu_interference/ksoftirq_delays_v1.bt 2>&1" \
      | awk -F': ' '
        /^@avg_delay_us/ { sum_avg += $2; cnt_avg++ }
        /^@max_delay_us/ { sum_max += $2; cnt_max++ }
        END {
          avg = (cnt_avg ? sum_avg/cnt_avg : 0)
          mx  = (cnt_max ? sum_max/cnt_max : 0)
          printf("%.2f %.2f\n", avg, mx)
        }'
      )
    read ksoft_avg ksoft_max <<< "$kraw"
    ksoft_avg=${ksoft_avg:-0}; ksoft_max=${ksoft_max:-0}

    # Write row
    echo "$ts,$rdcur,$iom,$ioc,$wil,$mem_read,$mem_write,$mem_total,$drop_pct,$cpu_busy,$ksoft_avg,$ksoft_max,$fault" \
        >> "$OUT_CSV"

done

echo "Done: $OUT_CSV"
