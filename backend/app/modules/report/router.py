from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, require_roles
from app.modules.report import service
from app.modules.report.schemas import GenerateReportRequest, ReportResponse

router = APIRouter()

_ALLOWED_ROLES = ["manager", "dispatcher", "admin", "owner"]


@router.get("", response_model=list[ReportResponse])
async def list_reports(
    db: AsyncSession = Depends(get_db),
    _actor=Depends(require_roles(_ALLOWED_ROLES)),
):
    return await service.find_all(db)


@router.post("/generate", response_model=ReportResponse, status_code=201)
async def generate_report(
    payload: GenerateReportRequest,
    db: AsyncSession = Depends(get_db),
    actor=Depends(require_roles(_ALLOWED_ROLES)),
):
    return await service.generate(payload, actor, db)
