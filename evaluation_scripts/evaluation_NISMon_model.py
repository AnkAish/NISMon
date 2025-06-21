#!/usr/bin/env python3
import pandas as pd
import numpy as np
import pickle
import time
import psutil, os, threading
from sklearn.metrics import (
    accuracy_score,
    precision_score, recall_score, f1_score,
    roc_auc_score, average_precision_score,
    confusion_matrix, roc_curve, precision_recall_curve
)
from sklearn.preprocessing import LabelBinarizer
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from pathlib import Path

# ─── 1) Paths & Parameters ───────────────────────────────────────────────────
TEST_CSV    = 'merged_labeled_Testdata_v3.csv'       # your CSV with string `label` column
PARENT      = Path.cwd().parent
MODEL_FILE  = PARENT / 'random_forest_model.pkl'
OUT_DIR     = Path('evaluation_results_RF')
OUT_DIR.mkdir(exist_ok=True)

# ─── 2) Load Data & Model ─────────────────────────────────────────────────────
df = pd.read_csv(TEST_CSV)
X_test = df.drop(columns=['label'])
y_true = df['label'].astype(str)

with open(MODEL_FILE, 'rb') as f:
    model = pickle.load(f)

# ─── 3) Measure Inference Latency ─────────────────────────────────────────────
_ = model.predict(X_test.iloc[:10])  # warm-up
start = time.perf_counter()
y_pred = model.predict(X_test)
latency_s = time.perf_counter() - start
n_samples = len(X_test)
ms_per_sample = latency_s / n_samples * 1e3

# ─── 4) Profile CPU & Memory During Inference ────────────────────────────────
proc = psutil.Process(os.getpid())
mem_before = proc.memory_info().rss / (1024**2)  # MiB

cpu_samples = []
stop_flag = False
def sample_cpu(interval=0.01):
    cpu_samples.append(proc.cpu_percent(interval=interval))

def cpu_sampler():
    while not stop_flag:
        sample_cpu()

t = threading.Thread(target=cpu_sampler)
t.start()
_ = model.predict(X_test)  # profile run
stop_flag = True
t.join()
mem_after = proc.memory_info().rss / (1024**2)

# ─── 5) Compute Classification Metrics ────────────────────────────────────────
labels = sorted(y_true.unique())  # e.g. ['cpu_interference','incast','memory_contention','normal']
metrics = {
    'accuracy': accuracy_score(y_true, y_pred),
    'precision_macro': precision_score(y_true, y_pred, average='macro', zero_division=0),
    'recall_macro':    recall_score(y_true, y_pred, average='macro', zero_division=0),
    'f1_macro':        f1_score(y_true, y_pred, average='macro', zero_division=0)
}

# ROC/PR AUC per class if proba available
if hasattr(model, 'predict_proba'):
    y_proba = model.predict_proba(X_test)
    lb = LabelBinarizer().fit(y_true)
    y_onehot = lb.transform(y_true)
    for i, cls in enumerate(lb.classes_):
        metrics[f'roc_auc_{cls}'] = roc_auc_score(y_onehot[:, i], y_proba[:, i])
        metrics[f'ap_{cls}']      = average_precision_score(y_onehot[:, i], y_proba[:, i])

# ─── 6) Save Confusion Matrix & Metrics ─────────────────────────────────────
cm = confusion_matrix(y_true, y_pred, labels=labels)
cm_df = pd.DataFrame(cm, index=[f'true_{l}' for l in labels],
                     columns=[f'pred_{l}' for l in labels])
cm_df.to_csv(OUT_DIR / 'confusion_matrix.csv')
pd.Series(metrics).to_csv(OUT_DIR / 'metrics_summary.csv', header=['value'])

# ─── 7) Save Latency & Resource Usage ────────────────────────────────────────
with open(OUT_DIR / 'latency_resources.txt', 'w') as f:
    f.write(f"Total inference time: {latency_s:.4f} s for {n_samples} samples\n")
    f.write(f"Avg latency/sample:   {ms_per_sample:.3f} ms\n")
    f.write(f"Memory before:        {mem_before:.1f} MiB\n")
    f.write(f"Memory after:         {mem_after:.1f} MiB\n")
    f.write(f"Peak mem overhead:    {mem_after - mem_before:.1f} MiB\n")
    f.write("CPU% during inference (min/avg/max): "
            f"{min(cpu_samples):.1f}/{sum(cpu_samples)/len(cpu_samples):.1f}/{max(cpu_samples):.1f}\n")

