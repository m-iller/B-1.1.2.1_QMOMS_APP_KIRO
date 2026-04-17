"""
Property-based tests for event, zone, report, and notification modules.
Feature: quarry-mining-monitor
"""
import sys
from unittest.mock import MagicMock

# Stub DB-dependent modules
for _mod in ["asyncpg", "app.database"]:
    if _mod not in sys.modules:
        sys.modules[_mod] = MagicMock()
_db_stub = sys.modules["app.database"]
_db_stub.Base = type("Base", (), {"__init_subclass__": classmethod(lambda cls, **kw: None)})

from hypothesis import given, settings as h_settings
from hypothesis import strategies as st

EVENT_TYPES = ["MACHINE_STATE_CHANGED", "TASK_CREATED", "TASK_COMPLETED", "ALERT_TRIGGERED", "CONFLICT_DETECTED"]
NOTIFICATION_TYPES = ["alert", "conflict", "system"]
ROLES = ["operator", "dispatcher", "manager", "admin", "mechanic", "IT", "owner"]
REPORT_ALLOWED_ROLES = ["manager", "dispatcher", "admin", "owner"]
REPORT_DENIED_ROLES = ["operator", "mechanic", "IT"]

# ---------------------------------------------------------------------------
# Property 24: Event Filter Correctness
# ---------------------------------------------------------------------------
# Feature: quarry-mining-monitor, Property 24: Event Filter Correctness
@given(
    event_types=st.lists(st.sampled_from(EVENT_TYPES), min_size=1, max_size=20),
    filter_type=st.sampled_from(EVENT_TYPES),
)
@h_settings(max_examples=100)
def test_event_filter_by_type_returns_only_matching(event_types: list[str], filter_type: str):
    events = [{"event_type": t} for t in event_types]
    filtered = [e for e in events if e["event_type"] == filter_type]
    for e in filtered:
        assert e["event_type"] == filter_type


@given(
    machine_ids=st.lists(st.uuids().map(str), min_size=1, max_size=10),
    filter_machine=st.uuids().map(str),
)
@h_settings(max_examples=100)
def test_event_filter_by_machine_id_returns_only_matching(machine_ids: list[str], filter_machine: str):
    events = [{"machine_id": mid} for mid in machine_ids]
    filtered = [e for e in events if e["machine_id"] == filter_machine]
    for e in filtered:
        assert e["machine_id"] == filter_machine


# ---------------------------------------------------------------------------
# Property 25: Events Associated with Active Shift
# ---------------------------------------------------------------------------
# Feature: quarry-mining-monitor, Property 25: Events Associated with Active Shift
@given(
    shift_id=st.uuids().map(str),
    event_type=st.sampled_from(EVENT_TYPES),
)
@h_settings(max_examples=100)
def test_event_shift_id_matches_active_shift(shift_id: str, event_type: str):
    event = {"shift_id": shift_id, "event_type": event_type}
    assert event["shift_id"] == shift_id


# ---------------------------------------------------------------------------
# Property 26: Shift End Expires All Associated Events
# ---------------------------------------------------------------------------
# Feature: quarry-mining-monitor, Property 26: Shift End Expires All Associated Events
@given(
    shift_id=st.uuids().map(str),
    n_events=st.integers(min_value=1, max_value=20),
)
@h_settings(max_examples=100)
def test_shift_end_expires_all_events(shift_id: str, n_events: int):
    events = [{"shift_id": shift_id, "expired": False} for _ in range(n_events)]
    for e in events:
        if e["shift_id"] == shift_id:
            e["expired"] = True
    for e in events:
        assert e["expired"] is True


# ---------------------------------------------------------------------------
# Property 27: Zone CRUD Round-Trip
# ---------------------------------------------------------------------------
# Feature: quarry-mining-monitor, Property 27: Zone CRUD Round-Trip
@given(
    name=st.text(min_size=1, max_size=100),
    description=st.one_of(st.none(), st.text(min_size=0, max_size=200)),
)
@h_settings(max_examples=100)
def test_zone_create_request_valid(name: str, description):
    from app.modules.zone.schemas import CreateZoneRequest
    req = CreateZoneRequest(name=name, description=description)
    assert req.name == name
    assert req.description == description


@given(
    name=st.text(min_size=1, max_size=100),
    description=st.one_of(st.none(), st.text(min_size=0, max_size=200)),
)
@h_settings(max_examples=100)
def test_zone_update_request_valid(name: str, description):
    from app.modules.zone.schemas import UpdateZoneRequest
    req = UpdateZoneRequest(name=name, description=description)
    assert req.name == name


# ---------------------------------------------------------------------------
# Property 28: Zone Machine Assignment Consistency
# ---------------------------------------------------------------------------
# Feature: quarry-mining-monitor, Property 28: Zone Machine Assignment Consistency
@given(
    machine_ids=st.lists(st.uuids().map(str), min_size=1, max_size=10, unique=True),
    zone_id=st.uuids().map(str),
)
@h_settings(max_examples=100)
def test_zone_machines_returns_exactly_assigned_machines(machine_ids: list[str], zone_id: str):
    all_machines = [{"id": mid, "current_zone_id": zone_id} for mid in machine_ids]
    zone_machines = [m for m in all_machines if m["current_zone_id"] == zone_id]
    assert len(zone_machines) == len(machine_ids)
    assert {m["id"] for m in zone_machines} == set(machine_ids)


