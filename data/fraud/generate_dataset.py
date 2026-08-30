"""
Checkpoint R1 — Payee Dataset Design
=====================================
Generates a synthetic dataset of recipient (payee) profiles for the
AI Financial Risk Manager (UPI-like, simulated only — no real accounts).

Profile classes:
    TRUSTED_MERCHANT
    NORMAL_USER
    NEW_ACCOUNT
    REPORTED_LEGITIMATE     <- a legit account that has drawn complaints (false-positive case)
    SUSPICIOUS_ACCOUNT
    CONFIRMED_SCAM_LIKE

Design notes:
- Each class has its own feature-generating distribution so that fraud
  patterns are NOT identical (Rule 9 / R1 requirement: no single
  hard-coded threshold like "amount > 9000 => fraud").
- REPORTED_LEGITIMATE deliberately overlaps with SUSPICIOUS_ACCOUNT on
  complaint_count so the model/reputation engine has to work to tell
  them apart (this feeds directly into Checkpoint R11).
- Reproducible via a fixed seed; dataset size is configurable.
- Label distribution is realistically imbalanced (fraud is rare).
"""

from __future__ import annotations
import argparse
import numpy as np
import pandas as pd
from dataclasses import dataclass

PROFILE_CLASSES = [
    "TRUSTED_MERCHANT",
    "NORMAL_USER",
    "NEW_ACCOUNT",
    "REPORTED_LEGITIMATE",
    "SUSPICIOUS_ACCOUNT",
    "CONFIRMED_SCAM_LIKE",
]

# Binary ML label: is this recipient ultimately fraud-like?
# (REPORTED_LEGITIMATE is explicitly NOT fraud -> tests false-positive handling)
FRAUD_LABEL = {
    "TRUSTED_MERCHANT": 0,
    "NORMAL_USER": 0,
    "NEW_ACCOUNT": 0,
    "REPORTED_LEGITIMATE": 0,
    "SUSPICIOUS_ACCOUNT": 1,
    "CONFIRMED_SCAM_LIKE": 1,
}

# Realistic class mix (imbalanced — fraud/suspicious are the minority)
DEFAULT_CLASS_WEIGHTS = {
    "TRUSTED_MERCHANT": 0.18,
    "NORMAL_USER": 0.45,
    "NEW_ACCOUNT": 0.15,
    "REPORTED_LEGITIMATE": 0.07,
    "SUSPICIOUS_ACCOUNT": 0.10,
    "CONFIRMED_SCAM_LIKE": 0.05,
}


def _clip01(x):
    return np.clip(x, 0.0, 1.0)


