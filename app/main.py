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
from app.api.logout import router as logout_router
from app.api.admin import router as admin_router
from app.api.content import router as content_router
from app.core.dependencies import get_current_user
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
app.include_router(logout_router)
app.include_router(admin_router)
app.include_router(content_router)

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
async def read_me(current_user: dict = Depends(get_current_user)):
	return {
		'username': current_user.get('sub'),
		'role': current_user.get('role'),
		'user_id': current_user.get('user_id')
	}

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

	await db.refresh(user, attribute_names=['roles'])
	user_role = user.roles[0].name if user.roles else user_data.role

	return UserResponse(
		id=user.id,
		username=user.username,
		role=user_role
	)
