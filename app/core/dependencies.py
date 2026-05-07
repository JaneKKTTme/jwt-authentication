from datetime import datetime, timezone
from typing import List, Set

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Session as SessionModel, User, Role, role_permissions, Permission as PermissionModel
from app.api.auth import decode_token
from app.core.permissions import Permission, expand_permissions_with_dependencies
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

    if session.expired_at and session.expired_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail='Session expired')
    
    return payload

async def get_user_permissions(user_id: int, db: AsyncSession) -> Set[str]:
    result = await db.execute(
        select(PermissionModel.name)
        .select_from(User)
        .join(user_roles, User.id == user_roles.c.user_id)
        .join(Role, user_roles.c.role_id == Role.id)
        .join(role_permissions, Role.id == role_permissions.c.role_id)
        .join(PermissionModel, role_permissions.c.permission_id == PermissionModel.id)
        .where(User.id == user_id)
    )
    return {row[0] for row in result.all()}

def permission_required(required_permissions: List[str]):
    async def checker(
        current_user: dict = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
    ):
        user_id = current_user.get('user_id')
        user_permissions = await get_user_permissions(user_id, db)

        missing = [p for p in required_permissions if p not in user_permissions]
        if missing:
            raise HTTPException(
                status_code=403, 
                detail=f'Missing permissions: {", ".join(missing)}'
            )
        return current_user
    return checker
