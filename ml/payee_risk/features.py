"""
Checkpoint R2 — Feature Engineering
====================================
Converts a raw payee record (as it would arrive from Murali's database)
into a deterministic, documented, normalized feature vector consumed by
the baseline model (R3) and the graph/reputation integration (R7).

No data leakage: every feature here is knowable *before* the outcome
(fraud/not-fraud) is known — none of them are derived from the label.

Feature groups
--------------
1. Direct behavioral features   -> come straight off the payee record
2. Temporal features            -> derived from account_age / recency
3. Rolling features             -> computed from a transaction time
                                    series when one is available
                                    (falls back to static approximation
                                    when only aggregate counts exist)
4. Graph-derived placeholders   -> filled in by ml/graph/graph_features.py;
                                    default to neutral values so this
                                    module can run standalone
"""

from __future__ import annotations
from dataclasses import dataclass, field
import numpy as np

# The exact, ordered list of features the model is trained on.
# Order matters: this list IS the model's input contract.
FEATURE_ORDER = [
    "account_age",
    "transaction_count",
    "incoming_volume",
    "outgoing_volume",
    "transaction_velocity",
    "unique_senders",
    "complaint_count",
    "complaint_rate",
    "successful_transaction_ratio",
    "refund_ratio",
    "suspicious_counterparty_count",
    "transaction_concentration",
    "incoming_outgoing_ratio",
    # temporal
    "account_age_log",
    "is_new_account",
    # rolling (recent-window) features
    "recent_transaction_ratio_7d",
    "recent_complaint_ratio_30d",
    # graph-derived placeholders (see ml/graph/graph_features.py)
    "graph_unique_counterparties",
    "graph_suspicious_neighbor_ratio",
    "graph_cluster_risk_indicator",
]

FEATURE_DOCS = {
    "account_age": "Days since the recipient account was created.",
    "transaction_count": "Total number of transactions ever received.",
    "incoming_volume": "Total amount received (currency units, simulated).",
    "outgoing_volume": "Total amount sent onward by this recipient.",
    "transaction_velocity": "transaction_count / account_age_days — how fast the account transacts relative to its age.",
    "unique_senders": "Count of distinct senders who have paid this recipient.",
    "complaint_count": "Number of fraud/dispute reports filed against this recipient.",
    "complaint_rate": "complaint_count / transaction_count — complaints normalized by activity.",
    "successful_transaction_ratio": "Fraction of transactions that completed without dispute or refund.",
    "refund_ratio": "Fraction of transaction volume that was refunded.",
    "suspicious_counterparty_count": "Count of counterparties that are themselves flagged as suspicious.",
    "transaction_concentration": "How concentrated incoming funds are among few senders (0=diffuse, 1=concentrated).",
    "incoming_outgoing_ratio": "incoming_volume / outgoing_volume — near 1 for pass-through ('mule') behavior.",
    "account_age_log": "log1p(account_age) — dampens the effect of very old accounts.",
    "is_new_account": "Binary flag: account_age < 30 days.",
    "recent_transaction_ratio_7d": "Share of all transactions that occurred in the last 7 days (activity burst signal).",
    "recent_complaint_ratio_30d": "Share of all complaints filed in the last 30 days (evidence recency).",
    "graph_unique_counterparties": "From transaction graph: distinct direct neighbors. Default 0 if graph unavailable.",
    "graph_suspicious_neighbor_ratio": "From transaction graph: fraction of neighbors flagged suspicious. Default 0.",
    "graph_cluster_risk_indicator": "From transaction graph: normalized risk of the connected component. Default 0.",
}

