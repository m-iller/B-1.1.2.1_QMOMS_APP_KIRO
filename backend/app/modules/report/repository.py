from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.report.models import Report


async def insert_report(shift_id: str, generated_by: str | None, data: dict, db: AsyncSession) -> Report:
    report = Report(shift_id=shift_id, generated_by=generated_by, data=data)
    db.add(report)
    await db.commit()
    await db.refresh(report)
    return report


async def find_all(db: AsyncSession) -> list[Report]:
    result = await db.execute(select(Report).order_by(Report.generated_at.desc()))
    return list(result.scalars().all())


async def find_by_id(report_id: str, db: AsyncSession) -> Report | None:
    result = await db.execute(select(Report).where(Report.id == report_id))
    return result.scalar_one_or_none()
