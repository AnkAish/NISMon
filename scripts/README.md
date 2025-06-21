# System Monitoring & Analysis Scripts

This folder contains scripts for profiling system performance metrics, including kernel softirq thread delays, CPU usage, memory usage, and network link utilization.

---

## 📁 Directory Structure

```plain
scripts/
├── ksoftirqd.bt
├── cpu_usage.sh
├── memory_usage.sh
└── link_utilization.sh
```

* **ksoftirqd.bt**

  * A [BPFtrace](https://github.com/iovisor/bpftrace) script that measures the `ksoftirqd` thread’s latency on each CPU. Outputs average and maximum delay per sampling interval.
* **cpu\_usage.sh**

  * Collects and logs overall CPU utilization percentage across all cores.
* **memory\_usage.sh**

  * Samples and logs system memory usage statistics (used, free, cached, etc.).
* **link\_utilization.sh**

  * Monitors and logs network interface transmit/receive byte rates and computes link utilization percentage.

---

## ⚙️ Prerequisites

* **bash** shell (GNU Bash 4+ recommended)
* **BPFtrace** installed for `ksoftirqd.bt`
* **sudo** privileges (required by `ksoftirqd.bt` to attach to kernel probes)

---

## 🚀 Usage

1. **Make scripts executable**

   ```bash
   chmod +x *.sh ksoftirqd.bt
   ```

2. **Run CPU usage monitor**

   ```bash
   ./cpu_usage.sh [interval]
   ```

   * `interval` (seconds) between samples. Default: 1s.

3. **Run Memory usage monitor**

   ```bash
   ./memory_usage.sh [interval]
   ```

   * `interval` (seconds) between samples. Default: 1s.

4. **Run Link utilization monitor**

   ```bash
   ./link_utilization.sh <interface> [interval]
   ```

   * `<interface>`: Network interface to monitor (e.g., `eth0`).
   * `interval` (seconds) between samples. Default: 1s.

5. **Run ksoftirqd delay tracer**

   ```bash
   sudo bpftrace ksoftirqd.bt
   ```

   * Outputs a running report of average and maximum `ksoftirqd` thread delays per CPU.

---

## 📂 Output

Each script writes to `stdout` by default. Redirect to a file to persist logs:

```bash
./cpu_usage.sh 2 > cpu_usage.log
./memory_usage.sh 2 > memory_usage.log
./link_utilization.sh eth0 2 > link_util.log
sudo bpftrace ksoftirqd.bt > ksoftirqd_delay.log
```

The CSV or whitespace-delimited logs can be parsed for further analysis or plotting.

---

## 🛠 Customization

* **Sampling Interval**: Adjust the sampling interval argument for `.sh` scripts to tune granularity.
* **Interface Selection**: Change the default interface name in `link_utilization.sh` if needed.
* **BPFtrace Probes**: Extend `ksoftirqd.bt` to capture additional latency distributions or histograms.

---
