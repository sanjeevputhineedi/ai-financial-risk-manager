from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.schemas.dashboard import DashboardMetricsResponse
from backend.app.services.dashboard_service import DashboardService

router = APIRouter()


@router.get("/metrics", response_model=DashboardMetricsResponse)
def get_dashboard_metrics(
    db: Session = Depends(get_db)
):
    """
    Checkpoint M13: Dashboard metrics providing live risk distributions,
    held payments summary, and system fraud intelligence statistics.
    """
    dashboard_service = DashboardService(db)
    return dashboard_service.get_metrics()
