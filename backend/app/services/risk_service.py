import os
import sys
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.models.payee_reputation import PayeeReputation
from backend.app.models.transaction import Transaction
from backend.app.models.account import Account
from backend.app.repositories.payee_repo import PayeeRepository
from backend.app.repositories.account_repo import AccountRepository
from backend.app.schemas.risk import RiskAnalysisRequest, RiskAnalysisResponse

# Import Reddy's ML payee risk model
try:
    from ml.payee_risk.api import analyze_payee, PayeeRiskService
    _has_payee_ml = True
except ImportError:
    try:
        sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))
        from ml.payee_risk.api import analyze_payee, PayeeRiskService
        _has_payee_ml = True
    except Exception as e:
        logger.warning(f"Payee ML module import fallback active: {e}")
        _has_payee_ml = False


class RiskService:
    def __init__(self, db: Session):
        self.db = db
        self.payee_repo = PayeeRepository(db)
        self.account_repo = AccountRepository(db)

    def evaluate_personal_risk(
        self,
        sender_id: str,
        amount: float,
        recipient_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Tuple[float, List[str]]:
        reasons = []
        
        account = self.account_repo.get_by_user_id(sender_id) or self.account_repo.get(sender_id) or self.account_repo.get_by_upi_id(sender_id)
        base_risk = 10.0
        
        if account:
            prev_txs = self.db.query(Transaction).filter(
                Transaction.sender_account_id == account.id,
                Transaction.status.in_(["COMPLETED", "RELEASED"])
            ).all()
            
            if prev_txs:
                avg_amt = sum(t.amount for t in prev_txs) / len(prev_txs)
                if amount > avg_amt * 5 and amount > 5000:
                    base_risk += 45.0
                    reasons.append(f"Transfer amount ₹{amount:.2f} is significantly higher than your typical average (₹{avg_amt:.2f}).")
                elif amount > avg_amt * 2.5:
                    base_risk += 20.0
                    reasons.append(f"Transfer amount ₹{amount:.2f} is above your standard transfer volume.")
            else:
                if amount > 5000:
                    base_risk += 35.0
                    reasons.append("High-value initial transfer on simulated account.")
                    
            if account.balance > 0 and (amount / account.balance) > 0.6:
                base_risk += 25.0
                reasons.append("Payment consumes over 60% of available account balance.")

        if amount >= 9000:
            base_risk = max(base_risk, 82.0)
            if not any("higher than" in r for r in reasons):
                reasons.append(f"Large transaction anomaly: ₹{amount:.2f} exceeds high-risk behavioral baseline.")
        elif amount >= 5000:
            base_risk = max(base_risk, 55.0)

        personal_risk = min(max(base_risk, 5.0), 98.0)
        return personal_risk, reasons

    def evaluate_payee_risk(
        self,
        recipient_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Tuple[float, List[str], str, float]:
        reasons = []
        payee_vpa = recipient_id
        
        payee_rep = self.payee_repo.get_by_vpa(payee_vpa)
        
        if _has_payee_ml:
            try:
                tx_context = context.copy() if context else {}
                if "record" not in tx_context:
                    rep_score = payee_rep.reputation_score if payee_rep else 80.0
                    reported = payee_rep.reported_count if payee_rep else 0
                    total_tx = payee_rep.total_transactions if payee_rep else 15
                    
                    is_suspicious = rep_score < 40 or reported > 0 or "suspicious" in payee_vpa.lower() or "scam" in payee_vpa.lower()
                    
                    record = {
                        "payee_id": payee_vpa,
                        "account_age": 180 if not is_suspicious else 12,
                        "transaction_count": total_tx,
                        "incoming_volume": float(total_tx * 500),
                        "outgoing_volume": float(total_tx * 450) if is_suspicious else float(total_tx * 50),
                        "transaction_velocity": 1.5 if not is_suspicious else 25.0,
                        "unique_senders": max(1, total_tx - 2),
                        "complaint_count": reported if reported > 0 else (5 if is_suspicious else 0),
                        "complaint_rate": 0.0 if not is_suspicious else (reported / max(total_tx, 1)),
                        "successful_transaction_ratio": 0.98 if not is_suspicious else 0.40,
                        "refund_ratio": 0.02 if not is_suspicious else 0.45,
                        "suspicious_counterparty_count": 0 if not is_suspicious else 6,
                        "transaction_concentration": 0.15 if not is_suspicious else 0.85,
                        "incoming_outgoing_ratio": 1.1 if not is_suspicious else 1.01,
                        "profile_type": "LEGITIMATE_MERCHANT" if not is_suspicious else "SUSPICIOUS_ACCOUNT"
                    }
                    tx_context["record"] = record
                
                ml_res = analyze_payee(payee_vpa, tx_context)
                ml_payee_risk = float(ml_res["payee_risk"])
                ml_reasons = ml_res.get("reasons", [])
                ml_version = ml_res.get("model_version", "payee-v1")
                ml_conf = float(ml_res.get("confidence", 0.9))
                
                if payee_rep and payee_rep.reported_count > 0:
                    ml_payee_risk = min(100.0, ml_payee_risk + (payee_rep.reported_count * 8.0))
                    if f"{payee_rep.reported_count} user fraud report(s)" not in ml_reasons:
                        ml_reasons.append(f"Recipient has {payee_rep.reported_count} active fraud report(s) on record.")

                return ml_payee_risk, ml_reasons, ml_version, ml_conf
            except Exception as e:
                logger.warning(f"Error calling analyze_payee: {e}. Falling back to DB reputation.")

        if payee_rep:
            db_risk = payee_rep.risk_score
            if payee_rep.reported_count > 0:
                reasons.append(f"Recipient has {payee_rep.reported_count} fraud report(s) submitted by other users.")
            if db_risk > 60:
                reasons.append(f"Recipient reputation score is low ({payee_rep.reputation_score:.1f}/100).")
            return db_risk, reasons, "payee-db-v1", 0.85

        return 20.0, ["New recipient with no prior transaction history."], "payee-default-v1", 0.70

    def analyze_transaction(self, req: RiskAnalysisRequest) -> RiskAnalysisResponse:
        personal_risk, personal_reasons = self.evaluate_personal_risk(
            sender_id=req.sender_id,
            amount=req.amount,
            recipient_id=req.recipient_id,
            context=req.context
        )

        payee_risk, payee_reasons, model_ver, confidence = self.evaluate_payee_risk(
            recipient_id=req.recipient_id,
            context=req.context
        )

        higher_signal = max(personal_risk, payee_risk)
        lower_signal = min(personal_risk, payee_risk)
        overall_risk = round((higher_signal * 0.65) + (lower_signal * 0.35), 1)
        
        all_reasons = personal_reasons + payee_reasons
        if not all_reasons:
            all_reasons.append("Standard transaction within normal behavioral and recipient risk limits.")

        if overall_risk < 40.0:
            risk_level = "LOW"
            decision = "ALLOW"
            requires_confirmation = False
            requires_hold = False
        elif overall_risk < 70.0:
            risk_level = "MEDIUM"
            decision = "WARN"
            requires_confirmation = True
            requires_hold = False
        elif overall_risk < 92.0:
            risk_level = "HIGH"
            decision = "HOLD"
            requires_confirmation = True
            requires_hold = True
        else:
            risk_level = "CRITICAL"
            decision = "HOLD"
            requires_confirmation = True
            requires_hold = True

        return RiskAnalysisResponse(
            personal_risk=round(personal_risk, 1),
            payee_risk=round(payee_risk, 1),
            overall_risk=overall_risk,
            risk_level=risk_level,
            decision=decision,
            requires_confirmation=requires_confirmation,
            requires_hold=requires_hold,
            reasons=all_reasons,
            model_version=f"{model_ver}+personal-v1"
        )
