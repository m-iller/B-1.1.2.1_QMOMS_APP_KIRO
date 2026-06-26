"""
Property-based tests for multiple conflicts resolution bugfix.
Bugfix: multiple-conflicts-resolution-fix
"""
import asyncio
import sys
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone

import pytest
from hypothesis import given, settings as h_settings
from hypothesis import strategies as st

# Stub out asyncpg-dependent modules before any app imports trigger DB engine creation
for _mod in [
    "asyncpg",
    "app.database",
]:
    if _mod not in sys.modules:
        sys.modules[_mod] = MagicMock()

# Provide a minimal Base stub so models can be imported without a real DB
import types as _types
_db_stub = sys.modules["app.database"]
_db_stub.Base = type("Base", (), {"__init_subclass__": classmethod(lambda cls, **kw: None)})

from app.modules.machine.models import Conflict, Machine


# ---------------------------------------------------------------------------
# Property 1: Bug Condition - Multiple Conflicts Wrong Resolution
# **Validates: Requirements 1.1, 1.2, 1.3, 2.1, 2.2, 2.4**
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_multiple_conflicts_wrong_resolution_bug_condition():
    """
    **Validates: Requirements 1.1, 1.2, 1.3, 2.1, 2.2, 2.4**
    
    Bug Condition Exploration Test - EXPECTED TO FAIL on unfixed code.
    
    This test demonstrates the bug: when multiple unresolved conflicts exist,
    resolve_conflict resolves the wrong conflict (first from query) instead of
    the specific conflict identified by conflict_id.
    
    Setup: Create machine with 3 unresolved conflicts (A, B, C)
    Action: Attempt to resolve conflict C by providing its conflict_id
    Expected behavior: Conflict C should be marked as resolved
    Actual buggy behavior: Conflict A (first from query) is marked as resolved
    """
    from app.modules.machine import repository, service
    
    # Mock database session
    db = AsyncMock()
    
    # Create mock actor (dispatcher)
    actor = MagicMock()
    actor.id = "user-123"
    actor.role = "dispatcher"
    
    # Create mock machine
    machine_id = "machine-001"
    machine = MagicMock(spec=Machine)
    machine.id = machine_id
    machine.name = "test-machine"
    machine.type = "excavator"
    machine.description = None
    machine.current_state = "idle"
    machine.conflict_active = True
    machine.enabled_sensors = ["engine_temp"]
    machine.assigned_dispatcher_id = None
    machine.current_zone_id = None
    machine.pos_x = None
    machine.pos_y = None
    machine.created_at = datetime.now(timezone.utc)
    machine.updated_at = datetime.now(timezone.utc)
    
    # Create 3 unresolved conflicts (A, B, C) in order
    # IMPORTANT: Give them DIFFERENT states so we can detect the bug
    conflict_a = MagicMock(spec=Conflict)
    conflict_a.id = "conflict-A"
    conflict_a.machine_id = machine_id
    conflict_a.dispatcher_state = "idle"  # Different from conflict C
    conflict_a.operator_state = "maintenance"
    conflict_a.resolved = False
    conflict_a.resolved_by_user_id = None
    conflict_a.resolved_at = None
    conflict_a.created_at = datetime.now(timezone.utc).isoformat()
    
    conflict_b = MagicMock(spec=Conflict)
    conflict_b.id = "conflict-B"
    conflict_b.machine_id = machine_id
    conflict_b.dispatcher_state = "breakdown"  # Different from conflict C
    conflict_b.operator_state = "idle"
    conflict_b.resolved = False
    conflict_b.resolved_by_user_id = None
    conflict_b.resolved_at = None
    conflict_b.created_at = datetime.now(timezone.utc).isoformat()
    
    conflict_c = MagicMock(spec=Conflict)
    conflict_c.id = "conflict-C"
    conflict_c.machine_id = machine_id
    conflict_c.dispatcher_state = "operating"  # Different from A and B
    conflict_c.operator_state = "maintenance"
    conflict_c.resolved = False
    conflict_c.resolved_by_user_id = None
    conflict_c.resolved_at = None
    conflict_c.created_at = datetime.now(timezone.utc).isoformat()
    
    # Mock repository functions
    async def mock_get_machine_by_id(mid, db_session):
        return machine if mid == machine_id else None
    
    async def mock_get_active_conflict(mid, db_session):
        # BUG: Returns first conflict arbitrarily, not the one requested
        return conflict_a  # Always returns conflict A (first)
    
    async def mock_resolve_conflict(cid, user_id, db_session):
        # This gets called with whatever conflict_id is passed to it
        # but because get_active_conflict returns conflict_a,
        # this will be called with conflict_a.id on buggy code
        if cid == "conflict-A":
            conflict_a.resolved = True
            conflict_a.resolved_by_user_id = user_id
            conflict_a.resolved_at = datetime.now(timezone.utc)
            return conflict_a
        elif cid == "conflict-B":
            conflict_b.resolved = True
            conflict_b.resolved_by_user_id = user_id
            conflict_b.resolved_at = datetime.now(timezone.utc)
            return conflict_b
        elif cid == "conflict-C":
            conflict_c.resolved = True
            conflict_c.resolved_by_user_id = user_id
            conflict_c.resolved_at = datetime.now(timezone.utc)
            return conflict_c
        return None
    
    async def mock_update_machine_state(mid, state, db_session):
        machine.current_state = state
        return machine
    
    async def mock_update_machine_conflict(mid, active, db_session):
        machine.conflict_active = active
    
    # Patch the repository functions
    repository.get_machine_by_id = mock_get_machine_by_id
    repository.get_active_conflict = mock_get_active_conflict
    repository.resolve_conflict = mock_resolve_conflict
    repository.update_machine_state = mock_update_machine_state
    repository.update_machine_conflict = mock_update_machine_conflict
    
    # Mock event service (optional dependency)
    event_service = None
    
    # ACTION: Attempt to resolve conflict C (third conflict) by its ID
    conflict_id_to_resolve = "conflict-C"
    resolution = "dispatcher"  # Choose dispatcher state
    
    # Call the buggy resolve_conflict function
    await service.resolve_conflict(
        machine_id=machine_id,
        conflict_id=conflict_id_to_resolve,  # We explicitly request conflict C
        resolution=resolution,
        actor=actor,
        db=db,
        event_service=event_service,
    )
    
    # ASSERTIONS: Verify the EXPECTED BEHAVIOR (what should happen after fix)
    # These assertions will FAIL on unfixed code, demonstrating the bug
    
    # The bug is more subtle than expected:
    # - Conflict C IS marked as resolved (correct)
    # - BUT the machine state is set to conflict A's winning state (WRONG!)
    # - It should be set to conflict C's winning state
    
    # Expected: Machine state should be set to conflict C's dispatcher_state
    # (since we chose resolution='dispatcher')
    expected_state = conflict_c.dispatcher_state  # "operating"
    actual_state = machine.current_state
    
    assert actual_state == expected_state, (
        f"Bug detected: When resolving conflict C (ID: {conflict_id_to_resolve}) with resolution='dispatcher', "
        f"machine state should be set to conflict C's dispatcher_state ('{expected_state}'), "
        f"but it was set to '{actual_state}' instead. "
        f"This happened because get_active_conflict retrieved conflict A, "
        f"so winning_state was computed from conflict A's states ('{conflict_a.dispatcher_state}'), "
        f"even though conflict C was the one being resolved. "
        f"\n"
        f"Conflict A dispatcher_state: {conflict_a.dispatcher_state}, "
        f"Conflict C dispatcher_state: {conflict_c.dispatcher_state}"
    )


