from sqlalchemy import Column, BigInteger, String

from jonex_core.common.database import Base
from jonex_core.common.entity import TimestampMixin


class ApplicationRoute(TimestampMixin, Base):
    __tablename__ = "application_routes"
    __table_args__ = {"schema": "platform"}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    app_id = Column(BigInteger, nullable=False)
    route_path = Column(String(256), nullable=False)
    title = Column(String(128))
    permission_code = Column(String(128))
