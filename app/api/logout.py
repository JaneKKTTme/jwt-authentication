from fastapi import APIRouter, Form, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.api.auth import decode_token
from app.core.redis_client import redis_client


router = APIRouter(tags=['auth'])

@router.post('/logout')
async def logout(
    token: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    payload = decode_token(token)
    
    if not payload:
        raise HTTPException(status_code=400, detail='Invalid token')
    
    jti = payload.get('jti')
    if not jti:
        raise HTTPException(status_code=400, detail='Invalid token format')
    
    if not redis_client.is_whitelisted(jti):
        raise HTTPException(status_code=400, detail='Token already inactive')
    
    if redis_client.is_blacklisted(jti):
        raise HTTPException(status_code=400, detail='Token already revoked')
    
    redis_client.add_to_blacklist(jti)
    redis_client.remove_from_whitelist(jti)
    
    return {'msg': 'Successfully logged out'}