def _gen_profile(rng: np.random.Generator, profile: str) -> dict:
    """Sample one recipient's raw feature values given its hidden profile class."""

    if profile == "TRUSTED_MERCHANT":
        account_age = rng.integers(365, 3650)
        transaction_count = rng.integers(500, 20000)
        incoming_volume = rng.gamma(8, 15000)
        outgoing_volume = incoming_volume * rng.uniform(0.05, 0.3)
        unique_senders = rng.integers(200, 5000)
        complaint_count = rng.poisson(1.5)
        successful_ratio = rng.uniform(0.96, 0.999)
        refund_ratio = rng.uniform(0.0, 0.03)
        suspicious_counterparties = rng.poisson(0.2)
        concentration = rng.uniform(0.01, 0.1)  # diffuse sender base

    elif profile == "NORMAL_USER":
        account_age = rng.integers(60, 2000)
        transaction_count = rng.integers(5, 400)
        incoming_volume = rng.gamma(3, 4000)
        outgoing_volume = rng.gamma(3, 4000)
        unique_senders = rng.integers(2, 60)
        complaint_count = rng.poisson(0.3)
        successful_ratio = rng.uniform(0.9, 0.999)
        refund_ratio = rng.uniform(0.0, 0.08)
        suspicious_counterparties = rng.poisson(0.1)
        concentration = rng.uniform(0.05, 0.4)

    elif profile == "NEW_ACCOUNT":
        account_age = rng.integers(1, 45)
        transaction_count = rng.integers(0, 25)
        incoming_volume = rng.gamma(2, 1500)
        outgoing_volume = rng.gamma(2, 1500)
        unique_senders = rng.integers(0, 10)
        complaint_count = rng.poisson(0.15)
        successful_ratio = rng.uniform(0.8, 1.0)
        refund_ratio = rng.uniform(0.0, 0.1)
        suspicious_counterparties = rng.poisson(0.1)
        concentration = rng.uniform(0.2, 0.7)

    elif profile == "REPORTED_LEGITIMATE":
        # Looks risky on complaints alone, but behaviorally healthy —
        # this is the key false-positive test case (see R11).
        account_age = rng.integers(120, 1800)
        transaction_count = rng.integers(50, 3000)
        incoming_volume = rng.gamma(5, 6000)
        outgoing_volume = incoming_volume * rng.uniform(0.1, 0.4)
        unique_senders = rng.integers(20, 800)
        complaint_count = rng.poisson(4.0)          # elevated, overlaps SUSPICIOUS
        successful_ratio = rng.uniform(0.9, 0.98)   # still mostly fine
        refund_ratio = rng.uniform(0.02, 0.12)       # a bit higher (disputes resolved)
        suspicious_counterparties = rng.poisson(0.3)
        concentration = rng.uniform(0.05, 0.3)

    elif profile == "SUSPICIOUS_ACCOUNT":
        account_age = rng.integers(1, 120)
        transaction_count = rng.integers(5, 200)
        incoming_volume = rng.gamma(3, 5000)
        outgoing_volume = incoming_volume * rng.uniform(0.6, 0.95)  # pass-through behavior
        unique_senders = rng.integers(10, 150)
        complaint_count = rng.poisson(3.5)           # overlaps REPORTED_LEGITIMATE on purpose
        successful_ratio = rng.uniform(0.6, 0.9)
        refund_ratio = rng.uniform(0.1, 0.35)
        suspicious_counterparties = rng.poisson(2.0)
        concentration = rng.uniform(0.3, 0.8)

    else:  # CONFIRMED_SCAM_LIKE
        account_age = rng.integers(0, 60)
        transaction_count = rng.integers(3, 150)
        incoming_volume = rng.gamma(4, 8000)
        outgoing_volume = incoming_volume * rng.uniform(0.7, 0.99)
        unique_senders = rng.integers(15, 300)
        complaint_count = rng.poisson(7.0)
        successful_ratio = rng.uniform(0.3, 0.7)
        refund_ratio = rng.uniform(0.2, 0.6)
        suspicious_counterparties = rng.poisson(4.0)
        concentration = rng.uniform(0.5, 0.95)

    # Inject realistic overlap noise so classes are NOT perfectly separable
    # (real fraud detection never is — a model scoring 1.0 on every metric
    # is a sign of a toy dataset, not a good model). We jitter the two
    # ratio features that most separate the classes, and occasionally
    # generate a genuinely ambiguous / borderline case.
    successful_ratio = _clip01(successful_ratio + rng.normal(0, 0.06))
    complaint_count = max(0, complaint_count + rng.integers(-1, 2))
    refund_ratio = _clip01(refund_ratio + rng.normal(0, 0.05))

    # ~4% of accounts in any class are genuinely ambiguous borderline cases
    if rng.random() < 0.04:
        successful_ratio = _clip01(rng.uniform(0.55, 0.85))
        refund_ratio = _clip01(rng.uniform(0.08, 0.25))
        complaint_count = max(complaint_count, rng.poisson(2.5))

    account_age = max(int(account_age), 0)
    transaction_count = max(int(transaction_count), 0)
    incoming_volume = float(max(incoming_volume * rng.lognormal(0, 0.15), 0))
    outgoing_volume = float(max(outgoing_volume * rng.lognormal(0, 0.15), 0))

    # Derived / composite features
    denom_days = max(account_age, 1)
    transaction_velocity = transaction_count / denom_days
    complaint_rate = complaint_count / max(transaction_count, 1)
    incoming_outgoing_ratio = incoming_volume / max(outgoing_volume, 1.0)

    return {
        "profile_type": profile,
        "label_fraud_like": FRAUD_LABEL[profile],
        "account_age": account_age,
        "transaction_count": transaction_count,
        "incoming_volume": round(incoming_volume, 2),
        "outgoing_volume": round(outgoing_volume, 2),
        "transaction_velocity": round(transaction_velocity, 4),
        "unique_senders": int(max(unique_senders, 0)),
        "complaint_count": int(max(complaint_count, 0)),
        "complaint_rate": round(_clip01(complaint_rate), 4),
        "successful_transaction_ratio": round(_clip01(successful_ratio), 4),
        "refund_ratio": round(_clip01(refund_ratio), 4),
        "suspicious_counterparty_count": int(max(suspicious_counterparties, 0)),
        "transaction_concentration": round(_clip01(concentration), 4),
        "incoming_outgoing_ratio": round(incoming_outgoing_ratio, 4),
    }


def generate_dataset(n: int, seed: int = 42, class_weights: dict | None = None) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    weights = class_weights or DEFAULT_CLASS_WEIGHTS
    classes = list(weights.keys())
    probs = np.array([weights[c] for c in classes], dtype=float)
    probs = probs / probs.sum()

    assigned = rng.choice(classes, size=n, p=probs)
    rows = [_gen_profile(rng, profile) for profile in assigned]

    df = pd.DataFrame(rows)
    df.insert(0, "payee_id", [f"payee_{i:06d}" for i in range(n)])
    return df


def main():
    parser = argparse.ArgumentParser(description="Generate synthetic payee/fraud dataset (R1)")
    parser.add_argument("--n", type=int, default=10000, help="number of synthetic payees")
    parser.add_argument("--seed", type=int, default=42, help="random seed for reproducibility")
    parser.add_argument("--out", type=str, default="data/fraud/synthetic_payees.csv")
    args = parser.parse_args()

    df = generate_dataset(args.n, args.seed)
    df.to_csv(args.out, index=False)

    print(f"Generated {len(df)} synthetic payees -> {args.out}")
    print("\nClass distribution:")
    print(df["profile_type"].value_counts())
    print("\nFraud-like label distribution:")
    print(df["label_fraud_like"].value_counts(normalize=True).round(3))


if __name__ == "__main__":
    main()
