from typing import Generator

import pytest
from httpx import AsyncClient

from app.main import app
from app.core.config import settings


@pytest.fixture(autouse=True)
def reset_settings():
	original_secret = settings.secret_key
	original_algorithm = settings.algorithm
	original_expire = settings.access_token_expire_minutes
		
	settings.secret_key = "test-secret-key"
	settings.algorithm = "HS256"
	settings.access_token_expire_minutes = 30
	
	yield
	
	settings.secret_key = original_secret
	settings.algorithm = original_algorithm
	settings.access_token_expire_minutes = original_expire

@pytest.fixture
async def client() -> AsyncGenerator:
	async with AsyncClient(app=app, base_url='http://test') as async_client:
		yield async_client
