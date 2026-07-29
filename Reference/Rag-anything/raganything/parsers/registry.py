"""Parser registry — built-in and custom parser registration.

Provides ``register_parser``, ``unregister_parser``, ``get_parser``,
``list_parsers``, and ``get_supported_parsers`` for extensible parser management.

Deprecated: import these directly from ``raganything.parsers.registry``
instead of from ``raganything.parser``.
"""

import logging
from typing import Dict, Tuple

from raganything.parsers.base import Parser
from raganything.parsers.mineru import (
    MineruOnlineParser,
    MineruParser,
    MineruSelfHostParser,
)
from raganything.parsers.docling import DoclingParser
from raganything.parsers.paddleocr import PaddleOCRParser

logger = logging.getLogger(__name__)

# Built-in parser names that cannot be overridden by custom registrations.
_BUILTIN_NAMES = {"mineru", "mineru_online", "mineru_selfhost", "docling", "paddleocr"}

# Custom parser registry for Bring-Your-Own-Parser support (see #151)
_CUSTOM_PARSERS: Dict[str, type] = {}

SUPPORTED_PARSERS = ("mineru", "mineru_online", "mineru_selfhost", "docling", "paddleocr")


def _normalize_parser_name(name: str) -> str:
    """Normalize and validate a parser name for registry APIs."""
    if not isinstance(name, str):
        raise TypeError(
            f"parser name must be a non-empty string, got {type(name).__name__}"
        )
    normalized = name.strip().lower()
    if not normalized:
        raise ValueError("parser name must be a non-empty string")
    return normalized


def register_parser(name: str, parser_class: type) -> None:
    """Register a custom parser class for use with RAGAnything.

    This enables the Bring-Your-Own-Parser pattern: users can integrate
    any document parser (e.g., Marker, Unstructured, Surya) by subclassing
    ``Parser`` and registering it here.

    Args:
        name: Unique identifier for the parser (e.g., "marker", "surya").
              Must not collide with built-in names ("mineru", "docling", "paddleocr").
        parser_class: A subclass of ``Parser`` that implements at least
                      ``parse_document``, ``check_installation``, and
                      optionally ``parse_pdf``, ``parse_image``, ``parse_office_doc``.

    Raises:
        TypeError: If *parser_class* is not a subclass of ``Parser``.
        ValueError: If *name* collides with a built-in parser name.
    """
    normalized_name = _normalize_parser_name(name)
    if not isinstance(parser_class, type) or not issubclass(parser_class, Parser):
        raise TypeError(
            f"parser_class must be a subclass of Parser, got {parser_class!r}"
        )
    if normalized_name in _BUILTIN_NAMES:
        raise ValueError(
            f"Cannot override built-in parser '{normalized_name}'. "
            f"Choose a different name for your custom parser."
        )
    _CUSTOM_PARSERS[normalized_name] = parser_class
    logger.info(
        "Registered custom parser: '%s' -> %s", normalized_name, parser_class.__name__
    )


def unregister_parser(name: str) -> None:
    """Remove a previously registered custom parser.

    Args:
        name: The parser name to remove.

    Raises:
        TypeError: If *name* is not a string.
        ValueError: If *name* is empty or only whitespace.
        KeyError: If no custom parser with that name is registered.
    """
    normalized_name = _normalize_parser_name(name)
    if normalized_name not in _CUSTOM_PARSERS:
        raise KeyError(f"No custom parser registered with name '{normalized_name}'")
    del _CUSTOM_PARSERS[normalized_name]
    logger.info("Unregistered custom parser: '%s'", normalized_name)


def list_parsers() -> Dict[str, str]:
    """Return a mapping of all available parser names to their class names.

    Returns:
        Dict mapping parser name to the fully-qualified class name.
        Includes both built-in and custom parsers.
    """
    result: Dict[str, str] = {
        "mineru": "MineruParser",
        "mineru_online": "MineruOnlineParser",
        "mineru_selfhost": "MineruSelfHostParser",
        "docling": "DoclingParser",
        "paddleocr": "PaddleOCRParser",
    }
    for name, cls in _CUSTOM_PARSERS.items():
        result[name] = cls.__name__
    return result


def get_supported_parsers() -> Tuple[str, ...]:
    """Return all supported parser names including custom registered parsers."""
    return SUPPORTED_PARSERS + tuple(_CUSTOM_PARSERS.keys())


def get_parser(parser_type: str) -> Parser:
    """Get a parser instance by name.

    Checks built-in parsers first, then falls back to the custom parser
    registry populated via :func:`register_parser`.

    Args:
        parser_type: Parser name (e.g., "mineru", "mineru_online", "mineru_selfhost",
                     "docling", "paddleocr", or any custom registered name).

    Returns:
        An instance of the requested parser.

    Raises:
        ValueError: If the parser name is not recognized.
    """
    parser_name = (parser_type or "mineru").strip().lower()
    if parser_name == "mineru":
        return MineruParser()
    if parser_name == "mineru_online":
        return MineruOnlineParser()
    if parser_name == "mineru_selfhost":
        return MineruSelfHostParser()
    if parser_name == "docling":
        return DoclingParser()
    if parser_name == "paddleocr":
        return PaddleOCRParser()
    if parser_name in _CUSTOM_PARSERS:
        return _CUSTOM_PARSERS[parser_name]()
    raise ValueError(
        f"Unsupported parser type: {parser_type}. "
        f"Supported parsers: {', '.join(get_supported_parsers())}"
    )
