from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.schemas.risk import RiskAnalysisRequest, RiskAnalysisResponse
from backend.app.services.risk_service import RiskService

router = APIRouter()


@router.post("/analyze", response_model=RiskAnalysisResponse)
def analyze_risk(
    req: RiskAnalysisRequest,
    db: Session = Depends(get_db)
):
    """
    M5 ML Integration Contract:
    Analyzes transaction risk by combining personal risk assessment
    with Reddy's ML Payee Risk Intelligence engine.
    """
    risk_service = RiskService(db)
    return risk_service.analyze_transaction(req)
