from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):

	database_url: str = Field(
		default='postgresql+asyncpg://postgres:postgres@postgres:5432/auth_db',
		validation_alias='DATABASE_URL'
	)

	test_database_url: str = Field(
		default='sqlite+aiosqlite:///:memory:',
		validation_alias='TEST_DATABASE_URL'
	)

	secret_key: str = Field(
		default='dev-secret-key-change-in-production',
		validation_alias='SECRET_KEY'
	)

	algorithm: str = Field(
		default='HS256',
		validation_alias='ALGORITHM'
	)

	access_token_expire_minutes: int = Field(
		default=30,
		validation_alias='ACCESS_TOKEN_EXPIRE_MINUTES'
	)

	redis_url: str = Field(
		default='redis://redis:6379/0',
		validation_alias='REDIS_URL'
	)

	@property
	def whitelist_ttl(self) -> int:
		return self.access_token_expire_minutes * 60

	model_config = SettingsConfigDict(
		env_file='.env',
		env_file_encoding='utf-8',
		extra='forbid',
		case_sensitive=True,
	)


settings = Settings()