# Normalization bounds, derived empirically from the synthetic dataset
# (see data/fraud/generate_dataset.py). Used for min-max scaling so the
# model receives features on comparable scales. Values are intentionally
# generous (not tight to the training set) so unseen payees don't clip badly.
NORM_BOUNDS = {
    "account_age": (0, 3650),
    "transaction_count": (0, 20000),
    "incoming_volume": (0, 500000),
    "outgoing_volume": (0, 500000),
    "transaction_velocity": (0, 50),
    "unique_senders": (0, 5000),
    "complaint_count": (0, 50),
    "complaint_rate": (0, 1),
    "successful_transaction_ratio": (0, 1),
    "refund_ratio": (0, 1),
    "suspicious_counterparty_count": (0, 30),
    "transaction_concentration": (0, 1),
    "incoming_outgoing_ratio": (0, 20),
    "account_age_log": (0, np.log1p(3650)),
    "is_new_account": (0, 1),
    "recent_transaction_ratio_7d": (0, 1),
    "recent_complaint_ratio_30d": (0, 1),
    "graph_unique_counterparties": (0, 5000),
    "graph_suspicious_neighbor_ratio": (0, 1),
    "graph_cluster_risk_indicator": (0, 1),
}


def _minmax(value: float, bounds: tuple[float, float]) -> float:
    lo, hi = bounds
    if hi <= lo:
        return 0.0
    return float(np.clip((value - lo) / (hi - lo), 0.0, 1.0))


def build_feature_vector(record: dict, graph_features: dict | None = None,
                          transaction_timestamps: list | None = None,
                          complaint_timestamps: list | None = None,
                          now_day: int | None = None) -> dict:
    """
    Convert one payee record into the full documented feature set.

    record: dict with at least the direct features from the synthetic
            dataset / DB row (account_age, transaction_count, ... etc.)
    graph_features: optional dict from ml/graph/graph_features.py with keys
            unique_counterparties, suspicious_neighbor_ratio, cluster_risk_indicator
    transaction_timestamps / complaint_timestamps: optional lists of day-offsets
            (ints) used to compute rolling/recency features when a real
            transaction stream is available. If absent, we fall back to a
            deterministic static approximation so the function never fails.
    now_day: the "current" day index for recency computation (defaults to account_age,
            i.e. "today").
    """
    account_age = int(record["account_age"])
    now_day = now_day if now_day is not None else account_age

    raw = {k: float(record.get(k, 0.0)) for k in FEATURE_ORDER if k in record}

    # --- temporal features ---
    raw["account_age_log"] = float(np.log1p(account_age))
    raw["is_new_account"] = 1.0 if account_age < 30 else 0.0

    # --- rolling features ---
    if transaction_timestamps:
        recent = sum(1 for t in transaction_timestamps if now_day - t <= 7)
        raw["recent_transaction_ratio_7d"] = recent / max(len(transaction_timestamps), 1)
    else:
        # deterministic static approximation: assume uniform activity over
        # account lifetime, so the "expected" 7-day share is 7/account_age
        raw["recent_transaction_ratio_7d"] = float(np.clip(7 / max(account_age, 1), 0, 1))

    if complaint_timestamps:
        recent_c = sum(1 for t in complaint_timestamps if now_day - t <= 30)
        raw["recent_complaint_ratio_30d"] = recent_c / max(len(complaint_timestamps), 1)
    else:
        raw["recent_complaint_ratio_30d"] = float(np.clip(30 / max(account_age, 1), 0, 1)) \
            if record.get("complaint_count", 0) else 0.0

    # --- graph placeholders ---
    gf = graph_features or {}
    raw["graph_unique_counterparties"] = float(gf.get("unique_counterparties", 0))
    raw["graph_suspicious_neighbor_ratio"] = float(gf.get("suspicious_neighbor_ratio", 0))
    raw["graph_cluster_risk_indicator"] = float(gf.get("cluster_risk_indicator", 0))

    return raw


def vectorize(features: dict, normalize: bool = True) -> np.ndarray:
    """Return a deterministic, ordered numpy vector for model input."""
    vec = []
    for name in FEATURE_ORDER:
        val = features.get(name, 0.0)
        if normalize:
            val = _minmax(val, NORM_BOUNDS[name])
        vec.append(val)
    return np.array(vec, dtype=float)


def record_to_vector(record: dict, **kwargs) -> np.ndarray:
    """Convenience: raw record -> normalized model-ready vector in one call."""
    feats = build_feature_vector(record, **kwargs)
    return vectorize(feats, normalize=True)
