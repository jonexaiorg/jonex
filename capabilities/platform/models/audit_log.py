from sqlalchemy import Column, BigInteger, String, SmallInteger, Text
from sqlalchemy.dialects.postgresql import JSONB

from jonex_core.common.database import Base
from jonex_core.common.entity import TenantMixin, TimestampMixin


class AuditLog(TenantMixin, TimestampMixin, Base):
    __tablename__ = "audit_logs"
    __table_args__ = {"schema": "platform"}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger)
    username = Column(String(128))
    ip = Column(String(64))
    action = Column(String(64), nullable=False)
    resource = Column(String(128))
    resource_id = Column(String(64))
    status_code = Column(SmallInteger)
    duration_ms = Column(BigInteger)
    request_params = Column(JSONB)
    response_body = Column(JSONB)
    error_stack = Column(Text)
    trace_id = Column(String(128))


    log_type = Column(String(32))
    service_name = Column(String(64))
    outcome = Column(String(16))
    log_level = Column(String(16))
    error_message = Column(Text)
    method = Column(String(8))
    path = Column(String(512))



    tenant_id = Column(String(64), nullable=True, index=True)
