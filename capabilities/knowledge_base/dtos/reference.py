#!/usr/bin/python3



from typing import Any, List, Optional

try:
    from pydantic.v1 import BaseModel, Field
except ImportError:
    from pydantic import BaseModel, Field


class SourceLocation(BaseModel):


    type: str = "chunk"
    chunk_index: Optional[int] = None
    char_start: Optional[int] = None
    char_end: Optional[int] = None
    page_no: Optional[int] = None
    time_start: Optional[float] = None
    time_end: Optional[float] = None
    text: Optional[str] = None


class SourceReference(BaseModel):


    doc_id: str
    kb_id: Optional[str] = None
    file_name: str
    mime_type: Optional[str] = None
    file_size: Optional[int] = None
    media_type: str = "other"
    raw_url: Optional[str] = None
    locations: List[SourceLocation] = Field(default_factory=list)


class ParsedRef(BaseModel):


    doc_id: str
    kb_id: Optional[str] = None
    chunk_index: Optional[int] = None
    char_start: Optional[int] = None
    char_end: Optional[int] = None
    page_no: Optional[int] = None
    time_start: Optional[float] = None
    time_end: Optional[float] = None


class ReferenceResolveRequest(BaseModel):


    doc_ids: List[str] = Field(default_factory=list)
    refs: List[ParsedRef] = Field(default_factory=list)


__all__ = [
    "ParsedRef",
    "ReferenceResolveRequest",
    "SourceLocation",
    "SourceReference",
]
