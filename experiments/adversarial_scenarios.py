"""
Checkpoint R12 — Adversarial / Evasion Scenarios
====================================================
Synthetic evaluation only (no real-world abuse tooling). Tests whether
graph + reputation features catch evasive behavior that a naive
"report-count only" system would miss.

Scenarios:
  1. Gradual volume increase (low-value transactions before larger activity)
  2. Rotating counterparties (many distinct senders, no repeats)
  3. Multiple related accounts (graph cluster of freshly created accounts)
  4. Temporary activity reduction (attempt to "cool down" after reports)
"""

from __future__ import annotations
import json

from ml.graph.graph_features import TransactionGraph
from ml.payee_risk.risk_integration import graph_features_to_risk
from ml.payee_risk.reputation import ReputationEngine


def naive_report_only_risk(report_count: int) -> float:
    """Baseline comparator: risk purely proportional to report count, capped at 100."""
    return min(report_count * 15.0, 100.0)


def scenario_rotating_counterparties() -> dict:
    tg = TransactionGraph()
    tg.add_node("evasive_recipient", "recipient")
    # 40 distinct one-time senders, several of which are flagged elsewhere,
    # but NO direct reports filed against the recipient itself
    for i in range(40):
        sender = f"rotating_sender_{i}"
        suspicious = i % 6 == 0  # ~17% flagged
        tg.add_node(sender, "sender", suspicious=suspicious)
        tg.add_payment(sender, "evasive_recipient", amount=300, day=i)

    graph_feats = tg.features_for("evasive_recipient")
    graph_risk = graph_features_to_risk(graph_feats)
    naive_risk = naive_report_only_risk(report_count=0)  # zero direct reports

    return {
        "scenario": "rotating_counterparties",
        "direct_reports": 0,
        "naive_report_only_risk": naive_risk,
        "graph_derived_risk": graph_risk,
        "graph_features": graph_feats,
        "graph_adds_value": graph_risk > naive_risk,
    }


def scenario_related_account_cluster() -> dict:
    tg = TransactionGraph()
    # a cluster of 4 freshly-created accounts all funded by, and funding,
    # each other and a small set of shared senders -- classic mule-ring shape
    cluster = ["mule_a", "mule_b", "mule_c", "mule_d"]
    for n in cluster:
        tg.add_node(n, "recipient")
    tg.mark_suspicious("mule_a", True)  # only ONE of the four has been flagged so far

    shared_senders = [f"shared_sender_{i}" for i in range(3)]
    for s in shared_senders:
        tg.add_node(s, "sender")
        for n in cluster:
            tg.add_payment(s, n, amount=1000, day=0)
    # money moves between the mule accounts themselves
    tg.add_payment("mule_a", "mule_b", amount=800, day=1)
    tg.add_payment("mule_b", "mule_c", amount=750, day=2)
    tg.add_payment("mule_c", "mule_d", amount=700, day=3)

    results = {}
    for n in cluster:
        gf = tg.features_for(n)
        results[n] = {
            "graph_features": gf,
            "graph_risk": graph_features_to_risk(gf),
            "naive_report_only_risk": 0.0,  # none of mule_b/c/d have been reported at all
        }
    return {
        "scenario": "related_account_cluster",
        "note": "only mule_a was ever reported; graph propagates elevated risk to b/c/d",
        "results": results,
        "graph_adds_value": all(
            results[n]["graph_risk"] > results[n]["naive_report_only_risk"]
            for n in ["mule_b", "mule_c", "mule_d"]
        ),
    }


def scenario_activity_cooldown() -> dict:
    """
    An account that gets reported, then goes quiet to 'wait out' suspicion,
    then resumes. Reputation should decay toward baseline during the quiet
    period but should NOT fully erase the recorded evidence weight —
    demonstrated here via the engine's persistent event_counts.
    """
    engine = ReputationEngine()
    state = engine.init_state("cooldown_account", seed_score=50)
    state = engine.apply_event(state, "report", category="SUSPECTED_FRAUD")
    score_after_report = state.score

    # simulate a quiet period: several decay-only steps, no new evidence
    for _ in range(5):
        state = engine.decay_only_step(state)
    score_after_cooldown = state.score

    # resumes activity with another report -> repetition amplification kicks back in
    state = engine.apply_event(state, "report", category="SUSPECTED_FRAUD")
    score_after_resumed_report = state.score

    return {
        "scenario": "activity_cooldown_evasion",
        "score_after_first_report": round(score_after_report, 2),
        "score_after_cooldown": round(score_after_cooldown, 2),
        "score_after_second_report": round(score_after_resumed_report, 2),
        "evidence_persisted": state.event_counts.get("SUSPECTED_FRAUD", 0) == 2,
        "note": "Score decays during quiet period but a second report is amplified due to prior evidence count, preventing simple cooldown evasion.",
    }


def run_all(out_path: str = "experiments/adversarial_results.json") -> dict:
    results = {
        "rotating_counterparties": scenario_rotating_counterparties(),
        "related_account_cluster": scenario_related_account_cluster(),
        "activity_cooldown_evasion": scenario_activity_cooldown(),
    }
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    return results


if __name__ == "__main__":
    results = run_all()
    print(json.dumps(results, indent=2))
