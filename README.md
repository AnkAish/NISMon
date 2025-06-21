# NISMon: Network and System Monitoring Framework

NISMon is a comprehensive framework for collecting, preprocessing, modeling, and evaluating system and network performance metrics under various fault scenarios. It provides modular scripts organized into four main components:

```
NISMon/
├── classifier_model_scripts/      # Train and save ML classifiers
├── metrics_collector/            # Collect and preprocess system metrics
├── evaluation_script/            # Evaluate trained models on test data
└── scripts/                      # Low-level system monitoring scripts
```

---

## 📋 Components Overview

### 1. Classifier Model Scripts (`classifier_model_scripts/`)

Train machine-learning models (Random Forest, SVM, MLP) on preprocessed metrics datasets.

* **Key files**: `random_forest_model.py`, `svm_model.py`, `mlp_model.py`
* **Purpose**: Load experimental data, train classifiers, and serialize models for inference.
* **Usage**: See `classifier_model_scripts/README.md`.

### 2. Metrics Collector (`metrics_collector/`)

Automate `iperf` traffic generation and sample system metrics under controlled faults.

* **Key files**: `common.sh`, `metrics_collection_with_*.sh`, `merge_and_label_CSV_files.py`
* **Purpose**: Sweep bandwidths, inject CPU/memory/incast or random faults, and generate labeled CSV datasets.
* **Usage**: See `metrics_collector/README.md`.

### 3. Evaluation Scripts (`evaluation_script/`)

Assess model performance on held-out test data and visualize results.

* **Key files**: `evaluation_NISMon_model.py`, `merge_and_label_CSV_files.py`, `dataset_testing.csv`
* **Purpose**: Compute confusion matrices, ROC/PR curves, and resource-latency summaries.
* **Sample Outputs**: `evaluation_result_RF/` folder contains example artifacts.
* **Usage**: See `evaluation_script/README.md`.

### 4. System Monitoring Scripts (`scripts/`)

Low-level probes for kernel softirq delays, CPU/memory usage, and link utilization.

* **Key files**: `ksoftirqd.bt`, `cpu_usage.sh`, `memory_usage.sh`, `link_utilization.sh`
* **Purpose**: Profile system internals at fine granularity for diagnostics or baseline measurement.
* **Usage**: See `scripts/README.md`.

---

## ⚙️ Global Prerequisites

* **Python 3.8+** with packages: `pandas`, `scikit-learn`, `joblib`, `matplotlib`, `glob2`
* **bash** shell (GNU Bash 4+) and **iperf2**
* **BPFtrace** (for `scripts/ksoftirqd.bt`)
* SSH passwordless access configured between host and DUT

Install Python dependencies once at the root:

```bash
pip install pandas scikit-learn joblib matplotlib glob2
```

---

## 🚀 Getting Started

1. **Collect Metrics** (in `metrics_collector/`):

   ```bash
   cd metrics_collector
   chmod +x *.sh
   ./common.sh
   python merge_and_label_CSV_files.py
   ```
2. **Train Models** (in `classifier_model_scripts/`):

   ```bash
   cd ../classifier_model_scripts
   python random_forest_model.py --input ../metrics_collector/merged_labeled_periodic_fault_data.csv
   # repeat for svm_model.py and mlp_model.py
   ```
3. **Evaluate Models** (in `evaluation_script/`):

   ```bash
   cd ../evaluation_script
   python merge_and_label_CSV_files.py
   python evaluation_NISMon_model.py --model-path ../classifier_model_scripts/random_forest_model.joblib --test-data dataset_testing.csv --results-dir evaluation_result_RF
   ```
4. **System Diagnostics** (in `scripts/`):

   ```bash
   cd ../scripts
   chmod +x *.sh ksoftirqd.bt
   sudo bpftrace ksoftirqd.bt
   ./cpu_usage.sh 1 > cpu.log
   ./memory_usage.sh 1 > mem.log
   ./link_utilization.sh eth0 1 > link.log
   ```

---

## 📄 License & Citation

NISMon is open source. Please cite this repository and any relevant publications when using these tools. Licensed under [MIT License](LICENSE).

---

Happy monitoring and modeling! 🚀
