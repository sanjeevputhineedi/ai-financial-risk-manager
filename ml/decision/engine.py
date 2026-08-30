from __future__ import annotations


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