"""
Checkpoint R11 — False Positive Experiment
=============================================
Core research result: can the reputation engine tell apart a
REPORTED_LEGITIMATE seller (elevated risk from complaints, but good
underlying behavior) from a CONFIRMED_SCAM_LIKE recipient (escalating
genuine evidence)?

Demonstrates:
    Legitimate: risk initially elevated -> successful behavior -> risk decays
    Fraud:      risk increases as new evidence arrives
"""

from __future__ import annotations
import json
from ml.payee_risk.reputation import ReputationEngine


def run_experiment(out_path: str = "experiments/false_positive_results.json") -> dict:
    engine = ReputationEngine()

    # --- Scenario A: reported legitimate merchant that behaves well afterward ---
    legit = engine.init_state("reported_legitimate_merchant", seed_score=68)
    legit_timeline = [("initial_report_spike", 68.0)]
    # a couple of initial disputes drove the score up before we start observing
    for _ in range(6):
        legit = engine.apply_event(legit, "successful_transaction")
    legit = engine.apply_event(legit, "refund_completed_cleanly")
    for _ in range(4):
        legit = engine.apply_event(legit, "successful_transaction")
    legit_timeline += [(reason, score) for _, score, reason in legit.history[1:]]

    # --- Scenario B: actual suspicious merchant escalating ---
    scam = engine.init_state("actual_suspicious_merchant", seed_score=68)
    scam = engine.apply_event(scam, "report", category="SUSPECTED_FRAUD")
    scam = engine.apply_event(scam, "report", category="REFUND_DISPUTE")
    scam = engine.apply_event(scam, "report", category="SUSPECTED_FRAUD")
    scam = engine.apply_event(scam, "report", category="SUSPECTED_FRAUD")
    scam_timeline = [(reason, score) for _, score, reason in scam.history]

    result = {
        "legitimate_seller": {
            "final_score": legit.score,
            "trend": "decreasing" if legit_timeline[-1][1] < legit_timeline[1][1] else "increasing",
            "timeline": legit_timeline,
        },
        "suspicious_merchant": {
            "final_score": scam.score,
            "trend": "decreasing" if scam_timeline[-1][1] < scam_timeline[0][1] else "increasing",
            "timeline": scam_timeline,
        },
        "distinguishable": legit.score < scam.score,
        "score_gap": round(scam.score - legit.score, 2),
    }

    with open(out_path, "w") as f:
        json.dump(result, f, indent=2)

    return result


if __name__ == "__main__":
    result = run_experiment()
    print(json.dumps(result, indent=2))
    assert result["distinguishable"], "FAILED: reputation engine could not distinguish legit from fraud"
    print("\nPASS: reputation engine correctly distinguishes reported-legitimate from actual fraud.")
