def generate_reasons(
    personal_features: dict | None = None,
    payee_features: dict | None = None,
    final_risk: float | None = None,
) -> list[str]:
    """
    Generate human-readable explanations for a risk decision.
    """

    reasons = []

    # Personal transaction behaviour
    if personal_features:
        amount_ratio = personal_features.get("amount_ratio", 0)
        transactions_last_hour = personal_features.get(
            "transactions_last_hour", 0
        )
        failed_transactions = personal_features.get(
            "failed_transactions", 0
        )

        if amount_ratio >= 3:
            reasons.append(
                f"Transaction amount is {amount_ratio:.1f}x higher than the usual amount."
            )

        if transactions_last_hour >= 5:
            reasons.append(
                f"High transaction frequency: {transactions_last_hour} transactions in the last hour."
            )

        if failed_transactions >= 2:
            reasons.append(
                f"{failed_transactions} recent failed transactions were detected."
            )

        if personal_features.get("new_device", False):
            reasons.append(
                "Transaction was initiated from a new device."
            )

        if personal_features.get("unusual_location", False):
            reasons.append(
                "Transaction originated from an unusual location."
            )

        if personal_features.get("unusual_hour", False):
            reasons.append(
                "Transaction occurred at an unusual time."
            )

    # Payee behaviour
    if payee_features:
        reputation_risk = payee_features.get("reputation_risk", 0)
        graph_risk = payee_features.get("graph_risk", 0)

        if reputation_risk >= 60:
            reasons.append(
                "Payee has a high-risk reputation based on previous activity."
            )

        if graph_risk >= 60:
            reasons.append(
                "Payee has suspicious connections in the transaction network."
            )

    # Final fallback explanation
    if not reasons:
        if final_risk is not None and final_risk >= 70:
            reasons.append("Overall transaction risk is high.")

        elif final_risk is not None and final_risk >= 40:
            reasons.append("Transaction requires additional review.")

        else:
            reasons.append(
                "No significant risk indicators were detected."
            )

    return reasons