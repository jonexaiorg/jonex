#!/usr/bin/python3



from jonex_core.common.repository import BaseRepository

from ..models.knowledge_info import KnowledgeInfo


class KnowledgeInfoRepository(BaseRepository[KnowledgeInfo]):
    model = KnowledgeInfo