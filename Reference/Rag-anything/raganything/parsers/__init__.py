"""
RAG-Anything parsers package.

Deprecated import path (shim): ``from raganything.parser import ...``
New import path:             ``from raganything.parsers import ...``
"""

from raganything.parsers.base import Parser as Parser
from raganything.parsers.mineru import MineruExecutionError as MineruExecutionError
from raganything.parsers.mineru import MineruOnlineParser as MineruOnlineParser
from raganything.parsers.mineru import MineruParser as MineruParser
from raganything.parsers.mineru import MineruSelfHostParser as MineruSelfHostParser
from raganything.parsers.docling import DoclingParser as DoclingParser
from raganything.parsers.paddleocr import PaddleOCRParser as PaddleOCRParser
from raganything.parsers.registry import (
    SUPPORTED_PARSERS as SUPPORTED_PARSERS,
    _CUSTOM_PARSERS as _CUSTOM_PARSERS,
    get_parser as get_parser,
    get_supported_parsers as get_supported_parsers,
    list_parsers as list_parsers,
    register_parser as register_parser,
    unregister_parser as unregister_parser,
)
from raganything.parsers.conversion import (
    convert_office_to_pdf as convert_office_to_pdf,
    convert_text_to_pdf as convert_text_to_pdf,
)

__all__ = [
    "Parser",
    "MineruParser",
    "MineruOnlineParser",
    "MineruSelfHostParser",
    "MineruExecutionError",
    "DoclingParser",
    "PaddleOCRParser",
    "register_parser",
    "unregister_parser",
    "get_parser",
    "list_parsers",
    "get_supported_parsers",
    "SUPPORTED_PARSERS",
    "_CUSTOM_PARSERS",
    "convert_office_to_pdf",
    "convert_text_to_pdf",
]
