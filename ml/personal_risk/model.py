"""
Personal risk scoring model.

This module converts personal transaction features into a
risk score between 0 and 100.
"""

from typing import Dict, Any

from ml.personal_risk.features import build_personal_features


def calculate_personal_risk(transaction: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate the personal risk of a transaction.

    Returns:
        personal_risk: Risk score from 0 to 100.
        risk_level: LOW, MEDIUM, or HIGH.
        features: Features used to calculate the score.
    """

    features = build_personal_features(transaction)

    score = 0.0

    # 1. Transaction amount compared with user's normal amount
    amount_ratio = features["amount_ratio"]

    if amount_ratio >= 5:
        score += 35
    elif amount_ratio >= 3:
        score += 25
    elif amount_ratio >= 2:
        score += 15
    elif amount_ratio >= 1.5:
        score += 5

    # 2. High transaction frequency
    transaction_frequency = features["transactions_last_hour"]

    if transaction_frequency >= 10:
        score += 20
    elif transaction_frequency >= 5:
        score += 10

    # 3. Recent failed transactions
    failed_transactions = features["failed_transactions"]

    if failed_transactions >= 5:
        score += 15
    elif failed_transactions >= 2:
        score += 8

    # 4. New device
    if features["new_device"]:
        score += 10

    # 5. Unusual location
    if features["unusual_location"]:
        score += 10

    # 6. Unusual transaction hour
    if features["unusual_hour"]:
        score += 10

    # Ensure score remains between 0 and 100.
    score = min(round(score, 2), 100.0)

    # Convert numerical score into a risk category.
    if score >= 60:
        risk_level = "HIGH"
    elif score >= 30:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"

    return {
        "personal_risk": score,
        "risk_level": risk_level,
        "features": features,
    }