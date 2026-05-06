import logging
from contextlib import asynccontextmanager
from typing import List, Dict, Any

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from sqlalchemy import text, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import engine, get_db, init_db
from app.models import User
from app.api.auth import router as auth_router
from app.api.auth import create_user
from app.core.redis_client import redis_client
from app.core.schemas import UserCreate, UserResponse


logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
	await init_db()
	redis_client.connect()
	logger.info('Redis initialized')
	yield

	await engine.dispose()
	if redis_client.client:
		redis_client.client.close()

app = FastAPI(title='Auth System', lifespan=lifespan)

app.include_router(auth_router)

security = HTTPBearer()


@app.get('/')
async def root():
	return {'status': 'ok', 'message': 'Auth system placeholder'}

@app.get('/ping')
async def ping():
	return 'ping'

@app.get('/health/db')
async def check_db(db: AsyncSession = Depends(get_db)):
	await db.execute(text('SELECT 1'))
	return {'database': 'connected'}

@app.get('/me')
async def read_me(credentials: HTTPAuthorizationCredentials = Depends(security)):
	token = credentials.credentials
	payload = decode_token(token)
	if not payload:
		raise HTTPException(status_code=401, detail='Invalid token')

	jti = payload.get('jti')
	if not jti or not redis_client.is_whitelisted(jti):
		raise HTTPException(status_code=401, detail='Token not active')

	return {
		'username': payload.get('sub'),
		'role': payload.get('role'),
		'user_id': payload.get('user_id')
	}

@app.get('/users')
async def get_users(db: AsyncSession = Depends(get_db)) -> List[Dict[str, Any]]:
	try: 
		result = await db.execute(
			text('SELECT id, username, role, is_active, created_at FROM users')
		)
		users = result.fetchall()
		return [dict(user._mapping) for user in users]
	except Exception as e:
		raise HTTPException(status_code=500, detail=str(e))

@app.post('/register', response_model=UserResponse)
async def register(
	user_data: UserCreate,
	db: AsyncSession = Depends(get_db)
):
	result = await db.execute(
		select(User).where(User.username == user_data.username)
	)
	if result.scalar_one_or_none():
		raise HTTPException(status_code=400, detail='Username already exists')

	user = await create_user(
		db=db,
		username=user_data.username,
		password=user_data.password,
		role=user_data.role
	)

	return UserResponse(
		id=user.id,
		username=user.username,
		role=user.role
	)
