"""
User Spend Profile — Aggregates transaction history into a behavioral baseline.

Computes: mean amount, std dev, max, time-of-day histogram, recipient frequency,
daily/weekly cadence for anomaly comparison.
"""

import numpy as np
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
from dataclasses import dataclass, field


@dataclass
class UserSpendProfile:
    """Behavioral baseline computed from a user's transaction history."""

    user_id: str
    mean_amount: float = 0.0
    std_amount: float = 0.0
    max_amount: float = 0.0
    min_amount: float = 0.0
    median_amount: float = 0.0
    total_transactions: int = 0
    daily_frequency: float = 0.0          # avg transactions per day
    weekly_frequency: float = 0.0         # avg transactions per week
    time_of_day_histogram: Dict[int, int] = field(default_factory=dict)  # hour -> count
    recipient_frequency: Dict[str, int] = field(default_factory=dict)    # recipient -> count
    amount_percentiles: Dict[str, float] = field(default_factory=dict)   # p25, p50, p75, p90, p95, p99

    @classmethod
    def from_transactions(cls, user_id: str, transactions: List[Dict[str, Any]]) -> "UserSpendProfile":
        """
        Build a spend profile from a list of transaction dicts.
        Each dict should have: amount (float), created_at (datetime or str), recipient_vpa (str).
        """
        profile = cls(user_id=user_id)

        if not transactions:
            return profile

        amounts = []
        timestamps = []
        recipients: Dict[str, int] = {}
        hour_hist: Dict[int, int] = {h: 0 for h in range(24)}

        for tx in transactions:
            amt = float(tx.get("amount", 0))
            amounts.append(amt)

            # Parse timestamp
            ts = tx.get("created_at")
            if isinstance(ts, str):
                try:
                    ts = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                except (ValueError, TypeError):
                    ts = datetime.now(timezone.utc)
            if isinstance(ts, datetime):
                timestamps.append(ts)
                hour_hist[ts.hour] = hour_hist.get(ts.hour, 0) + 1

            # Track recipient frequency
            recip = tx.get("recipient_vpa", "unknown")
            recipients[recip] = recipients.get(recip, 0) + 1

        arr = np.array(amounts)
        profile.mean_amount = float(np.mean(arr))
        profile.std_amount = float(np.std(arr)) if len(arr) > 1 else 0.0
        profile.max_amount = float(np.max(arr))
        profile.min_amount = float(np.min(arr))
        profile.median_amount = float(np.median(arr))
        profile.total_transactions = len(amounts)
        profile.time_of_day_histogram = hour_hist
        profile.recipient_frequency = recipients

        # Percentiles
        for p_label, p_val in [("p25", 25), ("p50", 50), ("p75", 75), ("p90", 90), ("p95", 95), ("p99", 99)]:
            profile.amount_percentiles[p_label] = float(np.percentile(arr, p_val))

        # Frequency (transactions per day / week)
        if len(timestamps) >= 2:
            timestamps.sort()
            span_days = max((timestamps[-1] - timestamps[0]).total_seconds() / 86400, 1.0)
            profile.daily_frequency = len(timestamps) / span_days
            profile.weekly_frequency = profile.daily_frequency * 7
        elif timestamps:
            profile.daily_frequency = 1.0
            profile.weekly_frequency = 7.0

        return profile

    def amount_zscore(self, amount: float) -> float:
        """Compute z-score of an amount relative to user's history."""
        if self.std_amount < 1e-6:
            # No variance — any significant deviation is suspicious
            if self.total_transactions > 0 and self.mean_amount > 0:
                return abs(amount - self.mean_amount) / max(self.mean_amount, 1.0) * 2.0
            return 0.0
        return (amount - self.mean_amount) / self.std_amount

    def time_deviation_score(self, hour: int) -> float:
        """
        Score how unusual a transaction at this hour is (0-1).
        0 = very common hour, 1 = never transacted at this hour.
        """
        total = sum(self.time_of_day_histogram.values())
        if total == 0:
            return 0.0
        hour_count = self.time_of_day_histogram.get(hour, 0)
        # Invert: fewer transactions at this hour = higher deviation
        frequency_ratio = hour_count / total
        return 1.0 - min(frequency_ratio * 10.0, 1.0)  # Scale up — even 10% is normal

    def recipient_familiarity(self, recipient_id: str) -> float:
        """
        Score 0-1: how familiar the recipient is.
        1 = very familiar (frequent), 0 = never seen before.
        """
        if not self.recipient_frequency:
            return 0.0
        count = self.recipient_frequency.get(recipient_id, 0)
        max_count = max(self.recipient_frequency.values())
        if max_count == 0:
            return 0.0
        return count / max_count
