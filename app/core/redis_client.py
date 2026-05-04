import logging
from typing import Optional

import redis

from app.core.config import settings


logger = logging.getLogger(__name__)

class RedisClient:

	def __init__(self):
		self.client: Optional[redis.Redis] = None

	def connect(self) -> bool:
		try:
			self.client = redis.Redis.from_url(
				settings.redis_url,
				decode_responses=True
			)
			self.client.ping()
			logger.info('Redis connected')
			return True
		except Exception as e:
			logger.error(f'Redis connection failed: {e}')
			self.client = None
			return False

	def add_to_whitelist(self, jti: str, username: str, role: str) -> bool:
		if not self.client:
			return False
		key = f'whitelist:{jti}'
		self.client.hset(key, mapping={'username': username, 'role': role})
		self.client.expire(key, settings.whitelist_ttl)
		return True

	def is_whitelisted(self, jti: str) -> bool:
		if not self.client:
			return False
		return self.client.exists(f'whitelist:{jti}') == 1

	def remove_from_whitelist(self, jti: str) -> bool:
		if not self.client:
			return False
		return self.client.delete(f'whitelist:{jti}') > 0

	def add_to_blacklist(self, jti: str) -> bool:
		if not self.client:
			return False
		key = f'blacklist:{jti}'
		self.client.setex(key, 3600, 'revoked')
		return True

	def is_blacklisted(self, jti: str) -> bool:
		if not self.client:
			return False
		return self.client.exists(f'blacklist:{jti}') == 1

	def ping(self) -> bool:
		try:
			return bool(self.client and self.client.ping())
		except Exception:
			return False

	def close(self):
		if self.client:
			self.client.close()


redis_client = RedisClient()