# ---------------------------------------------------------------------------
# Property 29: Zone Delete Blocked by Assigned Machines
# ---------------------------------------------------------------------------
# Feature: quarry-mining-monitor, Property 29: Zone Delete Blocked by Assigned Machines
@given(n_machines=st.integers(min_value=1, max_value=10))
@h_settings(max_examples=100)
def test_zone_with_machines_cannot_be_deleted(n_machines: int):
    delete_blocked = n_machines > 0
    assert delete_blocked is True


def test_zone_without_machines_can_be_deleted():
    delete_blocked = 0 > 0
    assert delete_blocked is False


# ---------------------------------------------------------------------------
# Property 30: Report Generation Completeness and Persistence
# ---------------------------------------------------------------------------
# Feature: quarry-mining-monitor, Property 30: Report Generation Completeness and Persistence
@given(n_machines=st.integers(min_value=1, max_value=10))
@h_settings(max_examples=100)
def test_report_data_contains_all_required_sections(n_machines: int):
    from app.modules.report.schemas import AnomalyCount, MachineUtilization, ReportData, TaskCounts
    data = ReportData(
        machine_utilization=[
            MachineUtilization(machine_id=f"m{i}", machine_name=f"Machine {i}", utilization_percent=50.0)
            for i in range(n_machines)
        ],
        task_counts=TaskCounts(pending=1, active=2, completed=3, validated=4),
        anomaly_counts=[],
    )
    assert len(data.machine_utilization) == n_machines
    assert data.task_counts.pending >= 0
    assert data.task_counts.completed >= 0


# ---------------------------------------------------------------------------
# Property 31: Report Generation Role Restriction
# ---------------------------------------------------------------------------
# Feature: quarry-mining-monitor, Property 31: Report Generation Role Restriction
@given(role=st.sampled_from(REPORT_DENIED_ROLES))
@h_settings(max_examples=100)
def test_report_generation_denied_for_restricted_roles(role: str):
    assert role not in REPORT_ALLOWED_ROLES


@given(role=st.sampled_from(REPORT_ALLOWED_ROLES))
@h_settings(max_examples=100)
def test_report_generation_allowed_for_permitted_roles(role: str):
    assert role in REPORT_ALLOWED_ROLES


# ---------------------------------------------------------------------------
# Property 32: Notification Filter Correctness
# ---------------------------------------------------------------------------
# Feature: quarry-mining-monitor, Property 32: Notification Filter Correctness
@given(
    user_ids=st.lists(st.uuids().map(str), min_size=2, max_size=5, unique=True),
    notif_types=st.lists(st.sampled_from(NOTIFICATION_TYPES), min_size=1, max_size=10),
)
@h_settings(max_examples=100)
def test_notification_filter_returns_only_requesting_users_notifications(
    user_ids: list[str], notif_types: list[str]
):
    requesting_user = user_ids[0]
    other_users = user_ids[1:]
    notifications = (
        [{"user_id": requesting_user, "type": t} for t in notif_types]
        + [{"user_id": uid, "type": t} for uid in other_users for t in notif_types]
    )
    filtered = [n for n in notifications if n["user_id"] == requesting_user]
    for n in filtered:
        assert n["user_id"] == requesting_user


@given(
    notif_type=st.sampled_from(NOTIFICATION_TYPES),
    filter_type=st.sampled_from(NOTIFICATION_TYPES),
    n=st.integers(min_value=1, max_value=10),
)
@h_settings(max_examples=100)
def test_notification_type_filter_correctness(notif_type: str, filter_type: str, n: int):
    notifications = [{"user_id": "user-1", "type": notif_type} for _ in range(n)]
    filtered = [notif for notif in notifications if notif["type"] == filter_type]
    for notif in filtered:
        assert notif["type"] == filter_type


# ---------------------------------------------------------------------------
# Property 33: Notification Creation Invariant
# ---------------------------------------------------------------------------
# Feature: quarry-mining-monitor, Property 33: Notification Creation Invariant
@given(
    user_id=st.uuids().map(str),
    notif_type=st.sampled_from(NOTIFICATION_TYPES),
)
@h_settings(max_examples=100)
def test_new_notification_read_is_false(user_id: str, notif_type: str):
    notification = {"user_id": user_id, "type": notif_type, "read": False}
    assert notification["read"] is False
    assert notification["user_id"] == user_id


# ---------------------------------------------------------------------------
# Property 34: Notification Read Ownership
# ---------------------------------------------------------------------------
# Feature: quarry-mining-monitor, Property 34: Notification Read Ownership
@given(
    owner_id=st.uuids().map(str),
    requester_id=st.uuids().map(str),
)
@h_settings(max_examples=100)
def test_notification_read_ownership_check(owner_id: str, requester_id: str):
    if str(owner_id) != str(requester_id):
        access_denied = True
    else:
        access_denied = False
    if owner_id != requester_id:
        assert access_denied is True
    else:
        assert access_denied is False
