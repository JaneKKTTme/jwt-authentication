from datetime import datetime

from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func

from app.database import Base


class User(Base):

	__tablename__ = 'users'

	id: int = Column(Integer, primary_key=True, index=True)
	username: str = Column(String(50), unique=True, index=True, nullable=False)
	hashed_password: str = Column(String(255), nullable=False)
	role: str = Column(String(20), default='user')
	is_active: bool = Column(Boolean, default=True)
	created_at: datetime = Column(DateTime(timezone=True), server_default=func.now())
	last_login: datetime | None = Column(DateTime(timezone=True), nullable=True)


class Session(Base):

	__tablename__ = 'session'

	id: int = Column(Integer, primary_key=True, index=True)
	user_id: int = Column(Integer, ForeignKey('user.id', ondelete='CASCADE'))
	jti: str = Column(String(255), unique=True, index=True)
	ip_address: str = Column(String(45), nullable=True)
	user_agent: str = Column(Text, nullable=True)
	created_at: datetime = Column(DateTime(timezone=True), server_default=func.now())
	expired_at: datetime | None = Column(DateTime(timezone=True), nullable=True)
	revoked_at: datetime | None = Column(DateTime(timezone=True), nullable=True)
