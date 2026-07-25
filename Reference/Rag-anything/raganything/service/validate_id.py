"""ID security validation and workspace header utilities."""

import os
import re

_SAFE_ID = re.compile(r"^[A-Za-z0-9_\-]+$")


def validate_id(value: str, name: str) -> str:
    """Validate that *value* is safe for use in file paths and workspace headers.

    Raises ValueError if the value is empty, contains path traversal characters,
    reserved double-underscores, or non-ASCII characters.
    """
    if not value or not _SAFE_ID.match(value):
        raise ValueError(f"Invalid {name}: {value!r}")
    if "__" in value:
        raise ValueError(f"Invalid {name} (contains reserved '__'): {value!r}")
    return value


def workspace(tenant_id: str, kb_id: str) -> str:
    """Build a LightRAG workspace header value.

    Uses ``|`` separator by default (overridable via ``WORKSPACE_SEPARATOR`` env var).
    When *kb_id* is empty, returns *tenant_id* alone.
    """
    sep = os.getenv("WORKSPACE_SEPARATOR", "|")
    return f"{tenant_id}{sep}{kb_id}" if kb_id else tenant_id