# ---------------------------------------------------------------------------
# Property 2: Preservation - Single Conflict Resolution Behavior
# **Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5**
# ---------------------------------------------------------------------------

# Strategy for generating valid machine states
machine_states = st.sampled_from(["idle", "operating", "maintenance", "breakdown"])

# Strategy for generating resolution choices
resolution_choices = st.sampled_from(["dispatcher", "operator"])

# Strategy for generating actor roles
actor_roles = st.sampled_from(["dispatcher", "dev"])


@pytest.mark.asyncio
@given(
    dispatcher_state=machine_states,
    operator_state=machine_states,
    resolution=resolution_choices,
    actor_role=actor_roles,
)
@h_settings(max_examples=50, deadline=None)
async def test_single_conflict_resolution_preservation(
    dispatcher_state: str,
    operator_state: str,
    resolution: str,
    actor_role: str,
):
    """
    **Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5**
    
    Preservation Property Test - EXPECTED TO PASS on unfixed code.
    
    This test verifies that single conflict resolution works correctly on the
    unfixed code. It tests the baseline behavior that must be preserved after
    the fix.
    
    Property: For machines with exactly 1 unresolved conflict, resolving by
    conflict_id succeeds and:
    - Machine current_state is updated to the winning state
    - Conflict record is marked with resolved=True, resolved_by_user_id, and resolved_at
    - After resolving the last conflict, machine.conflict_active is set to False
    
    This test generates many test cases across different state combinations,
    resolutions, and actor roles to provide strong guarantees.
    """
    from app.modules.machine import repository, service
    
    # Skip if dispatcher and operator states are the same (no conflict)
    if dispatcher_state == operator_state:
        return
    
    # Mock database session
    db = AsyncMock()
    
    # Create mock actor
    actor = MagicMock()
    actor.id = "user-456"
    actor.role = actor_role
    
    # Create mock machine
    machine_id = "machine-single"
    machine = MagicMock(spec=Machine)
    machine.id = machine_id
    machine.name = "test-machine-single"
    machine.type = "excavator"
    machine.description = None
    machine.current_state = "idle"
    machine.conflict_active = True
    machine.enabled_sensors = ["engine_temp"]
    machine.assigned_dispatcher_id = None
    machine.current_zone_id = None
    machine.pos_x = None
    machine.pos_y = None
    machine.created_at = datetime.now(timezone.utc)
    machine.updated_at = datetime.now(timezone.utc)
    
    # Create ONE unresolved conflict
    conflict = MagicMock(spec=Conflict)
    conflict.id = "conflict-single"
    conflict.machine_id = machine_id
    conflict.dispatcher_state = dispatcher_state
    conflict.operator_state = operator_state
    conflict.resolved = False
    conflict.resolved_by_user_id = None
    conflict.resolved_at = None
    conflict.created_at = datetime.now(timezone.utc).isoformat()
    
    # Mock repository functions
    async def mock_get_machine_by_id(mid, db_session):
        return machine if mid == machine_id else None
    
    async def mock_get_active_conflict(mid, db_session):
        # Returns the only conflict (for single conflict case)
        return conflict if not conflict.resolved else None
    
    async def mock_resolve_conflict(cid, user_id, db_session):
        if cid == conflict.id:
            conflict.resolved = True
            conflict.resolved_by_user_id = user_id
            conflict.resolved_at = datetime.now(timezone.utc)
            return conflict
        return None
    
    async def mock_update_machine_state(mid, state, db_session):
        machine.current_state = state
        return machine
    
    async def mock_update_machine_conflict(mid, active, db_session):
        machine.conflict_active = active
    
    # Patch the repository functions
    repository.get_machine_by_id = mock_get_machine_by_id
    repository.get_active_conflict = mock_get_active_conflict
    repository.resolve_conflict = mock_resolve_conflict
    repository.update_machine_state = mock_update_machine_state
    repository.update_machine_conflict = mock_update_machine_conflict
    
    # Mock event service (optional dependency)
    event_service = None
    
    # ACTION: Resolve the single conflict
    await service.resolve_conflict(
        machine_id=machine_id,
        conflict_id=conflict.id,
        resolution=resolution,
        actor=actor,
        db=db,
        event_service=event_service,
    )
    
    # ASSERTIONS: Verify preservation of baseline behavior
    
    # 3.1: Conflict is marked as resolved
    assert conflict.resolved is True, (
        f"Expected conflict to be marked as resolved (resolved=True), but got {conflict.resolved}"
    )
    
    # 3.2: Conflict has resolved_by_user_id set
    assert conflict.resolved_by_user_id == actor.id, (
        f"Expected conflict.resolved_by_user_id to be '{actor.id}', but got '{conflict.resolved_by_user_id}'"
    )
    
    # 3.3: Conflict has resolved_at timestamp
    assert conflict.resolved_at is not None, (
        "Expected conflict.resolved_at to be set with a timestamp, but it was None"
    )
    
    # 3.4: Machine state is updated to the winning state
    expected_winning_state = dispatcher_state if resolution == "dispatcher" else operator_state
    assert machine.current_state == expected_winning_state, (
        f"Expected machine.current_state to be '{expected_winning_state}' (resolution='{resolution}'), "
        f"but got '{machine.current_state}'"
    )
    
    # 3.5: After resolving the last (only) conflict, machine.conflict_active is False
    assert machine.conflict_active is False, (
        f"Expected machine.conflict_active to be False after resolving the last conflict, "
        f"but got {machine.conflict_active}"
    )


