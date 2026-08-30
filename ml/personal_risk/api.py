"""
Personal Risk API.

This is the public interface used by other parts of the project
to calculate the risk associated with the person initiating
a transaction.
"""

from typing import Dict, Any

from ml.personal_risk.model import calculate_personal_risk


def analyze_personal_risk(transaction: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze the personal risk of a transaction.

    Args:
        transaction:
            Dictionary containing transaction and user behaviour data.

    Returns:
        Dictionary containing:
            - personal_risk: score from 0 to 100
            - risk_level: LOW, MEDIUM, or HIGH
            - features: calculated risk features
    """

    return calculate_personal_risk(transaction)