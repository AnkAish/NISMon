#!/usr/bin/env bash
# metrics_collector.sh
# Run on the client. Assumes passwordless SSH to DUT or sudo -S.
# Usage:
#   ./metrics_collector.sh <SSH_DUT> <RATE_Gbps> <DURATION_s> <IFACE>
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

OUT_CSV="/home/ranjithak/Ankit/NISMon/scripts/normal/${RATE}G_iperf.csv"

# Header
cat > "$OUT_CSV" <<EOF
Timestamp,PCIRdCur,ItoM,ItoMCacheNear,WiL,MemRead,MemWrite,MemTotal,drop_pct(%),CPU_busy(%),ksoft_avg,ksoft_max
EOF

# 0) prime drop & rx counters on DUT
set +e
read prev_drop prev_rx < <(
  ssh "$SSH_DUT" \
    "echo '$DUT_PASS' | sudo -S sh -c '\
       echo \$(cat /sys/class/net/$IFACE/statistics/rx_dropped) \
            \$((\$(cat /sys/class/net/$IFACE/statistics/rx_packets)))'"
)
set -e
prev_drop=${prev_drop:-0}
prev_rx=${prev_rx:-0}

echo "Collecting for $DUR s at ${RATE}Gbps → $OUT_CSV"

for ((i=1; i<=DUR; i++)); do
    ts=$(date +"%Y-%m-%d %H:%M:%S")

    # 1) PCM‐PCIE: extract PCIRdCur, ItoM, ItoMCacheNear, WiL (handles optional K/M suffix)
    # 1) PCM‐PCIE: parse the "*" summary line via awk (concatenate suffix fields)
    read rdcur iom ioc wil < <(
        ssh "$SSH_DUT" \
        "echo '$DUT_PASS' | sudo -S pcm-pcie -i=1 2>/dev/null" \
        | awk '
            /^[[:space:]]*\*/ {
            # PCIRdCur = $2$3, ItoM = $4$5, ItoMCacheNear = $6$7, WiL = $9$10
            printf "%s %s %s %s\n", $2 $3, $4 $5, $6 $7, $9 $10
            exit
            }
        '
    )
    # default to 0 if any field missing
    rdcur=${rdcur:-0}
    iom=${iom:-0}
    ioc=${ioc:-0}
    wil=${wil:-0}


    # 2) PCM-MEMORY (Socket 1)
    set +e
    read mem_read mem_write mem_total < <(
        ssh "$SSH_DUT" \
        "echo '$DUT_PASS' | sudo -S pcm-memory -i=1 2>/dev/null" \
        | awk '
            /NODE 1 Mem Read/  { r = $16 }
            /NODE 1 Mem Write/ { w = $14 }
            /NODE 1 Memory/    { m = $12 }
            END { printf "%s %s %s", r, w, m }
            '
    )
    set -e

     # default to 0 if any field missing
    mem_read=${mem_read:-0}
    mem_write=${mem_write:-0}
    mem_total=${mem_total:-0}

     # 3) packet-drop % with six-decimal precision
    read cur_drop cur_rx < <(
      ssh "$SSH_DUT" \
        "echo \$(cat /sys/class/net/$IFACE/statistics/rx_dropped) \
              \$(cat /sys/class/net/$IFACE/statistics/rx_packets)"
    )
    cur_drop=${cur_drop:-0}; cur_rx=${cur_rx:-0}
    d_drop=$((cur_drop - prev_drop))
    d_rx=$((cur_rx  - prev_rx))
    prev_drop=$cur_drop; prev_rx=$cur_rx
  
    if (( d_drop + d_rx > 0 )); then
      drop_pct=$(awk -v d="$d_drop" -v r="$d_rx" \
        'BEGIN { printf "%.6f", d/(d+r)*100 }')
    else
      drop_pct="0.000000"
    fi
  
      # 4) CPU busy %
    cpu_busy=$(ssh "$SSH_DUT" \
        "echo '$DUT_PASS' | sudo -S mpstat 1 1" \
      | awk '/all/ { printf "%.2f", 100 - $NF; exit }')

    

     # --- 5) Softirq delays: run 1s trace, then compute global averages ---
    kraw=$(ssh "$SSH_DUT" \
      "echo '$DUT_PASS' | sudo -S bpftrace /home/ranjithak/Ankit/NISMon/scripts/cpu_interference/ksoftirq_delays.bt 2>&1" \
      | awk '
          # Lines with avg: "@avg_delay_us[CPU]: VALUE"
          /^@avg_delay_us/ {
            # value is field 2
            sum_avg += $2; count++;
            next;
          }
          # Lines with max: "@max_delay_us[CPU]: VALUE"
          /^@max_delay_us/ {
            sum_max += $2;
            next;
          }
          END {
            if (count>0)
              printf("%.2f %.2f\n", sum_avg/count, sum_max/count);
            else
              printf("0.00 0.00\n");
          }
        '
    )
    # split into two variables:
    read ksoft_avg ksoft_max <<< "$kraw"
    ksoft_avg=${ksoft_avg:-0}
    ksoft_max=${ksoft_max:-0}
  
    # then append these to your CSV:
    echo "$ts,$rdcur,$iom,$ioc,$wil,$mem_read,$mem_write,$mem_total,$drop_pct,$cpu_busy,$ksoft_avg,$ksoft_max" \
      >> "$OUT_CSV"

  done

# wait $IPERF_PID
echo "Done: $OUT_CSV"
