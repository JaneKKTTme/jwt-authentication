from fastapi import APIRouter, Depends, HTTPException, status

from app.core.dependencies import permission_required
from app.core.permissions import Permission


router = APIRouter(prefix='/content', tags=['content'])

@router.get('/common')
async def common_content(
    current_user=Depends(permission_required([Permission.CONTENT_READ_COMMON]))
):
    return {'content': 'This is common content for all roles'}


@router.get('/role1')
async def role1_content(
    current_user=Depends(permission_required([Permission.CONTENT_READ_ROLE1]))
):
    return {'content': 'Exclusive content for Role 1'}


@router.get('/role2')
async def role2_content(
    current_user=Depends(permission_required([Permission.CONTENT_READ_ROLE2]))
):
    return {'content': 'Exclusive content for Role 2'}

@router.get('/admin')
async def admin_content(
    current_user=Depends(permission_required([Permission.CONTENT_READ_ADMIN]))
):
    return {'content': 'Admin dashboard'}
