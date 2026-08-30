"""
Checkpoint R7 — Graph-Based Risk Integration
================================================
Combines three independent risk signals into one calibrated
combined_payee_risk score:

    direct_risk       - the baseline ML model's fraud probability (R3)
    reputation_risk    - the evolving reputation engine's score (R4)
    graph_risk          - a score derived from transaction-graph features (R6)

Weighting/calibration method
-----------------------------
We use a documented, fixed weighted average (not a second trained
model) so the calibration is transparent and auditable for this
prototype:

    combined = 0.45 * direct_risk
             + 0.35 * reputation_risk
             + 0.20 * graph_risk

Rationale for weights: the direct ML model captures the richest,
most-validated signal (it's evaluated in R10), so it gets the largest
share. Reputation captures behavioral evolution over time and is
weighted second. Graph risk is currently the least mature signal
(no GNN yet — see below) so it gets the smallest weight, acting as a
risk *amplifier* for edge cases rather than the primary driver.

This module exposes a clean `combine()` interface so a future GNN or
learned meta-model can be swapped in without changing callers (R9 API
contract stays stable).
"""

from __future__ import annotations
from dataclasses import dataclass

COMBINATION_WEIGHTS = {
    "direct": 0.45,
    "reputation": 0.35,
    "graph": 0.20,
}


def graph_features_to_risk(graph_feats: dict) -> float:
    """
    Turn raw graph features (R6) into a 0-100 graph_risk score.
    Simple, documented linear combination — explicit interface point
    for a future GNN replacement.
    """
    suspicious_ratio = graph_feats.get("suspicious_neighbor_ratio", 0.0)
    cluster_risk = graph_feats.get("cluster_risk_indicator", 0.0)
    concentration = graph_feats.get("transaction_concentration", 0.0)

    # weighted sum of already-normalized [0,1] signals -> scale to 0-100
    raw = (0.5 * suspicious_ratio) + (0.3 * cluster_risk) + (0.2 * concentration)
    return round(min(raw, 1.0) * 100, 2)


@dataclass
class CombinedRisk:
    direct_risk: float
    reputation_risk: float
    graph_risk: float
    combined_payee_risk: float
    weights: dict


def combine(direct_risk: float, reputation_risk: float, graph_risk: float,
            weights: dict | None = None) -> CombinedRisk:
    w = weights or COMBINATION_WEIGHTS
    combined = (
        w["direct"] * direct_risk
        + w["reputation"] * reputation_risk
        + w["graph"] * graph_risk
    )
    combined = round(min(max(combined, 0.0), 100.0), 2)
    return CombinedRisk(
        direct_risk=round(direct_risk, 2),
        reputation_risk=round(reputation_risk, 2),
        graph_risk=round(graph_risk, 2),
        combined_payee_risk=combined,
        weights=w,
    )


# --- Future-GNN interface -----------------------------------------------
# To swap in a learned graph model later, implement a class with the same
# signature as `graph_features_to_risk` (features dict -> float 0-100)
# and pass it into combine() call sites. No other code needs to change.
class GraphRiskScorer:
    """Interface for a future GNN-based graph risk scorer. Not implemented
    in this checkpoint per R7 instructions (do NOT implement a GNN initially)."""
    def score(self, graph_feats: dict) -> float:
        raise NotImplementedError("GNN scorer not implemented in baseline (R7 spec).")


if __name__ == "__main__":
    result = combine(direct_risk=40, reputation_risk=55, graph_risk=graph_features_to_risk(
        {"suspicious_neighbor_ratio": 0.6, "cluster_risk_indicator": 0.5, "transaction_concentration": 0.2}
    ))
    print(result)
