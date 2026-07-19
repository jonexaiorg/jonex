from sqlalchemy import Column, BigInteger, String, SmallInteger

from jonex_core.common.database import Base
from jonex_core.common.entity import SoftDeleteMixin, TimestampMixin


class Application(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "applications"
    __table_args__ = {"schema": "platform"}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    app_code = Column(String(64), nullable=False, unique=True)
    name = Column(String(128), nullable=False)
    entry_path = Column(String(256))
    icon = Column(String(128))
    description = Column(String(512))
    status = Column(SmallInteger, default=1)
    sort_order = Column(SmallInteger, default=0)
