#!/usr/bin/env python3

import asyncio

from sqlalchemy import select

from app.database import AsyncLocalSession, engine
from app.models import Permission, Role, user_roles, role_permissions
from app.core.permissions import Permission as PermEnum, PERMISSION_REGISTRY


async def seed_permissions():
    async with AsyncLocalSession() as session:
        for perm_name, meta in PERMISSION_REGISTRY.items():
            result = await session.execute(
                select(Permission).where(Permission.name == perm_name)
            )
            existing = result.scalar_one_or_none()
            
            if not existing:
                perm = Permission(
                    name=perm_name,
                    resource=meta.resource.value,
                    action=meta.action.value,
                    description=meta.description
                )
                session.add(perm)
                print(f'Created permission: {perm_name}')
        
        await session.commit()
        print('Permissions seeded successfully!')

async def seed_roles():
    async with AsyncLocalSession() as session:
        roles_config = {
            'role1': {
                'description': 'Basic user with role1 access',
                'is_default': True,
                'permissions': [
                    PermEnum.CONTENT_READ_COMMON,
                    PermEnum.CONTENT_READ_ROLE1,
                ]
            },
            'role2': {
                'description': 'Basic user with role2 access',
                'is_default': False,
                'permissions': [
                    PermEnum.CONTENT_READ_COMMON,
                    PermEnum.CONTENT_READ_ROLE2,
                ]
            },
            'admin': {
                'description': 'Administrator with full access',
                'is_default': False,
                'permissions': PermEnum.all_permissions()
            }
        }
        
        for role_name, config in roles_config.items():
            result = await session.execute(
                select(Role).where(Role.name == role_name)
            )
            role = result.scalar_one_or_none()
            
            if not role:
                role = Role(
                    name=role_name,
                    description=config['description'],
                    is_default=config['is_default']
                )
                session.add(role)
                await session.flush()
                print(f'Created role: {role_name}')
            
            for perm_name in config['permissions']:
                perm_result = await session.execute(
                    select(Permission).where(Permission.name == perm_name)
                )
                perm = perm_result.scalar_one_or_none()
                
                if perm and perm not in role.permissions:
                    role.permissions.append(perm)
                    print(f'  Added permission {perm_name} to {role_name}')
        
        await session.commit()
        print('Roles seeded successfully!')


async def assign_roles_to_users():
    async with AsyncLocalSession() as session:
        default_role_result = await session.execute(
            select(Role).where(Role.is_default == True)
        )
        default_role = default_role_result.scalar_one_or_none()
        
        admin_role_result = await session.execute(
            select(Role).where(Role.name == 'admin')
        )
        admin_role = admin_role_result.scalar_one_or_none()
        
        from app.models import User
        users_result = await session.execute(select(User))
        users = users_result.scalars().all()
        
        for user in users:
            if user.username == 'admin' and admin_role:
                if admin_role not in user.roles:
                    user.roles.append(admin_role)
                    print(f'Assigned admin role to {user.username}')
            elif default_role:
                if default_role not in user.roles:
                    user.roles.append(default_role)
                    print(f'Assigned default role ({default_role.name}) to {user.username}')
        
        await session.commit()


async def main():
    try:
        await seed_permissions()
        await seed_roles()
        await assign_roles_to_users()
    finally:
        await engine.dispose()


if __name__ == '__main__':
    asyncio.run(main())
