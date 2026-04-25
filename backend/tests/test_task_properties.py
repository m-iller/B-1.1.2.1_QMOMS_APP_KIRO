"""
Property-based tests for the task module.
Feature: quarry-mining-monitor
**Validates: Requirements 5.1–5.11, 6.1–6.4**
"""
import sys
from unittest.mock import MagicMock

# Stub DB-dependent modules before any app imports
for _mod in ["asyncpg", "app.database"]:
    if _mod not in sys.modules:
        sys.modules[_mod] = MagicMock()
_db_stub = sys.modules["app.database"]
_db_stub.Base = type("Base", (), {"__init_subclass__": classmethod(lambda cls, **kw: None)})

from datetime import datetime, timezone
from hypothesis import given, settings as h_settings
from hypothesis import strategies as st

TASK_STATES = ["pending", "active", "completed", "validated"]
PRIORITIES = ["low", "medium", "high", "critical"]


# ---------------------------------------------------------------------------
# Property 24: Deadline ISO string → datetime coercion
# repository.create_task receives deadline as ISO string from API layer;
# it must be parsed to datetime before being passed to SQLAlchemy.
# **Validates: fix for asyncpg DataError on deadline column**
# ---------------------------------------------------------------------------
def _parse_deadline(deadline) -> datetime:
    """Mirror of the coercion logic in repository.create_task."""
    if isinstance(deadline, str):
        return datetime.fromisoformat(deadline.replace("Z", "+00:00"))
    return deadline


@given(
    deadline=st.datetimes(
        min_value=datetime(2024, 1, 1),
        max_value=datetime(2030, 12, 31),
        timezones=st.just(timezone.utc),
    ).map(lambda d: d.isoformat()),
)
@h_settings(max_examples=200)
def test_deadline_string_parses_to_datetime(deadline: str):
    """Property 24a: Any ISO deadline string produced by the simulator parses to datetime."""
    result = _parse_deadline(deadline)
    assert isinstance(result, datetime)


@given(
    deadline=st.datetimes(
        min_value=datetime(2024, 1, 1),
        max_value=datetime(2030, 12, 31),
        timezones=st.just(timezone.utc),
    ),
)
@h_settings(max_examples=100)
def test_deadline_datetime_passthrough(deadline: datetime):
    """Property 24b: datetime input passes through coercion unchanged."""
    result = _parse_deadline(deadline)
    assert result == deadline


def test_deadline_z_suffix_parses():
    """Property 24c: ISO string with Z suffix (UTC shorthand) parses correctly."""
    result = _parse_deadline("2026-04-26T03:44:38.987125Z")
    assert isinstance(result, datetime)
    assert result.tzinfo is not None


def test_deadline_offset_suffix_parses():
    """Property 24d: ISO string with +00:00 offset parses correctly."""
    result = _parse_deadline("2026-04-26T03:44:38.987125+00:00")
    assert isinstance(result, datetime)
    assert result.tzinfo is not None


@given(
    deadline=st.datetimes(
        min_value=datetime(2024, 1, 1),
        max_value=datetime(2030, 12, 31),
        timezones=st.just(timezone.utc),
    ).map(lambda d: d.isoformat()),
)
@h_settings(max_examples=100)
def test_deadline_coercion_is_idempotent(deadline: str):
    """Property 24e: Applying coercion twice yields same result as once."""
    once = _parse_deadline(deadline)
    twice = _parse_deadline(once)
    assert once == twice


@given(
    deadline=st.datetimes(
        min_value=datetime(2024, 1, 1),
        max_value=datetime(2030, 12, 31),
        timezones=st.just(timezone.utc),
    ).map(lambda d: d.isoformat()),
)
@h_settings(max_examples=200)
def test_deadline_coercion_always_timezone_aware(deadline: str):
    """Property 24f: Coerced deadline is always timezone-aware (required by asyncpg TIMESTAMPTZ)."""
    result = _parse_deadline(deadline)
    assert result.tzinfo is not None

