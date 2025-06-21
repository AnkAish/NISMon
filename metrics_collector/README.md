# Metrics Collection Scripts

This folder contains shell scripts for collecting system metrics under various fault injection scenarios while running background `iperf` traffic. The collected metrics include PCIe counters, memory operations, network drops, CPU utilization, and kernel softirq statistics.

---

## 📁 Repository Structure

```plain
metrics_collector/
├── common.sh
├── metrics_collection_with_CPU_interference.sh
├── metrics_collection_with_incast.sh
├── metrics_collection_with_memory_contention.sh
└── metrics_collection_with_random_faults.sh
```

* **common.sh**

  * Orchestrates `iperf` bandwidth sweep tests and invokes metrics collection scripts.
* **metrics\_collection\_with\_CPU\_interference.sh**

  * Samples metrics under CPU interference faults.
* **metrics\_collection\_with\_incast.sh**

  * Samples metrics during incast traffic scenarios.
* **metrics\_collection\_with\_memory\_contention.sh**

  * Samples metrics under memory contention faults.
* **metrics\_collection\_with\_random\_faults.sh**

  * Injects random faults (incast, memory contention, CPU interference) at random intervals while collecting metrics.

---

## 📝 Overview

Each `metrics_collection_*.sh` script connects to the DUT via SSH, samples the following metrics at regular intervals, and writes them to a CSV file named according to the scenario and bandwidth:

* `PCIRdCur`        : PCIe read current count
* `ItoM`            : In-to-memory transactions
* `ItoMCacheNear`   : Near-cache memory transactions
* `WiL`             : Write-in-latency events
* `MemRead`         : Memory read operations
* `MemWrite`        : Memory write operations
* `MemTotal`        : Total memory usage
* `drop_pct` (%)    : Packet drop percentage on the interface
* `CPU_busy` (%)    : CPU busy percentage
* `ksoft_avg`       : Average kernel softirq rate
* `ksoft_max`       : Maximum kernel softirq rate

---

## ⚙️ Prerequisites

* **bash** shell (GNU Bash 4+ recommended)
* **iperf** version 2 on both host and DUT
* SSH passwordless access from the host to the DUT
* `common.sh` configured with the DUT’s hostname/IP, NIC interface, and sampling parameters

---

## 🚀 Usage

1. **Configure `common.sh`**

   * `SSH_DUT`: DUT’s SSH hostname or IP.
   * `SERVER_IP`: DUT’s NIC IP.
   * `IFACE_STATS`: Interface to monitor (drops and stats).
   * `BWS`: Array of `iperf` bandwidth targets.
   * `DUR`: Duration (seconds) for background traffic (default `2500`).
   * **Metrics duration**: adjust the hard-coded `300` (seconds) for metrics collection in the invocation line.

2. **Make scripts executable**

   ```bash
   chmod +x *.sh
   ```

3. **Run the standard sweep**

   ```bash
   ./common.sh
   ```

   * Launches `iperf` for `DUR` seconds across parallel streams.
   * For each bandwidth in `BWS`, runs the selected metrics script for the configured metrics duration.
   * Outputs CSV files named: `metrics_<scenario>_<bandwidth>.csv`.

4. **Run with random faults**

   * Modify in `common.sh`:

     ```bash
     DUR=5000               # background traffic duration (s)
     METRIC_DUR=600         # metrics collection duration (s)
     ```
   * Replace the metrics invocation line to use `metrics_collection_with_random_faults.sh`:

     ```bash
     ./metrics_collection_with_random_faults.sh "$SSH_DUT" "$BW" $METRIC_DUR "$IFACE_STATS" &
     ```
   * Execute:

     ```bash
     ./common.sh
     ```
   * This will inject faults at random points during the 5000s traffic and collect metrics for 600s per bandwidth.

---

## 📂 Example Outputs

After running, you will see files like:

```plain
metrics_CPU_interference_5G.csv
metrics_incast_7.5G.csv
metrics_memory_contention_10G.csv
metrics_random_faults_7.5G.csv
```

Each CSV contains a header row with metric names and one row per sampling interval.

---

## 🛠 Customization

* **Background traffic duration**: set `DUR` in `common.sh`.
* **Metrics collection duration**: set `METRIC_DUR` in `common.sh`.
* **Fault types**: edit `metrics_collection_with_random_faults.sh` to adjust fault intervals or types.
* **Additional metrics**: append new counters in any `metrics_collection_*.sh` as needed.

---