@pytest.mark.asyncio
async def test_single_conflict_resolution_with_event_emission():
    """
    **Validates: Requirements 3.4**
    
    Preservation test for event emission.
    
    Verifies that MACHINE_STATE_CHANGED event is emitted with conflict
    resolution details when resolving a conflict.
    """
    from app.modules.machine import repository, service
    
    # Mock database session
    db = AsyncMock()
    
    # Create mock actor
    actor = MagicMock()
    actor.id = "user-789"
    actor.role = "dispatcher"
    
    # Create mock machine
    machine_id = "machine-event"
    machine = MagicMock(spec=Machine)
    machine.id = machine_id
    machine.name = "test-machine-event"
    machine.type = "excavator"
    machine.description = None
    machine.current_state = "idle"
    machine.conflict_active = True
    machine.enabled_sensors = ["engine_temp"]
    machine.assigned_dispatcher_id = None
    machine.current_zone_id = None
    machine.pos_x = None
    machine.pos_y = None
    machine.created_at = datetime.now(timezone.utc)
    machine.updated_at = datetime.now(timezone.utc)
    
    # Create ONE unresolved conflict
    conflict = MagicMock(spec=Conflict)
    conflict.id = "conflict-event"
    conflict.machine_id = machine_id
    conflict.dispatcher_state = "operating"
    conflict.operator_state = "maintenance"
    conflict.resolved = False
    conflict.resolved_by_user_id = None
    conflict.resolved_at = None
    
    # Mock repository functions
    async def mock_get_machine_by_id(mid, db_session):
        return machine if mid == machine_id else None
    
    async def mock_get_active_conflict(mid, db_session):
        return conflict if not conflict.resolved else None
    
    async def mock_resolve_conflict(cid, user_id, db_session):
        if cid == conflict.id:
            conflict.resolved = True
            conflict.resolved_by_user_id = user_id
            conflict.resolved_at = datetime.now(timezone.utc)
            return conflict
        return None
    
    async def mock_update_machine_state(mid, state, db_session):
        machine.current_state = state
        return machine
    
    async def mock_update_machine_conflict(mid, active, db_session):
        machine.conflict_active = active
    
    # Patch repository
    repository.get_machine_by_id = mock_get_machine_by_id
    repository.get_active_conflict = mock_get_active_conflict
    repository.resolve_conflict = mock_resolve_conflict
    repository.update_machine_state = mock_update_machine_state
    repository.update_machine_conflict = mock_update_machine_conflict
    
    # Mock event service
    event_service = AsyncMock()
    event_service.emit = AsyncMock()
    
    # ACTION: Resolve the conflict
    resolution = "dispatcher"
    await service.resolve_conflict(
        machine_id=machine_id,
        conflict_id=conflict.id,
        resolution=resolution,
        actor=actor,
        db=db,
        event_service=event_service,
    )
    
    # ASSERTION: Verify event was emitted
    event_service.emit.assert_called_once()
    call_args = event_service.emit.call_args
    
    assert call_args.kwargs["machine_id"] == machine_id
    assert call_args.kwargs["event_type"] == "MACHINE_STATE_CHANGED"
    assert "conflict_resolved" in call_args.kwargs["payload"]
    assert call_args.kwargs["payload"]["conflict_resolved"] is True
    assert call_args.kwargs["payload"]["winning_state"] == "operating"
    assert call_args.kwargs["payload"]["resolution"] == "dispatcher"


if __name__ == "__main__":
    # Allow running the tests directly
    asyncio.run(test_multiple_conflicts_wrong_resolution_bug_condition())
    asyncio.run(test_single_conflict_resolution_with_event_emission())
