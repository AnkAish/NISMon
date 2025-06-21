# Metrics Collection & Preprocessing Scripts

This folder contains shell scripts to collect system metrics under various fault injection scenarios during background `iperf` traffic, plus a Python preprocessing script to merge and label the resulting CSVs.

---

## 📁 Repository Structure

```plain
metrics_collector/
├── common.sh
├── metrics_collection_with_CPU_interference.sh
├── metrics_collection_with_incast.sh
├── metrics_collection_with_memory_contention.sh
├── metrics_collection_with_random_faults.sh
├── merge_and_label_CSV_files.py
└── merged_labeled_periodic_fault_data.csv
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
* **merge\_and\_label\_CSV\_files.py**

  * Preprocesses, concatenates, and labels all generated CSVs into a single DataFrame.
* **merged\_labeled\_periodic\_fault\_data.csv**

  * Example output from running the Python preprocessing script.

---

## 📝 Overview

1. **Data Collection**: Shell scripts (`metrics_collection_*.sh`) connect to the DUT via SSH and sample these metrics at regular intervals:

   * `PCIRdCur`      : PCIe read current count
   * `ItoM`          : In-to-memory transactions
   * `ItoMCacheNear` : Near-cache memory transactions
   * `WiL`           : Write-in-latency events
   * `MemRead`       : Memory read operations
   * `MemWrite`      : Memory write operations
   * `MemTotal`      : Total memory usage
   * `drop_pct` (%)  : Packet drop percentage on the interface
   * `CPU_busy` (%)  : CPU busy percentage
   * `ksoft_avg`     : Average kernel softirq rate
   * `ksoft_max`     : Maximum kernel softirq rate

   CSV files are named `metrics_<scenario>_<bandwidth>.csv`.

2. **Data Preprocessing**: The Python script `merge_and_label_CSV_files.py`:

   * Reads all `metrics_*.csv` files in the directory.
   * Concatenates them into a single DataFrame.
   * Adds a `scenario` and `bandwidth` label extracted from filenames.
   * Outputs `merged_labeled_periodic_fault_data.csv` for downstream analysis.

---

## ⚙️ Prerequisites

* **bash** shell (GNU Bash 4+ recommended)
* **iperf** version 2 on both host and DUT
* SSH passwordless access from host to DUT
* **Python 3.8+** with the following packages:

  ```bash
  pip install pandas glob2
  ```

---

## 🚀 Usage

### 1. Collect Metrics

1. **Configure `common.sh`**

   ```bash
   SSH_DUT=netx4              # DUT hostname or IP
   SERVER_IP=30.0.0.2         # DUT NIC IP
   IFACE_STATS=ens802np1np1   # Interface to monitor
   BWS=(2.5G 3.75G 5G 6.25G 7.5G 8.75G 10G)
   DUR=2500                   # background traffic duration (s)
   METRIC_DUR=300             # metrics collection duration (s)
   ```
2. **Make scripts executable**

   ```bash
   chmod +x *.sh
   ```
3. **Run standard sweep**

   ```bash
   ./common.sh
   ```

### 2. Run with Random Faults

Modify in `common.sh`:

```bash
DUR=5000
METRIC_DUR=600
```

Replace invocation line:

```bash
./metrics_collection_with_random_faults.sh "$SSH_DUT" "$BW" $METRIC_DUR "$IFACE_STATS" &
```

Then:

```bash
./common.sh
```

### 3. Preprocess & Merge

```bash
python merge_and_label_CSV_files.py
```

* Scans for `metrics_*.csv` in the current folder.
* Generates `merged_labeled_periodic_fault_data.csv`.

---

## 📂 Example Outputs

```plain
metrics_CPU_interference_5G.csv
metrics_incast_7.5G.csv
metrics_memory_contention_10G.csv
metrics_random_faults_7.5G.csv
merged_labeled_periodic_fault_data.csv
```

* **`merged_labeled_periodic_fault_data.csv`** contains all sampled metrics with added `scenario` and `bandwidth` columns for easy filtering.

---

## 🛠 Customization

* Change `DUR` and `METRIC_DUR` in `common.sh` for traffic and collection durations.
* Add or remove bandwidth targets in the `BWS` array.
* Extend `metrics_collection_*.sh` scripts to capture additional counters.
* Modify `merge_and_label_CSV_files.py` to adjust labeling logic or include new file patterns.

---
