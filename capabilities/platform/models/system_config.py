from sqlalchemy import Column, BigInteger, String, Text

from jonex_core.common.database import Base
from jonex_core.common.entity import TimestampMixin


class SystemConfig(TimestampMixin, Base):
    __tablename__ = "system_configs"
    __table_args__ = {"schema": "platform"}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    config_group = Column(String(64), nullable=False)
    config_key = Column(String(128), nullable=False, unique=True)
    config_value = Column(Text)
    value_type = Column(String(32), default="string")
    description = Column(String(512))
