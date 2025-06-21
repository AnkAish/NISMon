#!/usr/bin/env python3
import pandas as pd
import pickle
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier
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
# Assumes 'final_data.csv' has feature columns plus a 'label' column
df = pd.read_csv('./normal/merged_labeled_Faultdata_v1.csv')
X = df.drop(columns=['label'])
y = df['label']

# ─── 2) Train/Test Split ──────────────────────────────────────────────────────
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, stratify=y, random_state=42
)

# ─── 3) Set Up Random Forest + Hyperparameter Grid ───────────────────────────
base_rf = RandomForestClassifier(
    random_state=42,
    n_jobs=-1
)

param_grid = {
    'n_estimators': [50, 100, 200],
    'max_depth': [None, 10, 20, 30],
    'max_features': ['sqrt', 'log2'],
    'min_samples_split': [2, 5, 10],
    'min_samples_leaf': [1, 2, 4]
}

cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

grid_search = GridSearchCV(
    estimator=base_rf,
    param_grid=param_grid,
    scoring='roc_auc_ovr',   # you can switch to 'accuracy' or 'roc_auc_ovr'
    cv=cv,
    n_jobs=-1,
    verbose=2
)

# ─── 4) Run Grid Search on Training Data ──────────────────────────────────────
print("Starting hyperparameter search...")
grid_search.fit(X_train, y_train)

best_params = grid_search.best_params_
best_score  = grid_search.best_score_

print("\nBest hyperparameters found:")
for param, val in best_params.items():
    print(f"  • {param}: {val}")
print(f"\nBest cross-validated F1-macro (training): {best_score:.4f}\n")

# Retrieve the best estimator
best_rf = grid_search.best_estimator_

# ─── 5) Evaluate on Test Set ──────────────────────────────────────────────────
y_pred = best_rf.predict(X_test)

print("Confusion Matrix (test set):")
print(confusion_matrix(y_test, y_pred))

print("\nClassification Report (test set):")
print(classification_report(y_test, y_pred, digits=4))

# ─── 6) Save the Best Model ───────────────────────────────────────────────────
with open('random_forest_model.pkl', 'wb') as f_out:
    pickle.dump(best_rf, f_out, protocol=pickle.HIGHEST_PROTOCOL)

print("\nSaved best model to 'random_forest_model.pkl'")
