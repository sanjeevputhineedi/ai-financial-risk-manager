"""
Checkpoint R3 — Baseline Payee Risk Model
===========================================
A lightweight, explainable baseline: RandomForestClassifier over the
R2 feature vector. Random Forest was chosen over XGBoost because no
extra dependency is justified for a prototype of this size, and it
gives free feature_importances_ for explainability (R8).

Output contract (matches R9 API contract downstream):
    payee_risk_score : float 0-100   (NOT "proof of scam" — a probability-derived score)
    risk_level        : LOW | MEDIUM | HIGH | CRITICAL
    confidence        : float 0-1     (how far the model's probability is from the decision boundary)
    model_version     : str
"""

from __future__ import annotations
import json
import pickle
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

from ml.payee_risk.features import FEATURE_ORDER, build_feature_vector, vectorize

MODEL_VERSION = "payee-v1"

RISK_LEVEL_THRESHOLDS = [
    (85, "CRITICAL"),
    (65, "HIGH"),
    (35, "MEDIUM"),
    (0, "LOW"),
]


def score_to_level(score: float) -> str:
    for threshold, level in RISK_LEVEL_THRESHOLDS:
        if score >= threshold:
            return level
    return "LOW"


class BaselinePayeeRiskModel:
    def __init__(self):
        self.clf: RandomForestClassifier | None = None
        self.version = MODEL_VERSION
        self.feature_order = FEATURE_ORDER

    def fit(self, df: pd.DataFrame, label_col: str = "label_fraud_like", seed: int = 42):
        X = np.vstack([
            vectorize(build_feature_vector(row.to_dict()), normalize=True)
            for _, row in df.iterrows()
        ])
        y = df[label_col].values

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=seed, stratify=y
        )

        self.clf = RandomForestClassifier(
            n_estimators=200,
            max_depth=8,
            min_samples_leaf=5,
            class_weight="balanced",   # fraud is the rare class
            random_state=seed,
        )
        self.clf.fit(X_train, y_train)
        return X_train, X_test, y_train, y_test

    def predict_raw(self, feature_vec: np.ndarray) -> float:
        """Return raw fraud probability (0-1)."""
        if self.clf is None:
            raise RuntimeError("Model not trained/loaded.")
        return float(self.clf.predict_proba(feature_vec.reshape(1, -1))[0, 1])

    def predict(self, record: dict, graph_features: dict | None = None) -> dict:
        feats = build_feature_vector(record, graph_features=graph_features)
        vec = vectorize(feats, normalize=True)
        prob = self.predict_raw(vec)

        score = round(prob * 100, 2)
        level = score_to_level(score)
        confidence = round(abs(prob - 0.5) * 2, 3)  # 0 at boundary, 1 at extremes

        return {
            "payee_risk_score": score,
            "risk_level": level,
            "confidence": confidence,
            "model_version": self.version,
            "_raw_features": feats,   # kept for explainability (R8); strip before external API
        }

    def feature_importances(self) -> dict:
        if self.clf is None:
            raise RuntimeError("Model not trained/loaded.")
        return dict(sorted(
            zip(self.feature_order, self.clf.feature_importances_),
            key=lambda kv: -kv[1]
        ))

    def save(self, path: str):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, "wb") as f:
            pickle.dump(self, f)
        meta = {
            "model_version": self.version,
            "feature_order": self.feature_order,
            "model_type": "RandomForestClassifier",
        }
        with open(str(Path(path).with_suffix(".meta.json")), "w") as f:
            json.dump(meta, f, indent=2)

    @staticmethod
    def load(path: str) -> "BaselinePayeeRiskModel":
        with open(path, "rb") as f:
            return pickle.load(f)


def train_and_save(dataset_path: str, model_out: str, seed: int = 42):
    df = pd.read_csv(dataset_path)
    model = BaselinePayeeRiskModel()
    X_train, X_test, y_train, y_test = model.fit(df, seed=seed)
    model.save(model_out)
    return model, (X_train, X_test, y_train, y_test)


if __name__ == "__main__":
    model, splits = train_and_save(
        "data/fraud/synthetic_payees.csv",
        "models/payee_risk_model.pkl",
    )
    print("Model trained and saved. Version:", model.version)
    print("\nTop feature importances:")
    for name, imp in list(model.feature_importances().items())[:8]:
        print(f"  {name:35s} {imp:.4f}")
