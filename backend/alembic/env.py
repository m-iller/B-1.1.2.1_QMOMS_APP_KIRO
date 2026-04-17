import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from app.config import settings
from app.database import Base  # noqa: F401 — ensures Base is populated

# ---------------------------------------------------------------------------
# Import all models so that Base.metadata is fully populated before autogenerate
# ---------------------------------------------------------------------------
from app.modules.auth.models import User  # noqa: F401
from app.modules.event.models import Event, Shift  # noqa: F401
from app.modules.machine.models import Conflict, Machine, MachineState  # noqa: F401
from app.modules.notification.models import Notification  # noqa: F401
from app.modules.report.models import Report  # noqa: F401
from app.modules.task.models import HaulCycle, Task, TaskDependency  # noqa: F401
from app.modules.telemetry.models import Anomaly, TelemetryData  # noqa: F401
from app.modules.zone.models import Zone  # noqa: F401

# ---------------------------------------------------------------------------
# Alembic Config
# ---------------------------------------------------------------------------
config = context.config

# Override sqlalchemy.url from pydantic-settings
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations in 'online' mode using async engine."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
