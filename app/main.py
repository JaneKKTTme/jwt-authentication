from fastapi import FastAPI, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db

app = FastAPI()

@app.get('/')
async def root():
	return {'status': 'ok', 'message': 'Auth system placeholder'}

@app.get('/ping')
async def ping():
	return 'ping'

@app.get('/health/db')
async def chech_db(db: AsyncSession = Depends(get_db)):
	await db.execute(text('SELECT 1'))
	return {'database': 'connected'}
