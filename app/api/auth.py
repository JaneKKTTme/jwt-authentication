import uuid
from datetime import datetime, timedelta, timezone

import bcrypt
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User
from app.core.config import settings


def hash_password(password: str) -> str:
	salt = bcrypt.gensalt()
	return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(suggested_password: str, hashed_password: str) -> bool:
	return bcrypt.checkpw(
			suggested_password.encode('utf-8'),
			hashed_password.encode('utf-8')
		)

def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
	to_encode = data.copy()

	if 'jti' not in to_encode:
		to_encode['jti'] = str(uuid.uuid4())

	expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=settings.access_token_expire_minutes))
	to_encode.update({'exp': expire})
	return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)

def decode_token(token: str) -> dict | None:
	try:
		return jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
	except JWTError:
		return None

async def create_user(db: AsyncSession, username: str, password: str, role: str = 'user') -> User:
	hashed_password = hash_password(password)
	user = User(
		username=username,
		hashed_password=hashed_password,
		role=role,
		is_active=True
	)
	db.add(user)
	await db.commit()
	await db.refresh(user)
	return user
	