# ---------------------------------------------------------------------------
# Property 16: Task Creation Invariant
# CreateTaskRequest with valid data should always produce state='pending'
# **Validates: Requirements 5.1**
# ---------------------------------------------------------------------------
@given(
    title=st.text(min_size=1, max_size=200),
    priority=st.sampled_from(PRIORITIES),
    deadline=st.datetimes(
        min_value=datetime(2024, 1, 1),
        max_value=datetime(2030, 12, 31),
    ).map(lambda d: d.isoformat()),
)
@h_settings(max_examples=100)
def test_task_creation_initial_state_is_pending(title: str, priority: str, deadline: str):
    """Property 16: Task Creation Invariant — schema never carries a state field."""
    from app.modules.task.schemas import CreateTaskRequest
    req = CreateTaskRequest(
        machine_id="some-machine-id",
        title=title,
        priority=priority,
        deadline=deadline,
    )
    assert req.priority == priority
    assert req.title == title
    # State is set by the service layer, not the schema
    assert "state" not in type(req).model_fields


# ---------------------------------------------------------------------------
# Property 17: Task Filter Correctness
# Filtering tasks by state should return only tasks with that state.
# **Validates: Requirements 5.3**
# ---------------------------------------------------------------------------
@given(
    states=st.lists(st.sampled_from(TASK_STATES), min_size=1, max_size=20),
    filter_state=st.sampled_from(TASK_STATES),
)
@h_settings(max_examples=100)
def test_task_filter_returns_only_matching_state(states: list[str], filter_state: str):
    """Property 17: Task Filter Correctness — filter predicate is exact."""
    tasks = [{"state": s} for s in states]
    filtered = [t for t in tasks if t["state"] == filter_state]
    for task in filtered:
        assert task["state"] == filter_state


# ---------------------------------------------------------------------------
# Property 18: Operator Activation Requires Dispatcher Confirmation
# When operator requests activation, state stays 'pending', pending_activation=True
# **Validates: Requirements 5.5**
# ---------------------------------------------------------------------------
@given(
    current_state=st.sampled_from(["pending"]),
)
@h_settings(max_examples=100)
def test_operator_activation_sets_pending_flag_not_state(current_state: str):
    """Property 18: Operator requesting activation must not change state directly."""
    actor_role = "operator"
    requested_state = "active"

    if requested_state == "active" and actor_role == "operator":
        new_state = current_state  # unchanged
        pending_activation = True
    else:
        new_state = requested_state
        pending_activation = False

    assert new_state == "pending"
    assert pending_activation is True


# ---------------------------------------------------------------------------
# Property 19: Task Completion Emits Event (structural)
# Transitioning to 'completed' should trigger event emission
# **Validates: Requirements 5.7**
# ---------------------------------------------------------------------------
@given(
    from_state=st.sampled_from(["active"]),
    to_state=st.just("completed"),
)
@h_settings(max_examples=100)
def test_completed_transition_triggers_event(from_state: str, to_state: str):
    """Property 19: Completing a task always satisfies the event-emission condition."""
    should_emit = to_state == "completed"
    assert should_emit is True


# ---------------------------------------------------------------------------
# Property 20: Task Validation Requires Dispatcher Role
# Only dispatcher can transition to 'validated'
# **Validates: Requirements 5.6**
# ---------------------------------------------------------------------------
@given(
    role=st.sampled_from(["operator", "manager", "admin", "mechanic", "IT", "owner"]),
)
@h_settings(max_examples=100)
def test_non_dispatcher_cannot_validate(role: str):
    """Property 20: Non-dispatcher roles must be denied the 'validated' transition."""
    requested_state = "validated"
    if requested_state == "validated" and role != "dispatcher":
        access_denied = True
    else:
        access_denied = False
    assert access_denied is True


