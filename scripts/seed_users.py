#!/usr/bin/env python3

import asyncio
import sys

from sqlalchemy import select

from app.database import AsyncLocalSession, engine
from app.models import User
from app.api.auth import hash_password


async def seed_users():

	test_users = [
		('alice', 'alicepass', 'role1'),
		('bob', 'bobpass', 'role2'),
		('admin', 'adminpass', 'admin'),
	]

	async with AsyncLocalSession() as session:
		for username, password, role in test_users:
			result = await session.execute(
				select(User).where(User.username == username)
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
			print(f'Created user: {username} ({role})')

		await session.commit()

	print('Seeding complete!')

async def main():
	try:
		await seed_users()
	finally:
		await engine.dispose()


if __name__ == '__main__':
	asyncio.run(main())
