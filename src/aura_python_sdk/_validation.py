"""Client-side argument validation, run before any request is sent (Go: internal/utils)."""

from __future__ import annotations

import re

from aura_python_sdk._errors import AuraValidationError

_UUID = re.compile(r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}")
_INSTANCE_ID = re.compile(r"[0-9a-fA-F]{8}")

MAX_INSTANCE_NAME_LENGTH = 30


def require_non_empty(name: str, value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        raise AuraValidationError(f"{name} must not be empty")
    return value


def _uuid(name: str, value: object) -> str:
    value = require_non_empty(name, value)
    if not _UUID.fullmatch(value):
        raise AuraValidationError(
            f"{name} must be a valid UUID format (xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx)"
        )
    return value


def instance_id(value: object, name: str = "instance ID") -> str:
    value = require_non_empty(name, value)
    if not _INSTANCE_ID.fullmatch(value):
        raise AuraValidationError(
            f"{name} must be in the format of a 8-character hex string (xxxxxxxx)"
        )
    return value


def tenant_id(value: object, name: str = "tenant ID") -> str:
    return _uuid(name, value)


def snapshot_id(value: object, name: str = "snapshot ID") -> str:
    return _uuid(name, value)


def session_id(value: object) -> str:
    return require_non_empty("GDS session ID", value)


def instance_name(value: object) -> str:
    value = require_non_empty("instance name", value)
    if len(value) > MAX_INSTANCE_NAME_LENGTH:
        raise AuraValidationError(
            f"instance name must be at most {MAX_INSTANCE_NAME_LENGTH} characters long"
        )
    return value


def non_negative_int(name: str, value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise AuraValidationError(f"{name} must be an integer of zero or more")
    return value
