from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Session as SessionModel
from app.api.auth import decode_token
from app.core.redis_client import redis_client


security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> dict:
    token = credentials.credentials
    payload = decode_token(token)
    
    if not payload:
        raise HTTPException(status_code=401, detail='Invalid token')
    
    jti = payload.get('jti')
    if not jti:
        raise HTTPException(status_code=401, detail='Invalid token format')
    
    if not redis_client.is_whitelisted(jti):
        raise HTTPException(status_code=401, detail='Token not active')
    
    if redis_client.is_blacklisted(jti):
        raise HTTPException(status_code=401, detail='Token revoked')

    result = await db.execute(
        select(SessionModel).where(SessionModel.jti == jti)
    )
    session = result.scalar_one_or_none()
    if not session or session.revoked_at:
        redis_client.add_to_blacklist(jti)
        redis_client.remove_from_whitelist(jti)
        raise HTTPException(status_code=401, detail='Session expired or revoked')
    
    return payload
