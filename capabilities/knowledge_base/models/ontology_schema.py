
from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB

from jonex_core.common.database import Base
from jonex_core.common.entity import TenantMixin, TimestampMixin


class OntologyTemplateBinding(TenantMixin, TimestampMixin, Base):


    __tablename__ = "ontology_template_bindings"
    __table_args__ = {"schema": "knowledge_base"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    knowledge_base_id = Column(String(128), nullable=False, index=True)
    template_domain_id = Column(String(64), nullable=True)
    template_scenario_id = Column(String(64), nullable=True)
    source_type = Column(String(32), nullable=False, default="business_template")
    status = Column(String(32), nullable=False, default="active")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "tenant_id": self.tenant_id,
            "knowledge_base_id": self.knowledge_base_id,
            "template_domain_id": self.template_domain_id,
            "template_scenario_id": self.template_scenario_id,
            "source_type": self.source_type,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class OntologyCompiledSchema(TenantMixin, TimestampMixin, Base):


    __tablename__ = "ontology_compiled_schemas"
    __table_args__ = {"schema": "knowledge_base"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    knowledge_base_id = Column(String(128), nullable=False, index=True)
    template_domain_id = Column(String(64), nullable=True)
    template_scenario_id = Column(String(64), nullable=True)
    source_type = Column(String(32), nullable=False, default="business_template")
    source_version = Column(Integer, nullable=False, default=1)
    source_hash = Column(String(64), nullable=True)
    schema_version = Column(Integer, nullable=False, default=1)
    entity_types = Column(JSONB, nullable=False, default=list)
    relation_types = Column(JSONB, nullable=False, default=list)
    constraints = Column(JSONB, nullable=False, default=list)
    disambiguation = Column(
        JSONB,
        nullable=False,
        default={"case_insensitive": True, "alias_merge": True},
    )
    prompt_schema = Column(JSONB, nullable=False, default=dict)
    status = Column(String(32), nullable=False, default="active")
    schema_mode = Column(String(32), nullable=False, default="template_seeded")
    sync_status = Column(String(32), nullable=False, default="synced")
    edited_at = Column(DateTime(timezone=True), nullable=True)
    edited_by = Column(String(128), nullable=True)
    compiled_at = Column(DateTime(timezone=True), nullable=False)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "tenant_id": self.tenant_id,
            "knowledge_base_id": self.knowledge_base_id,
            "template_domain_id": self.template_domain_id,
            "template_scenario_id": self.template_scenario_id,
            "source_type": self.source_type,
            "source_version": self.source_version,
            "source_hash": self.source_hash,
            "schema_version": self.schema_version,
            "entity_types": self.entity_types or [],
            "relation_types": self.relation_types or [],
            "constraints": self.constraints or [],
            "disambiguation": self.disambiguation or {},
            "prompt_schema": self.prompt_schema or {},
            "status": self.status,
            "schema_mode": self.schema_mode,
            "sync_status": self.sync_status,
            "edited_at": self.edited_at.isoformat() if self.edited_at else None,
            "edited_by": self.edited_by,
            "compiled_at": self.compiled_at.isoformat() if self.compiled_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


__all__ = ["OntologyTemplateBinding", "OntologyCompiledSchema"]
