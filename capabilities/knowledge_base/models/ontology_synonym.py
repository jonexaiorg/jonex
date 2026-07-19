#!/usr/bin/python3


from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import JSONB

from jonex_core.common.database import Base
from jonex_core.common.entity import SoftDeleteMixin, TenantMixin, TimestampMixin


class OntologySynonym(TenantMixin, TimestampMixin, SoftDeleteMixin, Base):


    __tablename__ = "ontology_synonyms"
    __table_args__ = {"schema": "knowledge_base"}

    id = Column(String(64), primary_key=True)
    knowledge_base_id = Column(String(128), nullable=False, index=True)
    terms = Column(JSONB, nullable=False, default=list)
    canonical = Column(String(255), nullable=True)

    def to_dict(self) -> dict:

        return {
            "id": self.id,
            "knowledge_base_id": self.knowledge_base_id,
            "terms": self.terms or [],
            "canonical": self.canonical,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


__all__ = ["OntologySynonym"]
