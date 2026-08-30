"""
Checkpoint R5 — Report Evidence Model
========================================
Classifies incoming reports and assigns them an evidentiary weight.
Not every report is equal evidence: a delivery delay is not confirmed
fraud, and a single dispute is not a pattern. This module does NOT
invent legal certainty — it only produces a *relative* evidentiary
weight consumed by the reputation engine (R4).
"""

from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime

REPORT_CATEGORIES = [
    "SUSPECTED_FRAUD",
    "DELIVERY_DELAY",
    "SERVICE_DISPUTE",
    "REFUND_DISPUTE",
    "OTHER",
]

# Relative evidentiary weight — NOT a probability of guilt, just how much
# a single instance of this category should move the reputation score.
# Kept in sync with reputation.DEFAULT_CONFIG["increase_weights"].
EVIDENTIARY_WEIGHT = {
    "SUSPECTED_FRAUD": 14.0,
    "REFUND_DISPUTE": 6.0,
    "SERVICE_DISPUTE": 4.0,
    "DELIVERY_DELAY": 2.0,
    "OTHER": 1.5,
}

VALID_OUTCOMES = ["PENDING", "CONFIRMED_FRAUDULENT", "RESOLVED_LEGITIMATE", "WITHDRAWN"]

# Confirmed fraudulent outcomes multiply the base weight; ordinary,
# unresolved disputes do not get this boost.
OUTCOME_MULTIPLIER = {
    "PENDING": 1.0,
    "CONFIRMED_FRAUDULENT": 1.8,
    "RESOLVED_LEGITIMATE": 0.1,   # resolved-in-favor-of-recipient barely counts as evidence
    "WITHDRAWN": 0.0,
}


@dataclass
class Report:
    report_id: str
    payee_id: str
    category: str
    outcome: str = "PENDING"
    filed_at_day: int = 0
    description: str | None = None

    def __post_init__(self):
        if self.category not in REPORT_CATEGORIES:
            raise ValueError(f"Invalid report category: {self.category}")
        if self.outcome not in VALID_OUTCOMES:
            raise ValueError(f"Invalid report outcome: {self.outcome}")

    def evidentiary_weight(self) -> float:
        """Weight to feed into the reputation engine for this single report."""
        base = EVIDENTIARY_WEIGHT[self.category]
        return round(base * OUTCOME_MULTIPLIER[self.outcome], 3)


def summarize_reports(reports: list[Report]) -> dict:
    """Aggregate a payee's report history into evidence-model summary stats."""
    by_category = {c: 0 for c in REPORT_CATEGORIES}
    confirmed_count = 0
    total_weight = 0.0

    for r in reports:
        by_category[r.category] += 1
        if r.outcome == "CONFIRMED_FRAUDULENT":
            confirmed_count += 1
        total_weight += r.evidentiary_weight()

    return {
        "total_reports": len(reports),
        "by_category": by_category,
        "confirmed_fraud_count": confirmed_count,
        "total_evidentiary_weight": round(total_weight, 2),
    }


if __name__ == "__main__":
    sample = [
        Report("r1", "payee_x", "DELIVERY_DELAY", outcome="RESOLVED_LEGITIMATE", filed_at_day=1),
        Report("r2", "payee_x", "SUSPECTED_FRAUD", outcome="CONFIRMED_FRAUDULENT", filed_at_day=10),
        Report("r3", "payee_x", "SUSPECTED_FRAUD", outcome="PENDING", filed_at_day=12),
    ]
    for r in sample:
        print(r.report_id, r.category, r.outcome, "-> weight", r.evidentiary_weight())
    print(summarize_reports(sample))
