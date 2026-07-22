from sqlalchemy import Column, BigInteger, String, SmallInteger, TIMESTAMP, Text, text

from jonex_core.common.database import Base


class LoginTicket(Base):
    __tablename__ = "login_tickets"
    __table_args__ = {"schema": "platform"}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    ticket_hash = Column(String(128), nullable=False, unique=True)
    tenant_id = Column(String(64), nullable=False)
    user_id = Column(BigInteger, nullable=False)
    app_id = Column(String(64), nullable=False)
    redirect_uri = Column(String(1024), nullable=False)
    state = Column(String(256))
    expires_at = Column(TIMESTAMP, nullable=False)
    used_at = Column(TIMESTAMP)
    created_at = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))
    client_ip = Column(String(64))
    user_agent = Column(Text)
