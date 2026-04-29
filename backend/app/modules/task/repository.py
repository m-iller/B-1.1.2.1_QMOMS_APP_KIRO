from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.task.models import Task

async def get_all_tasks(machine_id: str | None, state: str | None, db: AsyncSession) -> list[Task]:
    q = select(Task)
    if machine_id:
        q = q.where(Task.machine_id == machine_id)
    if state:
        q = q.where(Task.state == state)
    result = await db.execute(q)
    return list(result.scalars().all())

async def get_task_by_id(task_id: str, db: AsyncSession) -> Task | None:
    result = await db.execute(select(Task).where(Task.id == task_id))
    return result.scalar_one_or_none()

async def create_task(machine_id, title, description, priority, deadline, created_by, db: AsyncSession) -> Task:
    if isinstance(deadline, str):
        deadline = datetime.fromisoformat(deadline.replace("Z", "+00:00"))
    task = Task(machine_id=machine_id, title=title, description=description, priority=priority, deadline=deadline, created_by=created_by, state="pending")
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return task

async def update_task_state(task_id: str, state: str, db: AsyncSession) -> Task:
    task = await get_task_by_id(task_id, db)
    task.state = state
    task.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(task)
    return task

async def set_pending_activation(task_id: str, value: bool, db: AsyncSession) -> Task:
    task = await get_task_by_id(task_id, db)
    task.pending_activation = value
    task.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(task)
    return task

async def delete_task(task_id: str, db: AsyncSession) -> None:
    task = await get_task_by_id(task_id, db)
    if task is not None:
        await db.delete(task)
        await db.commit()
