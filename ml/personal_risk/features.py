"""
Personal risk feature engineering.

This module converts raw transaction and user information into
numerical features used by the personal risk model.
"""

from typing import Dict, Any


def build_personal_features(transaction: Dict[str, Any]) -> Dict[str, float]:
    """
    Build numerical risk features from transaction data.

    Expected transaction fields (optional):

    amount:
        Current transaction amount.

    average_amount:
        User's historical average transaction amount.

    transactions_last_hour:
        Number of transactions made in the last hour.

    failed_transactions:
        Number of recent failed transactions.

    new_device:
        True if the transaction comes from an unknown device.

    unusual_location:
        True if the transaction comes from an unusual location.

    unusual_hour:
        True if the transaction happens at an unusual time.
    """

    amount = float(transaction.get("amount", 0))
    average_amount = float(transaction.get("average_amount", 1))

    # Prevent division by zero.
    if average_amount <= 0:
        average_amount = 1

    amount_ratio = amount / average_amount

    transactions_last_hour = float(
        transaction.get("transactions_last_hour", 0)
    )

    failed_transactions = float(
        transaction.get("failed_transactions", 0)
    )

    new_device = float(
        bool(transaction.get("new_device", False))
    )

    unusual_location = float(
        bool(transaction.get("unusual_location", False))
    )

    unusual_hour = float(
        bool(transaction.get("unusual_hour", False))
    )

    return {
        "amount_ratio": amount_ratio,
        "transactions_last_hour": transactions_last_hour,
        "failed_transactions": failed_transactions,
        "new_device": new_device,
        "unusual_location": unusual_location,
        "unusual_hour": unusual_hour,
    }