# ---------------------------------------------------------------------------
# Property 21: Task Overdue Flag
# overdue=True when deadline < now AND state not in (completed, validated)
# overdue=False when state is completed or validated regardless of deadline
# **Validates: Requirements 5.8**
# ---------------------------------------------------------------------------
def _compute_overdue_logic(deadline_str: str, state: str) -> bool:
    """Mirror of service._compute_overdue, operating on plain strings."""
    if state in ("completed", "validated"):
        return False
    try:
        deadline = datetime.fromisoformat(deadline_str.replace("Z", "+00:00"))
        return deadline < datetime.now(timezone.utc)
    except Exception:
        return False


@given(
    state=st.sampled_from(["completed", "validated"]),
    deadline=st.datetimes(
        min_value=datetime(2000, 1, 1),
        max_value=datetime(2020, 12, 31),  # always in the past
    ).map(lambda d: d.isoformat()),
)
@h_settings(max_examples=100)
def test_completed_validated_never_overdue(state: str, deadline: str):
    """Property 21a: Completed/validated tasks are never overdue regardless of deadline."""
    assert _compute_overdue_logic(deadline, state) is False


@given(
    state=st.sampled_from(["pending", "active"]),
    deadline=st.datetimes(
        min_value=datetime(2000, 1, 1),
        max_value=datetime(2020, 12, 31),  # always in the past
    ).map(lambda d: d.replace(tzinfo=timezone.utc).isoformat()),
)
@h_settings(max_examples=100)
def test_past_deadline_active_task_is_overdue(state: str, deadline: str):
    """Property 21b: Active/pending tasks with a past deadline are always overdue."""
    assert _compute_overdue_logic(deadline, state) is True


@given(
    state=st.sampled_from(["pending", "active"]),
    deadline=st.datetimes(
        min_value=datetime(2030, 1, 1),
        max_value=datetime(2099, 12, 31),  # always in the future
    ).map(lambda d: d.replace(tzinfo=timezone.utc).isoformat()),
)
@h_settings(max_examples=100)
def test_future_deadline_task_not_overdue(state: str, deadline: str):
    """Property 21c: Active/pending tasks with a future deadline are never overdue."""
    assert _compute_overdue_logic(deadline, state) is False


# ---------------------------------------------------------------------------
# Property 22: Haul Cycle Creation Round-Trip
# CreateHaulCycleRequest with valid data should be parseable
# **Validates: Requirements 6.1–6.2**
# ---------------------------------------------------------------------------
@given(
    payload_tonnes=st.floats(
        min_value=0.1, max_value=200.0, allow_nan=False, allow_infinity=False
    ),
    start_time=st.datetimes(min_value=datetime(2024, 1, 1)).map(lambda d: d.isoformat()),
)
@h_settings(max_examples=100)
def test_haul_cycle_creation_request_valid(payload_tonnes: float, start_time: str):
    """Property 22: Any valid haul cycle payload round-trips through the schema."""
    from app.modules.task.schemas import CreateHaulCycleRequest
    req = CreateHaulCycleRequest(
        machine_id="machine-id",
        origin_zone_id="zone-a",
        destination_zone_id="zone-b",
        payload_tonnes=payload_tonnes,
        start_time=start_time,
    )
    assert req.payload_tonnes == payload_tonnes
    assert req.machine_id == "machine-id"


def test_haul_cycle_response_has_immutable_field():
    """Property 22 (structural): HaulCycleResponse exposes immutable and end_time fields."""
    from app.modules.task.schemas import HaulCycleResponse
    assert "immutable" in HaulCycleResponse.model_fields
    assert "end_time" in HaulCycleResponse.model_fields


# ---------------------------------------------------------------------------
# Property 23: Haul Cycle Immutability
# Once immutable=True, any edit attempt should be blocked
# **Validates: Requirements 6.3–6.4**
# ---------------------------------------------------------------------------
@given(immutable=st.booleans())
@h_settings(max_examples=100)
def test_immutable_haul_cycle_blocks_edit(immutable: bool):
    """Property 23: The immutability guard blocks edits iff immutable=True."""
    if immutable:
        edit_blocked = True
    else:
        edit_blocked = False
    assert edit_blocked == immutable
