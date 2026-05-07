from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.core.permissions import Permission
from app.core.dependencies import permission_required


router = APIRouter(prefix='/admin', tags=['admin'])

@router.get('/users')
async def list_users(
    db: AsyncSession = Depends(get_db),
    _=Depends(permission_required([Permission.USERS_READ]))
):
    try: 
        result = await db.execute(
            text('SELECT id, username, role, is_active, created_at FROM users')
        )
        users = result.fetchall()
        return [dict(user._mapping) for user in users]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))    

