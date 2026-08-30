"""
Personal Risk API — Stable contract for the backend risk service.

Mirrors the payee risk API pattern:
    result = analyze_personal_risk(sender_id, amount, recipient_id, transaction_history)

Returns:
    {
        "personal_risk_score": float (0-100),
        "risk_level": str,
        "reasons": List[str],
        "model_version": "personal-v2"
    }
"""

from typing import Dict, Any, List, Optional
from ml.personal_risk.profile import UserSpendProfile
from ml.personal_risk.anomaly_detector import PersonalRiskDetector

# Singleton detector instance
_detector = PersonalRiskDetector()


def analyze_personal_risk(
    sender_id: str,
    amount: float,
    recipient_id: str,
    transaction_history: Optional[List[Dict[str, Any]]] = None,
    balance: float = 0.0,
    transaction_hour: Optional[int] = None,
    recent_tx_count_24h: int = 0,
    context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Analyze personal spending risk for a given transaction.

    Args:
        sender_id: User/account ID of the sender
        amount: Transaction amount in INR
        recipient_id: VPA/ID of the recipient
        transaction_history: List of past transaction dicts with
            {amount, created_at, recipient_vpa}
        balance: Current account balance
        transaction_hour: Hour of day (0-23), auto-detected if None
        recent_tx_count_24h: Number of transactions in last 24 hours
        context: Additional context dict

    Returns:
        Dict with personal_risk_score, risk_level, reasons, model_version
    """
    # Build profile from history
    history = transaction_history or []
    profile = UserSpendProfile.from_transactions(sender_id, history)

    # Run anomaly detection
    result = _detector.analyze(
        profile=profile,
        amount=amount,
        recipient_id=recipient_id,
        balance=balance,
        transaction_hour=transaction_hour,
        recent_tx_count_24h=recent_tx_count_24h
    )

    return {
        "personal_risk_score": result["personal_risk_score"],
        "risk_level": result["risk_level"],
        "reasons": result["reasons"],
        "signal_breakdown": result.get("signal_breakdown", {}),
        "model_version": "personal-v2"
    }


# Quick test
if __name__ == "__main__":
    # Simulate a user with normal spending history
    history = [
        {"amount": 200, "created_at": "2026-08-01T10:00:00Z", "recipient_vpa": "grocery@upi"},
        {"amount": 350, "created_at": "2026-08-05T14:30:00Z", "recipient_vpa": "grocery@upi"},
        {"amount": 150, "created_at": "2026-08-10T09:00:00Z", "recipient_vpa": "electricity@upi"},
        {"amount": 500, "created_at": "2026-08-15T16:00:00Z", "recipient_vpa": "friend@upi"},
        {"amount": 250, "created_at": "2026-08-20T11:00:00Z", "recipient_vpa": "grocery@upi"},
        {"amount": 400, "created_at": "2026-08-22T18:00:00Z", "recipient_vpa": "restaurant@upi"},
        {"amount": 180, "created_at": "2026-08-25T12:00:00Z", "recipient_vpa": "grocery@upi"},
        {"amount": 300, "created_at": "2026-08-28T15:00:00Z", "recipient_vpa": "friend@upi"},
    ]

    # Normal transaction
    print("=== Normal Transaction (₹250 to grocery) ===")
    res = analyze_personal_risk("user1", 250, "grocery@upi", history, balance=25000)
    print(f"  Risk: {res['personal_risk_score']} ({res['risk_level']})")
    for r in res["reasons"]:
        print(f"  → {r}")

    # Anomalous transaction
    print("\n=== Anomalous Transaction (₹8000 to unknown) ===")
    res = analyze_personal_risk("user1", 8000, "unknown_seller@upi", history, balance=10000, transaction_hour=2)
    print(f"  Risk: {res['personal_risk_score']} ({res['risk_level']})")
    for r in res["reasons"]:
        print(f"  → {r}")
