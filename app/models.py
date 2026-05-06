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
	created_at: DateTime = Column(DateTime(timezone=True), server_default=func.now())
	last_login: datetime | None = Column(DateTime(timezone=True), nullable=True)
