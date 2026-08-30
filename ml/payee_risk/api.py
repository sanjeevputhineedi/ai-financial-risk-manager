"""
Checkpoint R9 — Payee API Contract
=====================================
The single stable entry point Murali's backend calls:

    analyze_payee(payee_id, transaction_context) -> dict

Output contract (STABLE — do not change fields without updating
REDDY_STATE.md, the API docs, and notifying Murali/Sanjeev):

{
  "payee_risk": 74.0,
  "risk_level": "HIGH",
  "confidence": 0.81,
  "reasons": ["high transaction velocity", "multiple recent reports"],
  "model_version": "payee-v1"
}

Internally this wires together:
  R3 baseline model  -> direct_risk
  R4 reputation engine -> reputation_risk
  R6 graph features    -> graph_risk (via R7 combination)
  R8 explainability    -> reasons
"""

from __future__ import annotations
from pathlib import Path

from ml.payee_risk.model import BaselinePayeeRiskModel, score_to_level, MODEL_VERSION
from ml.payee_risk.reputation import ReputationEngine, ReputationState
from ml.payee_risk.risk_integration import combine, graph_features_to_risk
from ml.payee_risk.explainability import generate_reasons
from ml.graph.graph_features import TransactionGraph


class PayeeRiskService:
    """
    Standalone service object. In production this would be a singleton
    loaded once at backend startup; Murali's FastAPI adapter should hold
    one instance and call .analyze_payee() per request.
    """

    def __init__(self, model_path: str = "models/payee_risk_model.pkl"):
        self.model = BaselinePayeeRiskModel.load(model_path) if Path(model_path).exists() else None
        self.reputation_engine = ReputationEngine()
        self.reputation_states: dict[str, ReputationState] = {}   # payee_id -> state (in-memory demo store)
        self.graph = TransactionGraph()

    # --- state management (Murali's DB would back this in production) ---
    def get_or_init_reputation(self, payee_id: str, seed_score: float | None = None) -> ReputationState:
        if payee_id not in self.reputation_states:
            self.reputation_states[payee_id] = self.reputation_engine.init_state(payee_id, seed_score)
        return self.reputation_states[payee_id]

    def record_event(self, payee_id: str, event_type: str, category: str | None = None):
        """Called by Murali's backend when a new report/successful transaction/refund occurs."""
        state = self.get_or_init_reputation(payee_id)
        self.reputation_engine.apply_event(state, event_type, category)
        return state

    # --- the contract ---
    def analyze_payee(self, payee_id: str, transaction_context: dict) -> dict:
        """
        payee_id: recipient identifier
        transaction_context: dict which MUST contain (or the caller must
            supply via `record`) the direct payee features. Minimal shape:
            {
                "record": {...direct behavioral features, see features.py...},
                "graph_features": {...optional, from TransactionGraph.features_for()...}
            }
        """
        record = transaction_context.get("record")
        if record is None:
            raise ValueError("transaction_context must include 'record' with payee features")

        graph_feats = transaction_context.get("graph_features") or self.graph.features_for(payee_id)

        # 1. direct model risk
        if self.model is not None:
            model_out = self.model.predict(record, graph_features=graph_feats)
            direct_risk = model_out["payee_risk_score"]
            raw_features = model_out["_raw_features"]
        else:
            # dev-stub fallback so backend integration isn't blocked while
            # the model is being trained separately (per Murali's M5 spec)
            direct_risk = 30.0
            raw_features = record

        # 2. reputation risk
        rep_state = self.get_or_init_reputation(payee_id, seed_score=direct_risk)
        reputation_risk = rep_state.score

        # 3. graph risk
        graph_risk = graph_features_to_risk(graph_feats)

        # 4. combine (R7)
        combined = combine(direct_risk, reputation_risk, graph_risk)

        # 5. explain (R8)
        reasons = generate_reasons(raw_features)

        # 6. confidence: blend model confidence with reputation evidence confidence
        model_confidence = model_out["confidence"] if self.model is not None else 0.3
        confidence = round((model_confidence + rep_state.confidence) / 2, 3)

        return {
            "payee_risk": combined.combined_payee_risk,
            "risk_level": score_to_level(combined.combined_payee_risk),
            "confidence": confidence,
            "reasons": reasons,
            "model_version": MODEL_VERSION,
            # extended diagnostic breakdown (additive, non-breaking field —
            # safe for Murali/Sanjeev to ignore if not needed)
            "_breakdown": {
                "direct_risk": combined.direct_risk,
                "reputation_risk": combined.reputation_risk,
                "graph_risk": combined.graph_risk,
            },
        }


# module-level convenience function matching the exact contract signature
_default_service: PayeeRiskService | None = None


def analyze_payee(payee_id: str, transaction_context: dict) -> dict:
    global _default_service
    if _default_service is None:
        _default_service = PayeeRiskService()
    return _default_service.analyze_payee(payee_id, transaction_context)


if __name__ == "__main__":
    import pandas as pd
    df = pd.read_csv("data/fraud/synthetic_payees.csv")
    sample = df[df["profile_type"] == "SUSPICIOUS_ACCOUNT"].iloc[0].to_dict()

    result = analyze_payee(sample["payee_id"], {"record": sample})
    import json
    print(json.dumps(result, indent=2))
