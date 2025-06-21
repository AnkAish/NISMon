# Metrics Collection Scripts

This folder contains shell scripts for collecting system metrics under various fault injection scenarios while running background traffic. The collected metrics include PCIe read counters, memory operations, network drops, CPU utilization, and kernel softirq statistics.

---

## 📁 Repository Structure

```plain
metrics_collector/
├── common.sh
├── metrics_collection_with_CPU_interference.sh
├── metrics_collection_with_incast.sh
└── metrics_collection_with_memory_contention.sh
```

* **common.sh**

  * Orchestrates bandwidth sweep tests using `iperf` and invokes the appropriate metrics collection script.
* **metrics\_collection\_with\_CPU\_interference.sh**

  * Collects system metrics while injecting CPU interference.
* **metrics\_collection\_with\_incast.sh**

  * Collects system metrics during an incast traffic scenario.
* **metrics\_collection\_with\_memory\_contention.sh**

  * Collects system metrics under memory contention faults.

---

## 📝 Overview

Each `metrics_collection_*.sh` script samples the following metrics on the DUT for a fixed duration:

* `PCIRdCur`     : PCIe read current count
* `ItoM`         : In-to-memory transactions
* `ItoMCacheNear`: Near cache memory transactions
* `WiL`          : Write-in-latency events
* `MemRead`      : Memory read operations
* `MemWrite`     : Memory write operations
* `MemTotal`     : Total memory usage
* `drop_pct`(%)  : Packet drop percentage on the interface
* `CPU_busy`(%)  : CPU busy percentage
* `ksoft_avg`    : Average kernel softirq rate
* `ksoft_max`    : Maximum kernel softirq rate

The CSV output is saved with a filename indicating the fault scenario and bandwidth.

---

## ⚙️ Prerequisites

* **bash** shell (GNU Bash 4+ recommended)
* **iperf** (version 2) installed on both client and DUT
* SSH passwordless access configured from the test host to DUT
* The DUT’s NIC interface and IP address correctly set in `common.sh`

---

## 🚀 Usage

1. **Configure `common.sh`**

   * Update `SSH_DUT` to the DUT’s hostname or IP for SSH.
   * Set `SERVER_IP` to the DUT’s NIC IP.
   * Adjust `IFACE_STATS` to the network interface to monitor drops and stats.
   * Modify `BWS` array for desired `iperf` bandwidth targets.

2. **Make scripts executable**

   ```bash
   chmod +x *.sh
   ```

3. **Run the sweep**

   ```bash
   ./common.sh
   ```

   * Runs `iperf` client for 2500 seconds
   * For each bandwidth in `BWS`, it launches the corresponding metrics collection script for 300 seconds
   * Outputs CSV files in the current directory, named:
     `metrics_<scenario>_<bandwidth>.csv`

---

## 📂 Example Output

After completion, you will find CSV files such as:

```plain
metrics_CPU_interference_5G.csv
metrics_incast_7.5G.csv
metrics_memory_contention_10G.csv
```

Each CSV has a header row listing the metrics and one row per sampling interval.

---

## 🛠 Customization

* **Duration**

  * Modify `DUR` in `common.sh` to change the `iperf` test length.
  * Change the hard-coded `300` in the `common.sh` invocation to adjust metrics collection time.

* **Parallel Streams**
  Adjust `IPERF_PARALLEL` for more or fewer concurrent TCP streams.

* **Additional Metrics**
  Extend each `metrics_collection_*.sh` script to capture more kernel or hardware counters as needed.

---
