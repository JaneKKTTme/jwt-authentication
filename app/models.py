from datetime import datetime

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


user_roles = Table(
	'user_roles',
	Base.metadata,
	Column('user_id', Integer, ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
	Column('role_id', Integer, ForeignKey('roles.id', ondelete='CASCADE'), primary_key=True)
)

role_permissions = Table(
	'role_permissions',
	Base.metadata,
	Column('role_id', Integer, ForeignKey('roles.id', ondelete='CASCADE'), primary_key=True),
	Column('permission_id', Integer, ForeignKey('permissions.id', ondelete='CASCADE'), primary_key=True)
)

class User(Base):

	__tablename__ = 'users'

	id: int = Column(Integer, primary_key=True, index=True)
	username: str = Column(String(50), unique=True, index=True, nullable=False)
	hashed_password: str = Column(String(255), nullable=False)
	is_active: bool = Column(Boolean, default=True)
	created_at: datetime = Column(DateTime(timezone=True), server_default=func.now())
	last_login: datetime | None = Column(DateTime(timezone=True), nullable=True)

	roles = relationship('Role', secondary=user_roles, backref='users')


class Session(Base):

	__tablename__ = 'sessions'

	id: int = Column(Integer, primary_key=True, index=True)
	user_id: int = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'))
	jti: str = Column(String(255), unique=True, index=True)
	ip_address: str = Column(String(45), nullable=True)
	user_agent: str = Column(Text, nullable=True)
	created_at: datetime = Column(DateTime(timezone=True), server_default=func.now())
	expired_at: datetime | None = Column(DateTime(timezone=True), nullable=True)
	revoked_at: datetime | None = Column(DateTime(timezone=True), nullable=True)


class Role(Base):

	__tablename__ = 'roles'

	id: int = Column(Integer, primary_key=True)
	name: str = Column(String(50), unique=True, nullable=False)
	description: str = Column(String(255), nullable=True)
	is_default: bool = Column(Boolean, default=False)

	permissions = relationship('Permission', secondary=role_permissions, backref='roles')
	users = relationship('User', secondary=user_roles, backref='roles')


class Permission(Base):

	__tablename__ = 'permissions'

	id: int = Column(Integer, primary_key=True)
	name: str = Column(String(100), unique=True, nullable=False)
	resource: str = Column(String(50), nullable=False)
	action: str = Column(String(50), nullable=False)
	description: str = Column(String(255), nullable=True)

	def __repr__(self):
		return f'<Permission {self.name}>'
