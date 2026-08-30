from __future__ import annotations

from ml.payee_risk.api import analyze_payee


def make_decision(personal_risk: float, payee_risk: float) -> dict:
    """
    Combine personal transaction risk and payee risk
    to produce a final fraud decision.
    """

    personal_risk = float(personal_risk)
    payee_risk = float(payee_risk)

    # Weighted final risk score
    final_risk = round(
        (personal_risk * 0.60) +
        (payee_risk * 0.40),
        2
    )

    # Decision rules
    if final_risk >= 80:
        decision = "BLOCK"
    elif final_risk >= 50:
        decision = "REVIEW"
    else:
        decision = "ALLOW"

    return {
        "personal_risk": personal_risk,
        "payee_risk": payee_risk,
        "final_risk": final_risk,
        "decision": decision,
    }


def analyze_transaction(
    personal_risk: float,
    payee_id: str,
    transaction_context: dict,
) -> dict:
    """
    Analyze a transaction by combining Sanjeev's personal-risk score
    with Reddy's Payee Risk API output.
    """

    # Get Payee Risk from Reddy's stable API.
    payee_result = analyze_payee(
        payee_id=payee_id,
        transaction_context=transaction_context,
    )

    # Use the Payee Risk score in Sanjeev's Decision Engine.
    decision_result = make_decision(
        personal_risk=personal_risk,
        payee_risk=payee_result["payee_risk"],
    )

    # Add useful integration information.
    return {
        **decision_result,
        "payee_risk_level": payee_result["risk_level"],
        "payee_confidence": payee_result["confidence"],
        "payee_reasons": payee_result["reasons"],
        "payee_model_version": payee_result["model_version"],
    }