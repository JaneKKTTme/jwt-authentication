from contextlib import asynccontextmanager
from typing import List, Dict, Any

from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import engine, get_db, init_db
from app.models import User


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
