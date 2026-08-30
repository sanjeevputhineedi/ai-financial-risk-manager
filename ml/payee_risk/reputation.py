"""
Checkpoint R4 — Reputation Engine
====================================
A dynamic reputation model. A single report must NEVER, by itself,
brand someone a scammer — risk is an evolving score that responds to
the *pattern* of evidence over time, and decays back down when
behavior is clean.

Design:
- reputation_score starts at a neutral baseline (50) unless seeded
  from the baseline model's direct risk.
- Each event (report, successful transaction, refund, dispute, model
  prediction) nudges the score by a configurable, evidence-weighted
  amount.
- Every step, decay pulls the score back toward the neutral baseline
  (simulates "good behavior over time reduces suspicion").
- Confidence grows with the amount of evidence observed (more events
  = more confident the score reflects reality).
"""

from __future__ import annotations
from dataclasses import dataclass, field
import math

DEFAULT_CONFIG = {
    "baseline": 50.0,
    "decay_rate": 0.12,          # fraction pulled back toward baseline each step
    "min_score": 0.0,
    "max_score": 100.0,
    # evidence weighting per event type (see reports.py for report categories)
    "increase_weights": {
        "SUSPECTED_FRAUD": 14.0,
        "REFUND_DISPUTE": 6.0,
        "SERVICE_DISPUTE": 4.0,
        "DELIVERY_DELAY": 2.0,
        "OTHER": 1.5,
        "model_high_risk_prediction": 8.0,
    },
    "decrease_weights": {
        "successful_transaction": 1.2,
        "refund_completed_cleanly": 2.0,
        "model_low_risk_prediction": 5.0,
    },
    # repeated-evidence amplification: each additional report of the SAME
    # category within the recent window multiplies its weight further
    "repetition_amplification": 0.25,
}


@dataclass
class ReputationState:
    payee_id: str
    score: float
    confidence: float = 0.1
    history: list = field(default_factory=list)   # list of (step, score, reason)
    event_counts: dict = field(default_factory=dict)  # category -> count


class ReputationEngine:
    def __init__(self, config: dict | None = None):
        self.config = {**DEFAULT_CONFIG, **(config or {})}

    def init_state(self, payee_id: str, seed_score: float | None = None) -> ReputationState:
        score = seed_score if seed_score is not None else self.config["baseline"]
        state = ReputationState(payee_id=payee_id, score=score)
        state.history.append((0, score, "initialized"))
        return state

    def _apply_decay(self, state: ReputationState):
        baseline = self.config["baseline"]
        decay = self.config["decay_rate"]
        state.score += (baseline - state.score) * decay

    def apply_event(self, state: ReputationState, event_type: str, category: str | None = None) -> ReputationState:
        """
        event_type: 'report' | 'successful_transaction' | 'refund_completed_cleanly'
                    | 'model_high_risk_prediction' | 'model_low_risk_prediction'
        category:   required for 'report' events, one of the report categories
        """
        cfg = self.config
        key = category if event_type == "report" else event_type
        state.event_counts[key] = state.event_counts.get(key, 0) + 1
        repeat_count = state.event_counts[key]

        if event_type == "report":
            base_weight = cfg["increase_weights"].get(category, cfg["increase_weights"]["OTHER"])
            amplification = 1.0 + cfg["repetition_amplification"] * (repeat_count - 1)
            delta = base_weight * amplification
            reason = f"report:{category} (#{repeat_count})"
        elif event_type in cfg["increase_weights"]:
            delta = cfg["increase_weights"][event_type]
            reason = event_type
        elif event_type in cfg["decrease_weights"]:
            delta = -cfg["decrease_weights"][event_type]
            reason = event_type
        else:
            raise ValueError(f"Unknown event_type/category: {event_type}/{category}")

        # apply natural decay toward baseline first (simulates time passing),
        # then apply the new evidence
        self._apply_decay(state)
        state.score += delta
        state.score = max(cfg["min_score"], min(cfg["max_score"], state.score))

        # confidence grows (saturating) with total evidence seen
        total_events = sum(state.event_counts.values())
        state.confidence = round(1 - math.exp(-total_events / 8.0), 3)

        state.history.append((len(state.history), round(state.score, 2), reason))
        return state

    def decay_only_step(self, state: ReputationState, reason: str = "time_decay") -> ReputationState:
        """Advance one time step with no new evidence — pure decay toward baseline."""
        self._apply_decay(state)
        state.history.append((len(state.history), round(state.score, 2), reason))
        return state


if __name__ == "__main__":
    engine = ReputationEngine()

    print("=== Improving legitimate seller (reported, then behaves well) ===")
    s1 = engine.init_state("payee_legit_001", seed_score=65)
    for _ in range(4):
        s1 = engine.apply_event(s1, "successful_transaction")
    print([round(s, 1) for _, s, _ in s1.history])

    print("\n=== Escalating fraud (mounting reports) ===")
    s2 = engine.init_state("payee_scam_001", seed_score=65)
    for _ in range(3):
        s2 = engine.apply_event(s2, "report", category="SUSPECTED_FRAUD")
    print([round(s, 1) for _, s, _ in s2.history])
