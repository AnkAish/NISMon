#!/usr/bin/env python3
import pandas as pd
import pickle
from pathlib import Path
from sklearn.neural_network import MLPClassifier
from sklearn.model_selection import (
    train_test_split,
    GridSearchCV,
    StratifiedKFold
)
from sklearn.metrics import (
    classification_report,
    confusion_matrix
)

# ─── 1) Load Data ─────────────────────────────────────────────────────────────
df = pd.read_csv('./normal/merged_labeled_Faultdata_v1.csv')
X = df.drop(columns=['label'])
y = df['label']

# ─── 2) Train/Test Split ──────────────────────────────────────────────────────
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, stratify=y, random_state=42
)

# ─── 3) Set Up MLP + Hyperparameter Grid ──────────────────────────────────────
base_mlp = MLPClassifier(
    random_state=42,
    max_iter=200
)

param_grid = {
    'hidden_layer_sizes': [(20,), (30,), (30, 20), (30, 30)],
    'activation': ['tanh', 'relu'],
    'solver': ['adam', 'sgd'],
    'alpha': [0.001, 0.01],
    'learning_rate_init': [0.005, 0.01]
}

cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

grid_search = GridSearchCV(
    estimator=base_mlp,
    param_grid=param_grid,
    scoring='roc_auc_ovr',   # or 'f1_macro', 'roc_auc_ovr'
    cv=cv,
    n_jobs=-1,
    verbose=2
)

# ─── 4) Run Grid Search on Training Data ──────────────────────────────────────
print("Starting hyperparameter search for MLPClassifier...")
grid_search.fit(X_train, y_train)

best_params = grid_search.best_params_
best_score  = grid_search.best_score_

print("\nBest hyperparameters for MLP found:")
for param, val in best_params.items():
    print(f"  • {param}: {val}")
print(f"\nBest cross-validated score (training): {best_score:.4f}\n")

# Retrieve the best estimator
best_mlp = grid_search.best_estimator_

# ─── 5) Evaluate on Test Set ──────────────────────────────────────────────────
y_pred = best_mlp.predict(X_test)

print("Confusion Matrix (test set):")
print(confusion_matrix(y_test, y_pred))

print("\nClassification Report (test set):")
print(classification_report(y_test, y_pred, digits=4))

# ─── 6) Save the Best Model ───────────────────────────────────────────────────
with open('mlp_model.pkl', 'wb') as f_out:
    pickle.dump(best_mlp, f_out, protocol=pickle.HIGHEST_PROTOCOL)

print("\nSaved best MLP model to 'mlp_model.pkl'")