# ─── 8) Plot & Save Figures ─────────────────────────────────────────────────
# 8a) Improved Confusion Matrix Plot with legend at top center
short_labels = ['C', 'I', 'M', 'N']  # Corresponds to ['cpu_interference','incast','memory_contention','normal']

plt.figure(figsize=(12, 10))
plt.imshow(cm, interpolation='nearest', cmap=plt.cm.Blues)
cbar = plt.colorbar()
cbar.ax.tick_params(labelsize=20, width=0)   # tick label size=20
for t in cbar.ax.get_yticklabels():
    t.set_fontweight('bold')

# Set the one‐letter ticks with bold, larger font
plt.xticks(
    range(len(labels)),
    short_labels,
    fontsize=28,
    fontweight='bold'
)
plt.yticks(
    range(len(labels)),
    short_labels,
    fontsize=28,
    fontweight='bold'
)

# Annotate counts inside each cell
for i in range(len(labels)):
    for j in range(len(labels)):
        plt.text(
            j,
            i,
            cm[i, j],
            ha='center',
            va='center',
            color='white' if cm[i, j] > cm.max() / 2 else 'black',
            fontsize=28,
            fontweight='bold'
        )

# Build legend handles showing full names for each short label
handles = []
full_names = labels  # ['cpu_interference','incast','memory_contention','normal']
for short, full in zip(short_labels, full_names):
    handles.append(
        Line2D([], [], linestyle='', marker='', label=f"{short}: {full}")
    )

# Shrink the axes from the top to make room for the legend
plt.tight_layout()
plt.subplots_adjust(top=0.80)  # leave 20% of figure height above axes

# Place the legend in the freed‐up space above the heatmap
plt.legend(
    handles=handles,
    loc='upper center',
    bbox_to_anchor=(0.5, 1.16),
    ncol=2,
    borderaxespad=0.0,
    prop={'size': 24, 'weight': 'bold'}
)

plt.savefig(OUT_DIR / 'confusion_matrix.png', bbox_inches='tight')
plt.close()


# 8b) Combined ROC & PR curves for all classes
if hasattr(model, 'predict_proba'):
    # Combined ROC‐curve figure
    plt.figure(figsize=(8, 6))
    for i, cls in enumerate(lb.classes_):
        fpr, tpr, _ = roc_curve(y_onehot[:, i], y_proba[:, i])
        auc_score = metrics[f'roc_auc_{cls}']
        plt.plot(fpr, tpr, lw=2, label=f"{cls}")

    plt.plot([0, 1], [0, 1], linestyle='--', color='gray', lw=1)
    plt.xlabel("False Positive Rate (FPR)", fontsize=22, fontweight='bold')
    plt.ylabel("True Positive Rate (TPR)", fontsize=22, fontweight='bold')
    plt.xticks(fontsize=20, fontweight='bold')
    plt.yticks(fontsize=20, fontweight='bold')
    plt.legend(loc='lower right', prop={'size': 16, 'weight': 'bold'})
    plt.tight_layout()
    plt.savefig(OUT_DIR / 'roc_all_classes.png')
    plt.close()

    # Combined Precision‐Recall figure
    plt.figure(figsize=(8, 6))
    for i, cls in enumerate(lb.classes_):
        prec, rec, _ = precision_recall_curve(y_onehot[:, i], y_proba[:, i])
        ap_score = metrics[f'ap_{cls}']
        plt.step(rec, prec, where='post', lw=2, label=f"{cls}")

    plt.xlabel("Recall", fontsize=22, fontweight='bold')
    plt.ylabel("Precision", fontsize=22, fontweight='bold')
    plt.xticks(fontsize=20, fontweight='bold')
    plt.yticks(fontsize=20, fontweight='bold')
    plt.legend(loc='center right', prop={'size': 14, 'weight': 'bold'})
    plt.tight_layout()
    plt.savefig(OUT_DIR / 'pr_all_classes.png')
    plt.close()

print(f"✅ All evaluation outputs written to {OUT_DIR}/")
