from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.schemas.payee import PayeeRiskResponse, PayeeReputationResponse
from backend.app.services.reputation_service import ReputationService
from backend.app.services.risk_service import RiskService

router = APIRouter()


@router.get("/{id}/risk", response_model=PayeeRiskResponse)
def get_payee_risk(
    id: str,
    db: Session = Depends(get_db)
):
    risk_service = RiskService(db)
    risk_score, reasons, model_ver, conf = risk_service.evaluate_payee_risk(recipient_id=id)
    
    risk_level = "LOW"
    if risk_score >= 90:
        risk_level = "CRITICAL"
    elif risk_score >= 70:
        risk_level = "HIGH"
    elif risk_score >= 40:
        risk_level = "MEDIUM"

    return PayeeRiskResponse(
        payee_vpa=id,
        payee_risk_score=round(risk_score, 1),
        risk_level=risk_level,
        confidence=conf,
        reasons=reasons,
        model_version=model_ver
    )


@router.get("/{id}/reputation", response_model=PayeeReputationResponse)
def get_payee_reputation(
    id: str,
    db: Session = Depends(get_db)
):
    rep_service = ReputationService(db)
    return rep_service.get_payee_reputation(payee_vpa=id)
