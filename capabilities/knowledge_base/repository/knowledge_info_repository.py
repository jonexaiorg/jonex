#!/usr/bin/python3
# -*- coding:utf-8 -*-
"""Repository for KnowledgeInfo."""

from jonex_core.common.repository import BaseRepository

from ..models.knowledge_info import KnowledgeInfo


class KnowledgeInfoRepository(BaseRepository[KnowledgeInfo]):
    model = KnowledgeInfo