from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db
from app.modules.analytics.schemas import DashboardAnalytics
from app.modules.analytics.service import compute_dashboard

router = APIRouter()


@router.get("/analytics/dashboard", response_model=DashboardAnalytics)
async def get_dashboard_analytics(
    db: AsyncSession = Depends(get_db),
    _actor=Depends(get_current_user),
) -> DashboardAnalytics:
    """
    Returns all dashboard analytics metrics.
    Fields marked [simulated] in the schema are estimated where real data is unavailable.
    """
    return await compute_dashboard(db)
