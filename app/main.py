from contextlib import asynccontextmanager
from typing import List, Dict, Any

from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import text, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import engine, get_db, init_db
from app.models import User
from app.core.schemas import UserCreate, UserResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
	await init_db()
	yield

	await engine.dispose()

app = FastAPI(title='Auth System', lifespan=lifespan)


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

	user = User.create(
		username=user_data.username,
		password=user_data.password,
		role=user_data.role
	)
	db.add(user)
	await db.commit()
	await db.refresh(user)

	return UserResponse(
		id=user.id,
		username=user.username,
		role=user.role
	)
