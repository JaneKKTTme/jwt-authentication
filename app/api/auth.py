import uuid
from datetime import datetime, timedelta, timezone

import bcrypt
from fastapi import APIRouter, Request, HTTPException, Depends
from jose import jwt, JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import User
from app.core.config import settings
from app.core.redis_client import redis_client


router = APIRouter(tags=['auth'])

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

	if 'jti' not in data:
		raise ValueError('jti claim is required in token payload')

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

async def get_user_by_username(db: AsyncSession, username: str) -> User | None:
	result = await db.execute(select(User).where(User.username == username))
	return result.scalar_one_or_none()

async def authenticate_user(db: AsyncSession, username: str, password: str) -> User | None:
	user = await get_user_by_username(db, username)
	if not user or not verify_password(password, user.hashed_password):
		return None
	if not user.is_active:
		return None
	return user

async def create_user_token(user: User) -> tuple[str, str]:
	jti = str(uuid.uuid4())
	token = create_access_token({
		'sub': user.username,
		'role': user.role, 
		'jti': jti,
		'user_id': user.id
	})
	redis_client.add_to_whitelist(jti, user.username, user.role)
	return token, jti

@router.post('/login')
async def login(
	request: Request, 
	username: str,
	password: str,
	db: AsyncSession = Depends(get_db)
):
	user = await authenticate_user(db, username, password)
	if not user:
		raise HTTPException(status_code=401, detail='Invalid credentials')

	user.last_login = datetime.now(timezone.utc)
	await db.commit()

	token, _ = await create_user_token(user)
	return {'access_token': token, 'token_type': 'bearer', 'role': user.role}
	