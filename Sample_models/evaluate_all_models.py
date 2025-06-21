#!/usr/bin/env python3
import pandas as pd
import numpy as np
import pickle
import time
import psutil, os, threading
from pathlib import Path
from sklearn.metrics import (
    accuracy_score,
    precision_score, recall_score, f1_score,
    roc_auc_score, average_precision_score,
    confusion_matrix
)
from sklearn.preprocessing import LabelBinarizer

# ─── CONFIG ────────────────────────────────────────────────────────────────────
TEST_CSV      = './normal/merged_labeled_Faultdata_v1.csv'
MODELS_DIR    = Path('.')            # put model_v3.pkl, svm_model_v1.pkl, mlp_model_v1.pkl, etc. here
OUT_DIR       = Path('models_comparison')
OUT_DIR.mkdir(exist_ok=True)

# ─── LOAD TEST SET ─────────────────────────────────────────────────────────────
df        = pd.read_csv(TEST_CSV)
X_test    = df.drop(columns=['label'])
y_true    = df['label'].astype(str)
labels    = sorted(y_true.unique())

# Prepare one-hot for ROC/PR
lb        = LabelBinarizer().fit(y_true)
y_onehot  = lb.transform(y_true)

# ─── EVALUATE ONE MODEL ───────────────────────────────────────────────────────
def evaluate_model(model_path):
    name = model_path.stem
    print(f"\n▶ Evaluating {name} …")

    # Load
    with open(model_path, 'rb') as f:
        model = pickle.load(f)

    # Warm-up
    _ = model.predict(X_test.iloc[:10])

    # Measure latency
    start = time.perf_counter()
    y_pred = model.predict(X_test)
    latency_s = time.perf_counter() - start
    ms_per_sample = latency_s / len(X_test) * 1e3

    # Profile CPU & memory
    proc = psutil.Process(os.getpid())
    mem_before = proc.memory_info().rss / (1024**2)
    cpu_samples = []
    stop_flag = False

    def sampler():
        while not stop_flag:
            cpu_samples.append(proc.cpu_percent(interval=0.01))

    t = threading.Thread(target=sampler)
    t.start()
    _ = model.predict(X_test)
    stop_flag = True
    t.join()
    mem_after = proc.memory_info().rss / (1024**2)

    # Basic metrics
    metrics = {
        'model': name,
        'accuracy':       accuracy_score(y_true, y_pred),
        'precision_macro': precision_score(y_true, y_pred, average='macro', zero_division=0),
        'recall_macro':    recall_score(y_true, y_pred, average='macro', zero_division=0),
        'f1_macro':        f1_score(y_true, y_pred, average='macro', zero_division=0),
        'latency_ms':      ms_per_sample,
        'mem_overhead_MiB': mem_after - mem_before,
        'cpu_avg_pct':     np.mean(cpu_samples)
    }

    # Per-class ROC-AUC & AP
    if hasattr(model, 'predict_proba'):
        y_proba = model.predict_proba(X_test)
        for i, cls in enumerate(lb.classes_):
            metrics[f'roc_auc_{cls}'] = roc_auc_score(y_onehot[:, i], y_proba[:, i])
            metrics[f'ap_{cls}']      = average_precision_score(y_onehot[:, i], y_proba[:, i])

    # Save per-model confusion matrix
    cm = confusion_matrix(y_true, y_pred, labels=labels)
    cm_df = pd.DataFrame(cm,
                         index=[f'true_{l}' for l in labels],
                         columns=[f'pred_{l}' for l in labels])
    cm_df.to_csv(OUT_DIR / f'{name}_confusion_matrix.csv')

    return metrics

# ─── MAIN LOOP ─────────────────────────────────────────────────────────────────
all_metrics = []
for model_file in MODELS_DIR.glob('*.pkl'):
    all_metrics.append(evaluate_model(model_file))

# ─── AGGREGATE & SAVE TRADE-OFF TABLE ──────────────────────────────────────────
metrics_df = pd.DataFrame(all_metrics)
metrics_df.to_csv(OUT_DIR / 'tradeoff_metrics_summary.csv', index=False)
print(f"\n✅ Finished. Summary table saved to {OUT_DIR / 'tradeoff_metrics_summary.csv'}")
