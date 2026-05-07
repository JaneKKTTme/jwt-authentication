#!/usr/bin/env python3

import asyncio
from sqlalchemy import text

from app.database import AsyncLocalSession, engine
from app.core.permissions import Permission as PermEnum, PERMISSION_REGISTRY


async def seed_permissions():
    async with AsyncLocalSession() as session:
        for perm_name, meta in PERMISSION_REGISTRY.items():
            check_result = await session.execute(
                text('SELECT id FROM permissions WHERE name = :name'),
                {'name': perm_name}
            )
            existing = check_result.fetchone()
            
            if not existing:
                await session.execute(
                    text('''
                        INSERT INTO permissions (name, resource, action, description)
                        VALUES (:name, :resource, :action, :description)
                    '''),
                    {
                        'name': perm_name,
                        'resource': meta.resource.value,
                        'action': meta.action.value,
                        'description': meta.description
                    }
                )
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
                'permissions': list(PermEnum.all_permissions())
            }
        }
        
        for role_name, config in roles_config.items():
            check_result = await session.execute(
                text('SELECT id FROM roles WHERE name = :name'),
                {'name': role_name}
            )
            role_row = check_result.fetchone()
            
            if not role_row:
                result = await session.execute(
                    text('''
                        INSERT INTO roles (name, description, is_default)
                        VALUES (:name, :description, :is_default)
                        RETURNING id
                    '''),
                    {
                        'name': role_name,
                        'description': config['description'],
                        'is_default': config['is_default']
                    }
                )
                role_id = result.fetchone()[0]
                print(f'Created role: {role_name}')
            else:
                role_id = role_row[0]
            
            for perm_name in config['permissions']:
                perm_result = await session.execute(
                    text('SELECT id FROM permissions WHERE name = :name'),
                    {'name': perm_name}
                )
                perm_row = perm_result.fetchone()
                
                if not perm_row:
                    print(f'  Warning: Permission {perm_name} not found')
                    continue
                
                perm_id = perm_row[0]
                
                link_result = await session.execute(
                    text('''
                        SELECT 1 FROM role_permissions
                        WHERE role_id = :role_id AND permission_id = :perm_id
                    '''),
                    {'role_id': role_id, 'perm_id': perm_id}
                )
                
                if not link_result.fetchone():
                    await session.execute(
                        text('''
                            INSERT INTO role_permissions (role_id, permission_id)
                            VALUES (:role_id, :perm_id)
                        '''),
                        {'role_id': role_id, 'perm_id': perm_id}
                    )
                    print(f'  Added permission {perm_name} to {role_name}')
        
        await session.commit()
        print('Roles seeded successfully!')


async def assign_roles_to_users():
    async with AsyncLocalSession() as session:
        default_role_result = await session.execute(
            text('SELECT id FROM roles WHERE is_default = True LIMIT 1')
        )
        default_role_row = default_role_result.fetchone()
        
        admin_role_result = await session.execute(
            text("SELECT id FROM roles WHERE name = 'admin'")
        )
        admin_role_row = admin_role_result.fetchone()
        
        users_result = await session.execute(
            text('SELECT id, username FROM users')
        )
        users = users_result.fetchall()
        
        for user_id, username in users:
            if username == 'admin' and admin_role_row:
                admin_role_id = admin_role_row[0]
                check_result = await session.execute(
                    text('''
                        SELECT 1 FROM user_roles
                        WHERE user_id = :user_id AND role_id = :role_id
                    '''),
                    {'user_id': user_id, 'role_id': admin_role_id}
                )
                if not check_result.fetchone():
                    await session.execute(
                        text('''
                            INSERT INTO user_roles (user_id, role_id)
                            VALUES (:user_id, :role_id)
                        '''),
                        {'user_id': user_id, 'role_id': admin_role_id}
                    )
                    print(f'Assigned admin role to {username}')
                    
            elif default_role_row:
                default_role_id = default_role_row[0]
                check_result = await session.execute(
                    text('''
                        SELECT 1 FROM user_roles
                        WHERE user_id = :user_id AND role_id = :role_id
                    '''),
                    {'user_id': user_id, 'role_id': default_role_id}
                )
                if not check_result.fetchone():
                    await session.execute(
                        text('''
                            INSERT INTO user_roles (user_id, role_id)
                            VALUES (:user_id, :role_id)
                        '''),
                        {'user_id': user_id, 'role_id': default_role_id}
                    )
                    print(f'Assigned default role to {username}')
        
        await session.commit()
        print('Roles assigned to users successfully!')


async def main():
    try:
        await seed_permissions()
        await seed_roles()
        await assign_roles_to_users()
        print('All seeding completed successfully!')
    except Exception as e:
        print(f'Error during seeding: {e}')
        import traceback
        traceback.print_exc()
    finally:
        await engine.dispose()


if __name__ == '__main__':
    asyncio.run(main())
