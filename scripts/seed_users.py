#!/usr/bin/env python3

import asyncio

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.database import AsyncLocalSession, engine
from app.models import User, Role
from app.api.auth import hash_password


async def seed_users():

	test_users = [
		('alice', 'alicepass', 'role1'),
		('bob', 'bobpass', 'role2'),
		('admin', 'adminpass', 'admin'),
	]

	async with AsyncLocalSession() as session:
		for username, password, role_name in test_users:
			result = await session.execute(
				select(User)
				.where(User.username == username)
				.options(selectinload(User.roles))
			)
			existing = result.scalar_one_or_none()

			if existing:
				print(f'User {username} already exists, skipping')
				continue

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
				print(f'Created user: {username} with role {role_name}')
			else:
				print(f'Warning: role {role_name} not found for user {username}')

		await session.commit()

	print('Seeding complete!')

async def main():
	try:
		from app.database import init_db
		await init_db()

		await seed_users()
	except Exception as e:
		print(f'Error: {e}')
		import traceback
		traceback.print_exc()
	finally:
		await engine.dispose()


if __name__ == '__main__':
	asyncio.run(main())
