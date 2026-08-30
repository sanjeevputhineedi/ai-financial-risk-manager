"""
Personal Risk Anomaly Detector — Checkpoint 05.

Combines statistical z-score analysis with Isolation Forest ML to detect
anomalous personal spending behavior. Returns a risk score (0-100),
risk level, and human-readable reasons.
"""

import numpy as np
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime, timezone

from ml.personal_risk.profile import UserSpendProfile

# Try to import IsolationForest; fall back to pure statistical if unavailable
try:
    from sklearn.ensemble import IsolationForest
    _HAS_SKLEARN = True
except ImportError:
    _HAS_SKLEARN = False


class PersonalRiskDetector:
    """
    Multi-signal anomaly detector for personal transaction risk.

    Signals:
    1. Amount z-score deviation from historical spend profile
    2. Isolation Forest anomaly score (if sklearn available)
    3. Time-of-day deviation
    4. Recipient familiarity
    5. Balance consumption ratio
    6. Transaction velocity spike
    """

    # Weight allocation for each signal
    WEIGHTS = {
        "amount_zscore": 0.35,
        "isolation_forest": 0.15,
        "time_deviation": 0.10,
        "recipient_familiarity": 0.15,
        "balance_ratio": 0.15,
        "velocity": 0.10,
    }

    def __init__(self):
        self.isolation_forest = None
        if _HAS_SKLEARN:
            self.isolation_forest = IsolationForest(
                n_estimators=100,
                contamination=0.1,
                random_state=42
            )

    def analyze(
        self,
        profile: UserSpendProfile,
        amount: float,
        recipient_id: str,
        balance: float = 0.0,
        transaction_hour: Optional[int] = None,
        recent_tx_count_24h: int = 0
    ) -> Dict[str, Any]:
        """
        Analyze a transaction against the user's spend profile.

        Returns:
            {
                "personal_risk_score": float (0-100),
                "risk_level": str (LOW/MEDIUM/HIGH/CRITICAL),
                "reasons": List[str],
                "signal_breakdown": Dict[str, float]
            }
        """
        reasons: List[str] = []
        signals: Dict[str, float] = {}

        if transaction_hour is None:
            transaction_hour = datetime.now(timezone.utc).hour

        # Signal 1: Amount z-score
        zscore = profile.amount_zscore(amount)
        amount_risk = self._zscore_to_risk(zscore, amount, profile, reasons)
        signals["amount_zscore"] = amount_risk

        # Signal 2: Isolation Forest (if enough history and sklearn available)
        if self.isolation_forest and profile.total_transactions >= 10:
            iso_risk = self._isolation_forest_risk(profile, amount, reasons)
        else:
            iso_risk = amount_risk * 0.5  # Proxy from z-score when IF unavailable
        signals["isolation_forest"] = iso_risk

        # Signal 3: Time-of-day deviation
        time_risk = self._time_deviation_risk(profile, transaction_hour, reasons)
        signals["time_deviation"] = time_risk

        # Signal 4: Recipient familiarity
        familiarity_risk = self._recipient_familiarity_risk(profile, recipient_id, reasons)
        signals["recipient_familiarity"] = familiarity_risk

        # Signal 5: Balance consumption ratio
        balance_risk = self._balance_ratio_risk(amount, balance, reasons)
        signals["balance_ratio"] = balance_risk

        # Signal 6: Velocity spike
        velocity_risk = self._velocity_risk(profile, recent_tx_count_24h, reasons)
        signals["velocity"] = velocity_risk

        # Weighted combination
        combined = sum(
            signals[key] * self.WEIGHTS[key]
            for key in self.WEIGHTS
        )

        # Scale to 0-100 and apply floor/ceiling
        personal_risk = max(5.0, min(98.0, combined))

        # Determine risk level
        risk_level = self._classify_risk_level(personal_risk)

        # Add a positive reason if risk is low
        if not reasons:
            reasons.append("Transaction is within your normal spending patterns.")

        return {
            "personal_risk_score": round(personal_risk, 1),
            "risk_level": risk_level,
            "reasons": reasons,
            "signal_breakdown": {k: round(v, 2) for k, v in signals.items()}
        }

    def _zscore_to_risk(
        self, zscore: float, amount: float, profile: UserSpendProfile, reasons: List[str]
    ) -> float:
        """Convert z-score to risk score 0-100."""
        abs_z = abs(zscore)

        if profile.total_transactions == 0:
            # First-time user — scale based on absolute amount
            if amount >= 10000:
                reasons.append(f"High-value initial transfer: ₹{amount:,.2f} with no transaction history.")
                return 75.0
            elif amount >= 5000:
                reasons.append(f"Moderate first transaction: ₹{amount:,.2f} on new account.")
                return 45.0
            return 15.0

        if abs_z > 4.0:
            reasons.append(
                f"Transaction ₹{amount:,.2f} is {abs_z:.1f}σ above your average spend of ₹{profile.mean_amount:,.2f} — extreme anomaly."
            )
            return min(95.0, 60.0 + abs_z * 5)
        elif abs_z > 2.5:
            reasons.append(
                f"Transaction ₹{amount:,.2f} is {abs_z:.1f}σ above your average (₹{profile.mean_amount:,.2f}) — significantly unusual."
            )
            return 50.0 + (abs_z - 2.5) * 15
        elif abs_z > 1.5:
            reasons.append(
                f"Transaction ₹{amount:,.2f} is moderately above your typical spending range."
            )
            return 25.0 + (abs_z - 1.5) * 20
        elif abs_z > 1.0:
            return 15.0 + (abs_z - 1.0) * 10
        return max(5.0, abs_z * 10)

    def _isolation_forest_risk(
        self, profile: UserSpendProfile, amount: float, reasons: List[str]
    ) -> float:
        """Fit Isolation Forest on user's history and score the new transaction."""
        try:
            # Build feature matrix from historical patterns
            hist_amounts = list(profile.amount_percentiles.values()) if profile.amount_percentiles else [profile.mean_amount]
            X_train = np.array([[a] for a in np.linspace(
                profile.min_amount, profile.max_amount, min(50, profile.total_transactions)
            )])

            if len(X_train) < 5:
                return 30.0

            self.isolation_forest.fit(X_train)
            score = self.isolation_forest.score_samples(np.array([[amount]]))[0]

            # Isolation Forest scores: negative = more anomalous
            # Typical range: -0.5 (normal) to -1.0 (anomalous)
            anomaly_risk = max(0, min(100, ((-score - 0.3) / 0.5) * 100))

            if anomaly_risk > 60:
                reasons.append("ML anomaly detector flagged this transaction as statistically unusual for your profile.")

            return anomaly_risk

        except Exception:
            return 25.0

    def _time_deviation_risk(
        self, profile: UserSpendProfile, hour: int, reasons: List[str]
    ) -> float:
        """Score time-of-day unusualness."""
        deviation = profile.time_deviation_score(hour)
        risk = deviation * 70.0  # Max 70 for time alone

        if deviation > 0.8:
            period = "late night" if (hour >= 23 or hour < 5) else "unusual hours"
            reasons.append(f"Transaction initiated during {period} (hour {hour:02d}:00) — atypical for your usage pattern.")

        return risk

    def _recipient_familiarity_risk(
        self, profile: UserSpendProfile, recipient_id: str, reasons: List[str]
    ) -> float:
        """Score recipient unfamiliarity."""
        familiarity = profile.recipient_familiarity(recipient_id)

        if familiarity == 0 and profile.total_transactions > 3:
            reasons.append("First-time recipient — you have never transacted with this payee before.")
            return 55.0
        elif familiarity < 0.1 and profile.total_transactions > 5:
            reasons.append("Rarely transacted recipient — limited history with this payee.")
            return 35.0
        elif familiarity < 0.3:
            return 20.0

        return max(5.0, (1.0 - familiarity) * 30)

    def _balance_ratio_risk(
        self, amount: float, balance: float, reasons: List[str]
    ) -> float:
        """Score what percentage of balance is being consumed."""
        if balance <= 0:
            return 20.0

        ratio = amount / balance
        if ratio > 0.9:
            reasons.append(f"Payment consumes {ratio*100:.0f}% of your available balance — near-total account drain.")
            return 90.0
        elif ratio > 0.6:
            reasons.append(f"Payment consumes {ratio*100:.0f}% of your available balance.")
            return 60.0
        elif ratio > 0.4:
            return 35.0
        elif ratio > 0.2:
            return 15.0
        return 5.0

    def _velocity_risk(
        self, profile: UserSpendProfile, recent_24h: int, reasons: List[str]
    ) -> float:
        """Score transaction velocity spikes."""
        expected_daily = max(profile.daily_frequency, 0.5)

        if recent_24h <= 0:
            return 5.0

        ratio = recent_24h / expected_daily

        if ratio > 5.0:
            reasons.append(f"Transaction velocity spike: {recent_24h} transactions in 24h vs your daily average of {expected_daily:.1f}.")
            return 80.0
        elif ratio > 3.0:
            reasons.append(f"Elevated transaction frequency: {recent_24h} today vs typical {expected_daily:.1f}/day.")
            return 50.0
        elif ratio > 2.0:
            return 30.0

        return 5.0

    @staticmethod
    def _classify_risk_level(score: float) -> str:
        """Classify numeric risk score into level."""
        if score < 30:
            return "LOW"
        elif score < 60:
            return "MEDIUM"
        elif score < 85:
            return "HIGH"
        return "CRITICAL"
