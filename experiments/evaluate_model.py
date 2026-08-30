"""
Checkpoint R10 — Fraud Model Evaluation
==========================================
Reproducible evaluation of the baseline payee risk model. Because
fraud is heavily imbalanced (~15% in our synthetic set), we report
precision/recall/F1/PR-AUC alongside accuracy rather than relying on
accuracy alone (a trivial "always predict legit" model would score
~85% accuracy while being useless).
"""

from __future__ import annotations
import json
import pandas as pd
import numpy as np
from sklearn.metrics import (
    precision_score, recall_score, f1_score, roc_auc_score,
    average_precision_score, confusion_matrix
)

from ml.payee_risk.model import BaselinePayeeRiskModel


def evaluate(dataset_path: str = "data/fraud/synthetic_payees.csv",
             model_path: str = "models/payee_risk_model.pkl",
             seed: int = 42,
             out_path: str = "experiments/evaluation_results.json") -> dict:
    df = pd.read_csv(dataset_path)
    model = BaselinePayeeRiskModel()
    X_train, X_test, y_train, y_test = model.fit(df, seed=seed)  # retrain on same split for reproducibility
    model.save(model_path)

    y_prob = model.clf.predict_proba(X_test)[:, 1]
    y_pred = (y_prob >= 0.5).astype(int)

    tn, fp, fn, tp = confusion_matrix(y_test, y_pred).ravel()
    false_positive_rate = fp / (fp + tn) if (fp + tn) else 0.0

    results = {
        "n_test": int(len(y_test)),
        "precision": round(float(precision_score(y_test, y_pred)), 4),
        "recall": round(float(recall_score(y_test, y_pred)), 4),
        "f1": round(float(f1_score(y_test, y_pred)), 4),
        "roc_auc": round(float(roc_auc_score(y_test, y_prob)), 4),
        "pr_auc": round(float(average_precision_score(y_test, y_prob)), 4),
        "false_positive_rate": round(float(false_positive_rate), 4),
        "confusion_matrix": {
            "true_negative": int(tn), "false_positive": int(fp),
            "false_negative": int(fn), "true_positive": int(tp),
        },
        "model_version": model.version,
        "seed": seed,
    }

    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)

    return results


if __name__ == "__main__":
    results = evaluate()
    print(json.dumps(results, indent=2))
