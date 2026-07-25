"""Path component validation — prevents directory traversal attacks."""
from __future__ import annotations

import re

_PATH_COMPONENT_RE = re.compile(r"^[a-zA-Z0-9_\-]+$")


def validate_path_component(value: str, name: str) -> str:
    """Validate that a path component contains only safe characters.

    Allowed: [a-zA-Z0-9_-]
    Rejected: /, \\, ., spaces, @, empty, None

    Raises ValueError on invalid input.
    Returns the validated value unchanged on success.
    """
    if not value or not isinstance(value, str):
        raise ValueError(
            f"{name} must be a non-empty string, got: {value!r}"
        )
    if not _PATH_COMPONENT_RE.match(value):
        raise ValueError(
            f"Invalid {name}: '{value}' — only [a-zA-Z0-9_-] allowed"
        )
    return value
