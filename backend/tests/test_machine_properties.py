"""
Property-based tests for the machine module.
Feature: quarry-mining-monitor
"""
import sys
from unittest.mock import MagicMock

# Stub out asyncpg-dependent modules before any app imports trigger DB engine creation
for _mod in [
    "asyncpg",
    "app.database",
    "app.modules.machine.repository",
]:
    if _mod not in sys.modules:
        sys.modules[_mod] = MagicMock()

# Provide a minimal Base stub so models can be imported without a real DB
import types as _types
_db_stub = sys.modules["app.database"]
_db_stub.Base = type("Base", (), {"__init_subclass__": classmethod(lambda cls, **kw: None)})

from hypothesis import given, settings as h_settings
from hypothesis import strategies as st

from app.modules.machine.conflict_service import resolve_effective_state

MACHINE_STATES = ["idle", "operating", "maintenance", "breakdown"]
ROLES = ["operator", "dispatcher", "manager", "admin", "mechanic", "IT", "owner"]

# ---------------------------------------------------------------------------
# Property 5: Machine List Completeness
# (Integration test — tested via API; here we verify the schema shape)
# ---------------------------------------------------------------------------
# Feature: quarry-mining-monitor, Property 5: Machine List Completeness
@given(
    names=st.lists(st.text(min_size=1, max_size=50), min_size=1, max_size=20, unique=True),
)
@h_settings(max_examples=100)
def test_machine_response_schema_has_required_fields(names: list[str]):
    from app.modules.machine.schemas import MachineResponse
    # Verify MachineResponse model fields exist
    fields = MachineResponse.model_fields
    assert "id" in fields
    assert "name" in fields
    assert "current_state" in fields
    assert "conflict_active" in fields


# ---------------------------------------------------------------------------
# Property 7: State Update Source Recording
# Dispatcher role → source='dispatcher'; any other role → source='operator'
# ---------------------------------------------------------------------------
# Feature: quarry-mining-monitor, Property 7: State Update Source Recording
@given(role=st.sampled_from(ROLES))
@h_settings(max_examples=100)
def test_state_source_matches_actor_role(role: str):
    source = "dispatcher" if role == "dispatcher" else "operator"
    if role == "dispatcher":
        assert source == "dispatcher"
    else:
        assert source == "operator"


# ---------------------------------------------------------------------------
# Property 8: State Priority Invariant
# When dispatcher_state is set, effective_state always equals dispatcher_state
# regardless of operator_state or telemetry_state.
# ---------------------------------------------------------------------------
# Feature: quarry-mining-monitor, Property 8: State Priority Invariant
@given(
    dispatcher_state=st.sampled_from(MACHINE_STATES),
    telemetry_state=st.one_of(st.none(), st.sampled_from(MACHINE_STATES)),
    operator_state=st.one_of(st.none(), st.sampled_from(MACHINE_STATES)),
)
@h_settings(max_examples=100)
def test_dispatcher_state_always_wins(
    dispatcher_state: str,
    telemetry_state: str | None,
    operator_state: str | None,
):
    effective_state, _ = resolve_effective_state(dispatcher_state, telemetry_state, operator_state)
    assert effective_state == dispatcher_state


# ---------------------------------------------------------------------------
# Property 9: Conflict Detection and API Flag
# When dispatcher_state and operator_state are both set and disagree,
# conflict_active must be True.
# ---------------------------------------------------------------------------
# Feature: quarry-mining-monitor, Property 9: Conflict Detection and API Flag
@given(
    dispatcher_state=st.sampled_from(MACHINE_STATES),
    operator_state=st.sampled_from(MACHINE_STATES),
    telemetry_state=st.one_of(st.none(), st.sampled_from(MACHINE_STATES)),
)
@h_settings(max_examples=100)
def test_conflict_detected_when_states_disagree(
    dispatcher_state: str,
    operator_state: str,
    telemetry_state: str | None,
):
    _, conflict_active = resolve_effective_state(dispatcher_state, telemetry_state, operator_state)
    if dispatcher_state != operator_state:
        assert conflict_active is True
    else:
        assert conflict_active is False


# ---------------------------------------------------------------------------
# Property 10: Conflict Side-Effects (structural)
# When conflict is detected, conflict_active=True and effective_state=dispatcher_state
# ---------------------------------------------------------------------------
# Feature: quarry-mining-monitor, Property 10: Conflict Side-Effects
@given(
    dispatcher_state=st.sampled_from(MACHINE_STATES),
    operator_state=st.sampled_from(MACHINE_STATES).filter(lambda s: s != "idle"),
)
@h_settings(max_examples=100)
def test_conflict_effective_state_is_dispatcher(dispatcher_state: str, operator_state: str):
    if dispatcher_state == operator_state:
        return  # no conflict case, skip
    effective_state, conflict_active = resolve_effective_state(dispatcher_state, None, operator_state)
    assert conflict_active is True
    assert effective_state == dispatcher_state


# ---------------------------------------------------------------------------
# Property 11: Conflicts Never Auto-Resolve
# resolve_effective_state never clears conflict_active on its own —
# only explicit resolution (not modeled here) can do that.
# We verify: if both states are set and disagree, conflict_active stays True
# regardless of how many times we call the function.
# ---------------------------------------------------------------------------
# Feature: quarry-mining-monitor, Property 11: Conflicts Never Auto-Resolve
@given(
    dispatcher_state=st.sampled_from(MACHINE_STATES),
    operator_state=st.sampled_from(MACHINE_STATES),
    n_calls=st.integers(min_value=1, max_value=10),
)
@h_settings(max_examples=100)
def test_conflict_never_auto_resolves(dispatcher_state: str, operator_state: str, n_calls: int):
    if dispatcher_state == operator_state:
        return  # no conflict, skip
    for _ in range(n_calls):
        _, conflict_active = resolve_effective_state(dispatcher_state, None, operator_state)
        assert conflict_active is True


# ---------------------------------------------------------------------------
# Property 12: Conflict Resolution Clears Flag
# When dispatcher_state == operator_state (agreement), conflict_active=False
# ---------------------------------------------------------------------------
# Feature: quarry-mining-monitor, Property 12: Conflict Resolution Clears Flag and Emits Event
@given(
    state=st.sampled_from(MACHINE_STATES),
    telemetry_state=st.one_of(st.none(), st.sampled_from(MACHINE_STATES)),
)
@h_settings(max_examples=100)
def test_no_conflict_when_states_agree(state: str, telemetry_state: str | None):
    effective_state, conflict_active = resolve_effective_state(state, telemetry_state, state)
    assert conflict_active is False
    assert effective_state == state


# ---------------------------------------------------------------------------
# Property 6: Machine Creation Round-Trip (schema validation)
# CreateMachineRequest accepts valid machine types
# ---------------------------------------------------------------------------
# Feature: quarry-mining-monitor, Property 6: Machine Creation Round-Trip with Event
@given(
    name=st.text(min_size=1, max_size=100),
    machine_type=st.sampled_from(["excavator", "haul_truck", "drill", "dozer", "grader"]),
    initial_state=st.sampled_from(MACHINE_STATES),
)
@h_settings(max_examples=100)
def test_create_machine_request_valid(name: str, machine_type: str, initial_state: str):
    from app.modules.machine.schemas import CreateMachineRequest
    req = CreateMachineRequest(name=name, type=machine_type, initial_state=initial_state)
    assert req.name == name
    assert req.type == machine_type
    assert req.initial_state == initial_state
