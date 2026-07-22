#!/usr/bin/python3
# -*- coding:utf-8 -*-
"""Domain capability layer - provides capability encapsulation for specific domains"""

from .base import DomainCapability
from .speech_processing.speech_to_text import SpeechToTextCapability
from .text_generation.summary_generator import SummaryGeneratorCapability
from .knowledge_retrieval.semantic_search import SemanticSearchCapability

__all__ = [
    "DomainCapability",
    "SpeechToTextCapability",
    "SummaryGeneratorCapability",
    "SemanticSearchCapability",
]
