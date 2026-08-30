"""
Checkpoint R8 — Payee Explainability
========================================
Translates a risk score into human-readable reasons. Uses simple,
auditable threshold rules on the documented features (fast, always
available) and optionally augments with SHAP values from the trained
RandomForest when the model is available (slower, more precise
per-prediction attribution).

Rule-based explanations are kept intentionally conservative in
language per Rule 7 of DEVELOPMENT.md: we say "elevated risk of X",
never "this is a scam."
"""

from __future__ import annotations

# (feature_name, condition_fn, human_readable_reason)
EXPLANATION_RULES = [
    ("account_age", lambda v: v < 30, "Recently created account"),
    ("transaction_velocity", lambda v: v > 2.0, "Unusually high transaction velocity for account age"),
    ("complaint_count", lambda v: v >= 3, "Multiple reports filed against this recipient"),
    ("recent_complaint_ratio_30d", lambda v: v > 0.6, "Reports have clustered recently"),
    ("unique_senders", lambda v: v > 100, "Unusually high number of unique senders"),
    ("incoming_outgoing_ratio", lambda v: 0.85 <= v <= 1.15, "Funds appear to pass through quickly (possible mule pattern)"),
    ("refund_ratio", lambda v: v > 0.15, "High proportion of transactions refunded"),
    ("successful_transaction_ratio", lambda v: v < 0.8, "Lower-than-typical successful transaction rate"),
    ("suspicious_counterparty_count", lambda v: v >= 2, "Connected to other flagged accounts"),
    ("graph_suspicious_neighbor_ratio", lambda v: v > 0.3, "Significant share of transaction-graph neighbors are flagged suspicious"),
    ("graph_cluster_risk_indicator", lambda v: v > 0.3, "Part of a network cluster with elevated suspicious activity"),
    ("transaction_concentration", lambda v: v > 0.6, "Incoming funds concentrated among very few senders"),
]

POSITIVE_RULES = [
    ("successful_transaction_ratio", lambda v: v > 0.97, "Strong track record of successful transactions"),
    ("account_age", lambda v: v > 365, "Long-standing account history"),
    ("refund_ratio", lambda v: v < 0.02, "Very low refund/dispute rate"),
]


def generate_reasons(raw_features: dict, max_reasons: int = 5) -> list[str]:
    """Rule-based, always-available explanation generator."""
    reasons = []
    for feature, condition, text in EXPLANATION_RULES:
        val = raw_features.get(feature)
        if val is not None and condition(val):
            reasons.append(text)
    return reasons[:max_reasons] if reasons else ["No significant risk indicators identified"]


def generate_reassurances(raw_features: dict, max_items: int = 3) -> list[str]:
    """Positive-signal explanations, useful for the false-positive / recovery narrative (R11)."""
    reasons = []
    for feature, condition, text in POSITIVE_RULES:
        val = raw_features.get(feature)
        if val is not None and condition(val):
            reasons.append(text)
    return reasons[:max_items]


def shap_top_features(model, feature_vector, feature_names, top_n: int = 5):
    """
    Optional SHAP-based per-prediction attribution.
    Requires the `shap` package; used only when explicitly justified by a
    high-stakes prediction, per R8 instructions ("where justified").
    """
    try:
        import shap
    except ImportError:
        return None  # SHAP not installed -> caller should fall back to rule-based reasons

    explainer = shap.TreeExplainer(model.clf)
    shap_values = explainer.shap_values(feature_vector.reshape(1, -1))
    # shap_values[1] = contribution toward the "fraud" class for tree ensembles
    contributions = shap_values[1][0] if isinstance(shap_values, list) else shap_values[0]
    ranked = sorted(zip(feature_names, contributions), key=lambda kv: -abs(kv[1]))
    return ranked[:top_n]


if __name__ == "__main__":
    sample_features = {
        "account_age": 12,
        "transaction_velocity": 3.2,
        "complaint_count": 4,
        "recent_complaint_ratio_30d": 0.8,
        "unique_senders": 150,
        "incoming_outgoing_ratio": 0.95,
        "refund_ratio": 0.22,
        "successful_transaction_ratio": 0.7,
        "suspicious_counterparty_count": 3,
    }
    print(generate_reasons(sample_features))
