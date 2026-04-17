from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.machine import repository


def resolve_effective_state(
    dispatcher_state: str | None,
    telemetry_state: str | None,
    operator_state: str | None,
) -> tuple[str, bool]:
    conflict_active = (
        dispatcher_state is not None
        and operator_state is not None
        and dispatcher_state != operator_state
    )
    effective_state = dispatcher_state or telemetry_state or operator_state or "idle"
    return effective_state, conflict_active


async def detect_and_handle_conflict(
    machine_id: str,
    actor_role: str,
    db: AsyncSession,
    event_service,
    notification_service,
) -> bool:
    dispatcher_ms = await repository.get_latest_machine_state_by_source(machine_id, "dispatcher", db)
    operator_ms = await repository.get_latest_machine_state_by_source(machine_id, "operator", db)
    telemetry_ms = await repository.get_latest_machine_state_by_source(machine_id, "telemetry", db)

    dispatcher_state = dispatcher_ms.state if dispatcher_ms else None
    operator_state = operator_ms.state if operator_ms else None
    telemetry_state = telemetry_ms.state if telemetry_ms else None

    effective_state, conflict_active = resolve_effective_state(
        dispatcher_state, telemetry_state, operator_state
    )

    if conflict_active:
        await repository.insert_conflict(machine_id, dispatcher_state, operator_state, db)
        await repository.update_machine_conflict(machine_id, True, db)

        if event_service is not None:
            try:
                await event_service.emit(
                    machine_id=machine_id,
                    event_type="CONFLICT_DETECTED",
                    payload={
                        "dispatcher_state": dispatcher_state,
                        "operator_state": operator_state,
                    },
                    db=db,
                )
            except Exception:
                pass

        if notification_service is not None:
            try:
                machine = await repository.get_machine_by_id(machine_id, db)
                if machine and machine.assigned_dispatcher_id:
                    await notification_service.create(
                        user_id=machine.assigned_dispatcher_id,
                        type_="CONFLICT_DETECTED",
                        payload={
                            "machine_id": machine_id,
                            "dispatcher_state": dispatcher_state,
                            "operator_state": operator_state,
                        },
                        db=db,
                    )
            except Exception:
                pass
    else:
        await repository.update_machine_state(machine_id, effective_state, db)
        await repository.update_machine_conflict(machine_id, False, db)

    return conflict_active
