"""
SHAP Explainer — Checkpoint 11.

Provides SHAP-based feature contributions for the payee risk Random Forest model
and rule-based explanations for the personal risk model.
"""

import os
import pickle
from typing import Dict, List, Any, Optional

from ml.explainability.reason_codes import generate_reason_codes, FEATURE_LABELS

# Try loading SHAP — it's optional
try:
    import shap
    import numpy as np
    _HAS_SHAP = True
except ImportError:
    _HAS_SHAP = False


class SHAPExplainer:
    """
    Provides feature-level explanations using SHAP TreeExplainer for the
    payee risk Random Forest model.
    """

    PAYEE_FEATURE_ORDER = [
        "account_age", "transaction_count", "incoming_volume", "outgoing_volume",
        "transaction_velocity", "unique_senders", "complaint_count", "complaint_rate",
        "successful_transaction_ratio", "refund_ratio", "suspicious_counterparty_count",
        "transaction_concentration", "incoming_outgoing_ratio"
    ]

    def __init__(self, model_path: Optional[str] = None):
        self.model = None
        self.explainer = None

        if model_path is None:
            model_path = os.path.join(
                os.path.dirname(__file__), "..", "..", "models", "payee_risk_model.pkl"
            )

        try:
            if os.path.exists(model_path):
                with open(model_path, "rb") as f:
                    self.model = pickle.load(f)

                if _HAS_SHAP and self.model is not None:
                    self.explainer = shap.TreeExplainer(self.model)
        except Exception:
            pass

    def explain_payee_risk(
        self,
        features: Dict[str, Any],
        payee_risk_score: float,
        risk_level: str
    ) -> Dict[str, Any]:
        """
        Explain a payee risk prediction using SHAP values if available,
        falling back to rule-based explanations.

        Returns:
            {
                "shap_available": bool,
                "top_features": List[Dict],
                "reason_codes": List[Dict],
                "explanation_text": str
            }
        """
        shap_features = {}
        top_features = []

        if self.explainer is not None and _HAS_SHAP:
            try:
                import numpy as np
                # Build feature vector in expected order
                feature_vector = np.array([[
                    float(features.get(f, 0)) for f in self.PAYEE_FEATURE_ORDER
                ]])

                shap_values = self.explainer.shap_values(feature_vector)

                # For binary classifier, take class 1 (fraud) SHAP values
                if isinstance(shap_values, list) and len(shap_values) == 2:
                    sv = shap_values[1][0]
                else:
                    sv = shap_values[0] if len(shap_values.shape) == 1 else shap_values[0]

                # Build feature → SHAP contribution mapping
                for i, fname in enumerate(self.PAYEE_FEATURE_ORDER):
                    shap_features[fname] = float(sv[i])

                # Sort by absolute contribution
                sorted_features = sorted(
                    shap_features.items(),
                    key=lambda x: abs(x[1]),
                    reverse=True
                )

                top_features = [
                    {
                        "feature": fname,
                        "label": FEATURE_LABELS.get(fname, fname),
                        "shap_value": round(val, 4),
                        "direction": "increases risk" if val > 0 else "decreases risk",
                        "raw_value": features.get(fname, "N/A")
                    }
                    for fname, val in sorted_features[:5]
                ]

            except Exception:
                pass

        # Generate reason codes (works with or without SHAP)
        reason_codes = generate_reason_codes(
            risk_level=risk_level,
            payee_features=features,
            feature_importances=shap_features or None
        )

        # Build explanation text
        explanation_parts = []
        if top_features:
            explanation_parts.append("Key factors in this risk assessment:")
            for tf in top_features[:3]:
                explanation_parts.append(
                    f"  • {tf['label']}: {tf['raw_value']} ({tf['direction']}, "
                    f"contribution: {abs(tf['shap_value']):.3f})"
                )
        elif reason_codes:
            explanation_parts.append("Risk factors identified:")
            for rc in reason_codes[:3]:
                explanation_parts.append(f"  • [{rc['severity']}] {rc['message']}")
        else:
            explanation_parts.append(f"Overall payee risk score: {payee_risk_score:.1f} ({risk_level})")

        return {
            "shap_available": bool(top_features),
            "top_features": top_features,
            "reason_codes": reason_codes,
            "explanation_text": "\n".join(explanation_parts)
        }

    def explain_personal_risk(
        self,
        signal_breakdown: Dict[str, float],
        personal_risk_score: float,
        risk_level: str,
        reasons: List[str]
    ) -> Dict[str, Any]:
        """
        Explain a personal risk prediction using signal breakdown.
        Personal risk uses rule-based/statistical signals, not a tree model,
        so SHAP is not applicable — but we provide equivalent transparency.
        """
        # Sort signals by contribution
        sorted_signals = sorted(
            signal_breakdown.items(),
            key=lambda x: x[1],
            reverse=True
        )

        top_signals = [
            {
                "signal": name,
                "label": FEATURE_LABELS.get(name, name.replace("_", " ").title()),
                "contribution": round(val, 2),
                "is_elevated": val > 30
            }
            for name, val in sorted_signals
        ]

        # Generate personal risk reason codes
        reason_codes = generate_reason_codes(
            risk_level=risk_level,
            personal_signals=signal_breakdown
        )

        return {
            "shap_available": False,
            "top_signals": top_signals,
            "reason_codes": reason_codes,
            "reasons": reasons,
            "explanation_text": f"Personal risk: {personal_risk_score:.1f} ({risk_level}). "
                               f"Primary signal: {top_signals[0]['label']} ({top_signals[0]['contribution']:.0f})" if top_signals else ""
        }


# Singleton
_explainer = None


def get_explainer() -> SHAPExplainer:
    global _explainer
    if _explainer is None:
        _explainer = SHAPExplainer()
    return _explainer
