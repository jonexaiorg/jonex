from sqlalchemy import Column, BigInteger, String, TIMESTAMP, Text

from jonex_core.common.database import Base
from jonex_core.common.entity import TenantMixin, TimestampMixin


class LoginTicket(TenantMixin, TimestampMixin, Base):
    __tablename__ = "login_tickets"
    __table_args__ = {"schema": "platform"}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    ticket_hash = Column(String(128), nullable=False, unique=True)
    user_id = Column(BigInteger, nullable=False)
    app_id = Column(String(64), nullable=False)
    redirect_uri = Column(String(1024), nullable=False)
    state = Column(String(256))
    expires_at = Column(TIMESTAMP, nullable=False)
    used_at = Column(TIMESTAMP)
    client_ip = Column(String(64))
    user_agent = Column(Text)
