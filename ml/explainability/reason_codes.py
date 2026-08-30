"""
Reason Code Generator — Maps feature importance to human-readable reasons.

Provides clear, actionable reason codes for transactions flagged as HIGH or CRITICAL.
"""

from typing import Dict, List, Any, Optional


# Feature → Human-readable label mapping
FEATURE_LABELS = {
    "account_age": "Account Age",
    "transaction_count": "Transaction Volume",
    "incoming_volume": "Incoming Payment Volume",
    "outgoing_volume": "Outgoing Payment Volume",
    "transaction_velocity": "Transaction Speed",
    "unique_senders": "Unique Sender Count",
    "complaint_count": "Fraud Complaints Filed",
    "complaint_rate": "Complaint Rate",
    "successful_transaction_ratio": "Success Rate",
    "refund_ratio": "Refund Rate",
    "suspicious_counterparty_count": "Suspicious Connections",
    "transaction_concentration": "Payment Concentration",
    "incoming_outgoing_ratio": "In/Out Flow Ratio",
    "amount_zscore": "Amount Deviation",
    "time_deviation": "Time-of-Day Anomaly",
    "recipient_familiarity": "Recipient Familiarity",
    "balance_ratio": "Balance Consumption",
    "velocity": "Transaction Velocity Spike",
}

# Reason code templates for each risk signal
REASON_TEMPLATES = {
    "account_age_low": "Recipient account is very new ({value} days old) — new accounts carry higher fraud risk.",
    "complaint_count_high": "Recipient has {value} fraud complaint(s) filed by other users.",
    "complaint_rate_high": "Recipient's complaint rate ({value:.1%}) is significantly above the platform average.",
    "refund_ratio_high": "Recipient has an unusually high refund rate ({value:.1%}), indicating potential delivery issues.",
    "suspicious_counterparty_high": "Recipient is connected to {value} accounts flagged as suspicious in the transaction network.",
    "transaction_concentration_high": "Recipient receives concentrated payments from very few sources ({value:.1%} concentration).",
    "velocity_high": "Recipient's transaction velocity ({value:.1f}/hr) is unusually high, suggesting automated activity.",
    "success_rate_low": "Recipient has a low transaction success rate ({value:.1%}), indicating potential issues.",
    "amount_anomaly": "This transaction amount is unusual based on your spending patterns — {value:.1f}σ deviation.",
    "time_anomaly": "Transaction at unusual hour — this time of day is atypical for your transaction pattern.",
    "new_recipient": "First-time recipient — you have no prior transaction history with this payee.",
    "balance_drain": "This payment would consume {value:.0%} of your available balance.",
}


def generate_reason_codes(
    risk_level: str,
    payee_features: Optional[Dict[str, Any]] = None,
    personal_signals: Optional[Dict[str, float]] = None,
    feature_importances: Optional[Dict[str, float]] = None
) -> List[Dict[str, Any]]:
    """
    Generate structured reason codes for a risk decision.

    Args:
        risk_level: HIGH or CRITICAL
        payee_features: Raw payee feature dict
        personal_signals: Personal risk signal breakdown
        feature_importances: SHAP or model feature importance values

    Returns:
        List of reason code dicts with:
            - code: str (e.g., "RC001")
            - category: str (PAYEE_RISK / PERSONAL_RISK / NETWORK_RISK)
            - severity: str (WARNING / DANGER / CRITICAL)
            - message: str (human-readable)
            - feature: str (underlying feature name)
            - contribution: float (how much this feature contributed to the score)
    """
    codes = []
    code_counter = 1

    if payee_features:
        # Payee risk reason codes
        if payee_features.get("account_age", 999) < 30:
            codes.append(_make_code(
                code_counter, "PAYEE_RISK", "WARNING",
                REASON_TEMPLATES["account_age_low"].format(value=payee_features["account_age"]),
                "account_age", feature_importances
            ))
            code_counter += 1

        if payee_features.get("complaint_count", 0) > 0:
            severity = "CRITICAL" if payee_features["complaint_count"] > 3 else "DANGER"
            codes.append(_make_code(
                code_counter, "PAYEE_RISK", severity,
                REASON_TEMPLATES["complaint_count_high"].format(value=payee_features["complaint_count"]),
                "complaint_count", feature_importances
            ))
            code_counter += 1

        if payee_features.get("complaint_rate", 0) > 0.05:
            codes.append(_make_code(
                code_counter, "PAYEE_RISK", "DANGER",
                REASON_TEMPLATES["complaint_rate_high"].format(value=payee_features["complaint_rate"]),
                "complaint_rate", feature_importances
            ))
            code_counter += 1

        if payee_features.get("refund_ratio", 0) > 0.2:
            codes.append(_make_code(
                code_counter, "PAYEE_RISK", "WARNING",
                REASON_TEMPLATES["refund_ratio_high"].format(value=payee_features["refund_ratio"]),
                "refund_ratio", feature_importances
            ))
            code_counter += 1

        if payee_features.get("suspicious_counterparty_count", 0) > 2:
            codes.append(_make_code(
                code_counter, "NETWORK_RISK", "DANGER",
                REASON_TEMPLATES["suspicious_counterparty_high"].format(
                    value=payee_features["suspicious_counterparty_count"]
                ),
                "suspicious_counterparty_count", feature_importances
            ))
            code_counter += 1

        if payee_features.get("transaction_concentration", 0) > 0.6:
            codes.append(_make_code(
                code_counter, "PAYEE_RISK", "WARNING",
                REASON_TEMPLATES["transaction_concentration_high"].format(
                    value=payee_features["transaction_concentration"]
                ),
                "transaction_concentration", feature_importances
            ))
            code_counter += 1

    if personal_signals:
        if personal_signals.get("amount_zscore", 0) > 40:
            codes.append(_make_code(
                code_counter, "PERSONAL_RISK", "DANGER",
                "This transaction amount is significantly unusual based on your spending history.",
                "amount_zscore", feature_importances
            ))
            code_counter += 1

        if personal_signals.get("time_deviation", 0) > 50:
            codes.append(_make_code(
                code_counter, "PERSONAL_RISK", "WARNING",
                REASON_TEMPLATES["time_anomaly"],
                "time_deviation", feature_importances
            ))
            code_counter += 1

        if personal_signals.get("recipient_familiarity", 0) > 40:
            codes.append(_make_code(
                code_counter, "PERSONAL_RISK", "WARNING",
                REASON_TEMPLATES["new_recipient"],
                "recipient_familiarity", feature_importances
            ))
            code_counter += 1

        if personal_signals.get("balance_ratio", 0) > 50:
            codes.append(_make_code(
                code_counter, "PERSONAL_RISK", "DANGER",
                "This payment would consume a significant portion of your available balance.",
                "balance_ratio", feature_importances
            ))
            code_counter += 1

    return codes


def _make_code(
    counter: int,
    category: str,
    severity: str,
    message: str,
    feature: str,
    importances: Optional[Dict[str, float]] = None
) -> Dict[str, Any]:
    """Create a structured reason code dict."""
    return {
        "code": f"RC{counter:03d}",
        "category": category,
        "severity": severity,
        "message": message,
        "feature": feature,
        "feature_label": FEATURE_LABELS.get(feature, feature),
        "contribution": importances.get(feature, 0.0) if importances else 0.0
    }
