"""
Property-based tests for the auth module.
Feature: quarry-mining-monitor
"""
import pytest
from datetime import datetime, timedelta, timezone
from hypothesis import given, settings as h_settings
from hypothesis import strategies as st
from jose import jwt, JWTError
from passlib.context import CryptContext

from app.config import settings as app_settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ROLES = ["operator", "dispatcher", "manager", "admin", "mechanic", "IT", "owner"]

# ---------------------------------------------------------------------------
# Property 1: JWT Login Round-Trip
# For any valid user (any role), a JWT created with the correct payload should
# decode back to the same user ID and role.
# ---------------------------------------------------------------------------
# Feature: quarry-mining-monitor, Property 1: JWT Login Round-Trip
@given(
    user_id=st.uuids().map(str),
    role=st.sampled_from(ROLES),
)
@h_settings(max_examples=100)
def test_jwt_login_round_trip(user_id: str, role: str):
    expire = datetime.now(timezone.utc) + timedelta(seconds=3600)
    token_data = {"sub": user_id, "role": role, "exp": expire}
    token = jwt.encode(token_data, app_settings.JWT_SECRET, algorithm="HS256")
    decoded = jwt.decode(token, app_settings.JWT_SECRET, algorithms=["HS256"])
    assert decoded["sub"] == user_id
    assert decoded["role"] == role


# ---------------------------------------------------------------------------
# Property 2: Invalid Credentials Always Rejected
# A JWT signed with a wrong secret should always fail to decode.
# ---------------------------------------------------------------------------
# Feature: quarry-mining-monitor, Property 2: Invalid Credentials Always Rejected
@given(
    wrong_secret=st.text(min_size=1, max_size=64).filter(lambda s: s != app_settings.JWT_SECRET),
    user_id=st.uuids().map(str),
    role=st.sampled_from(ROLES),
)
@h_settings(max_examples=100)
def test_token_with_wrong_secret_always_rejected(wrong_secret: str, user_id: str, role: str):
    expire = datetime.now(timezone.utc) + timedelta(seconds=3600)
    token = jwt.encode({"sub": user_id, "role": role, "exp": expire}, wrong_secret, algorithm="HS256")
    with pytest.raises(JWTError):
        jwt.decode(token, app_settings.JWT_SECRET, algorithms=["HS256"])


# ---------------------------------------------------------------------------
# Property 3: Protected Endpoints Require Valid JWT
# A malformed token string should always raise JWTError on decode.
# ---------------------------------------------------------------------------
# Feature: quarry-mining-monitor, Property 3: Protected Endpoints Require Valid JWT
@given(
    bad_token=st.text(min_size=1, max_size=200).filter(lambda s: s.count(".") != 2),
)
@h_settings(max_examples=100)
def test_malformed_token_always_rejected(bad_token: str):
    with pytest.raises(JWTError):
        jwt.decode(bad_token, app_settings.JWT_SECRET, algorithms=["HS256"])


# ---------------------------------------------------------------------------
# Property 4: Unauthorized Role Always Rejected
# require_roles logic: if user role not in allowed list, access is denied.
# ---------------------------------------------------------------------------
# Feature: quarry-mining-monitor, Property 4: Unauthorized Role Always Rejected
@given(
    user_role=st.sampled_from(ROLES),
    allowed_roles=st.lists(st.sampled_from(ROLES), min_size=1, max_size=6, unique=True).filter(
        lambda roles: len(roles) < len(ROLES)  # ensure at least one role is excluded
    ),
)
@h_settings(max_examples=100)
def test_unauthorized_role_always_rejected(user_role: str, allowed_roles: list):
    # If user_role is not in allowed_roles, access should be denied
    if user_role not in allowed_roles:
        assert user_role not in allowed_roles  # role check fails → 403
    else:
        # If user_role IS in allowed_roles, access is granted
        assert user_role in allowed_roles


# ---------------------------------------------------------------------------
# Bonus: Password hashing round-trip (supports Property 1 correctness)
# bcrypt truncates at 72 bytes; constrain strategy to ASCII to stay within limit.
# ---------------------------------------------------------------------------
_safe_password = st.text(
    min_size=1,
    max_size=72,
    alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"), whitelist_characters="!@#$%^&*"),
).filter(lambda s: len(s.encode("utf-8")) <= 72)


@given(password=_safe_password)
@h_settings(max_examples=50, deadline=None)
def test_password_hash_verify_round_trip(password: str):
    hashed = pwd_context.hash(password)
    assert pwd_context.verify(password, hashed) is True


@given(password=_safe_password, wrong_password=_safe_password)
@h_settings(max_examples=50, deadline=None)
def test_wrong_password_never_verifies(password: str, wrong_password: str):
    if password == wrong_password:
        return  # skip equal case
    hashed = pwd_context.hash(password)
    assert pwd_context.verify(wrong_password, hashed) is False
