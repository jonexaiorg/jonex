#!/usr/bin/python3



from datetime import datetime

from sqlalchemy import Column, DateTime, SmallInteger, String
from sqlalchemy.orm import declared_attr


class TenantMixin:


    @declared_attr
    def tenant_id(cls):
        return Column(String(64), nullable=False, index=True)


class TimestampMixin:


    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )


class SoftDeleteMixin:


    is_deleted = Column(SmallInteger, default=0, nullable=False, index=True)


class AuditMixin:


    created_by = Column(String(64), nullable=True)
    updated_by = Column(String(64), nullable=True)


__all__ = [
    "AuditMixin",
    "SoftDeleteMixin",
    "TenantMixin",
    "TimestampMixin",
]
