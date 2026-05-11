from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import inspect, select
from fakeredis import FakeRedis
from unittest.mock import patch

from app.main import app
from app.database import Base, get_db
from app.models import User, Role, Permission
from app.api.auth import hash_password
from app.core.config import settings


@pytest.fixture(autouse=True)
def reset_settings():
	original_secret = settings.secret_key
	original_algorithm = settings.algorithm
	original_expire = settings.access_token_expire_minutes
		
	settings.secret_key = 'test-secret-key'
	settings.algorithm = 'HS256'
	settings.access_token_expire_minutes = 30
	
	yield
	
	settings.secret_key = original_secret
	settings.algorithm = original_algorithm
	settings.access_token_expire_minutes = original_expire

@pytest.fixture
async def client() -> AsyncGenerator:
	async with AsyncClient(app=app, base_url='http://test') as async_client:
		yield async_client

@pytest_asyncio.fixture(autouse=True)
async def setup_database():
	engine = create_async_engine(settings.test_database_url, echo=False)
	
	async with engine.begin() as conn:
		await conn.run_sync(Base.metadata.drop_all)
		await conn.run_sync(Base.metadata.create_all)
	
	async def override_get_db():
		async_session = async_sessionmaker(engine, expire_on_commit=False)
		async with async_session() as session:
			yield session
	
	app.dependency_overrides[get_db] = override_get_db
	
	async with async_sessionmaker(engine, expire_on_commit=False)() as session:
		from app.core.permissions import Permission as PermEnum, PERMISSION_REGISTRY
		
		for perm_name, meta in PERMISSION_REGISTRY.items():
			permission = Permission(
				name=perm_name,
				resource=meta.resource.value,
				action=meta.action.value,
				description=meta.description
			)
			session.add(permission)
		await session.commit()
		print(f'DEBUG: Created {len(PERMISSION_REGISTRY)} permissions')

		roles = {
			'role1': Role(name='role1', description='Role 1', is_default=True),
			'role2': Role(name='role2', description='Role 2', is_default=False),
			'admin': Role(name='admin', description='Admin', is_default=False),
		}
		for role in roles.values():
			session.add(role)
		await session.commit()

		role1 = (await session.execute(select(Role).where(Role.name == 'role1'))).scalar_one()
		role2 = (await session.execute(select(Role).where(Role.name == 'role2'))).scalar_one()
		admin_role = (await session.execute(select(Role).where(Role.name == 'admin'))).scalar_one()
		
		perm_common = (await session.execute(select(Permission).where(Permission.name == PermEnum.CONTENT_READ_COMMON))).scalar_one()
		perm_role1 = (await session.execute(select(Permission).where(Permission.name == PermEnum.CONTENT_READ_ROLE1))).scalar_one()
		perm_role2 = (await session.execute(select(Permission).where(Permission.name == PermEnum.CONTENT_READ_ROLE2))).scalar_one()
		perm_admin = (await session.execute(select(Permission).where(Permission.name == PermEnum.CONTENT_READ_ADMIN))).scalar_one()
		
		from app.models import role_permissions
		
		await session.execute(role_permissions.insert().values(role_id=role1.id, permission_id=perm_common.id))
		await session.execute(role_permissions.insert().values(role_id=role1.id, permission_id=perm_role1.id))
		
		await session.execute(role_permissions.insert().values(role_id=role2.id, permission_id=perm_common.id))
		await session.execute(role_permissions.insert().values(role_id=role2.id, permission_id=perm_role2.id))
		
		await session.execute(role_permissions.insert().values(role_id=admin_role.id, permission_id=perm_common.id))
		await session.execute(role_permissions.insert().values(role_id=admin_role.id, permission_id=perm_admin.id))
		
		await session.commit()

		users_data = [
			('alice', 'alicepass', 'role1'),
			('bob', 'bobpass', 'role2'),
			('admin', 'adminpass', 'admin'),
		]
		
		for username, password, role_name in users_data:
			user = User(
				username=username,
				hashed_password=hash_password(password),
				is_active=True
			)
			session.add(user)
			await session.flush()

			role_result = await session.execute(
				select(Role).where(Role.name == role_name)
			)
			role = role_result.scalar_one_or_none()
			if role:
				from app.models import user_roles
				await session.execute(
					user_roles.insert().values(user_id=user.id, role_id=role.id)
				)
		
		await session.commit()
	yield
	
	app.dependency_overrides.clear()
	await engine.dispose()


@pytest.fixture(autouse=True)
async def setup_redis():
	from app.core import redis_client as redis_module

	fake_redis = FakeRedis()

	original = redis_module.redis_client.client
	redis_module.redis_client.client = fake_redis
	yield
	redis_module.redis_client.client = original
	fake_redis.flushall()
