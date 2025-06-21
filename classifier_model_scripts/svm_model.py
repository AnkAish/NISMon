#!/usr/bin/env python3
import pandas as pd
import pickle
from sklearn.svm import SVC
from sklearn.model_selection import train_test_split, GridSearchCV, StratifiedKFold
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline

# ─── 1) Load Data ─────────────────────────────────────────────────────────────
df = pd.read_csv('./normal/merged_labeled_Faultdata_v1.csv')
X = df.drop(columns=['label'])
y = df['label']

# ─── 2) Train/Test Split ──────────────────────────────────────────────────────
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, stratify=y, random_state=42
)

# ─── 3) Set Up Scaled SVM Pipeline + Grid ─────────────────────────────────────
pipeline = Pipeline([
    ('scaler', StandardScaler()),
    ('svc', SVC(probability=True, random_state=42))
])

param_grid = {
    'svc__C': [1, 10],                  # Reduced for speed
    'svc__kernel': ['rbf', 'poly'],
    'svc__degree': [2],                # Used only for 'poly'
    'svc__gamma': ['scale']            # Use 'scale' (recommended over 'auto')
}

cv = StratifiedKFold(n_splits=3, shuffle=True, random_state=42)

grid_search = GridSearchCV(
    estimator=pipeline,
    param_grid=param_grid,
    scoring='roc_auc_ovr',
    cv=cv,
    n_jobs=-1,
    verbose=2
)

# ─── 4) Run Grid Search ───────────────────────────────────────────────────────
print("Starting hyperparameter search for SVM...")
grid_search.fit(X_train, y_train)

best_model = grid_search.best_estimator_
print("\nBest parameters found:")
print(grid_search.best_params_)
print(f"Best training CV score: {grid_search.best_score_:.4f}")

# ─── 5) Evaluate on Test Set ──────────────────────────────────────────────────
y_pred = best_model.predict(X_test)
y_proba = best_model.predict_proba(X_test)

print("\nConfusion Matrix (test set):")
print(confusion_matrix(y_test, y_pred))

print("\nClassification Report (test set):")
print(classification_report(y_test, y_pred, digits=4))

# ─── 6) Save the Best Model ───────────────────────────────────────────────────
with open('svm_model.pkl', 'wb') as f_out:
    pickle.dump(best_model, f_out, protocol=pickle.HIGHEST_PROTOCOL)

print("\nSaved best SVM model to 'svm_model.pkl'")
