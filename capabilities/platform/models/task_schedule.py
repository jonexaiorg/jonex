from sqlalchemy import Column, BigInteger, String, SmallInteger, TIMESTAMP
from sqlalchemy.dialects.postgresql import JSONB

from jonex_core.common.database import Base
from jonex_core.common.entity import SoftDeleteMixin, TenantMixin, TimestampMixin


class TaskSchedule(TenantMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "task_schedules"
    __table_args__ = {"schema": "platform"}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    task_type = Column(String(64), nullable=False)
    cron_expr = Column(String(128))
    status = Column(SmallInteger, default=1)
    last_run_at = Column(TIMESTAMP)
    next_run_at = Column(TIMESTAMP)
    config_json = Column(JSONB)
