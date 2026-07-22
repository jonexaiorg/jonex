from sqlalchemy import Column, BigInteger, String, SmallInteger, TIMESTAMP, text

from jonex_core.common.database import Base


class User(Base):
    __tablename__ = "users"
    __table_args__ = {"schema": "platform"}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id = Column(String(64), nullable=False, default="default_tenant")
    username = Column(String(128), nullable=False)
    password_hash = Column(String(256), nullable=False)
    display_name = Column(String(255))
    email = Column(String(255))
    role = Column(String(32), nullable=False, default="user")
    status = Column(SmallInteger, default=1)
    last_login_at = Column(TIMESTAMP)
    create_time = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))
    update_time = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))
    is_deleted = Column(SmallInteger, default=0)
