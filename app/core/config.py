from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):

	database_url: str = Field(
		default='postgresql+asyncpg://postgres:postgres@postgres:5432/auth_db',
		env='DATABASE_URL'
	)

	secret_key: str = Field(
		default='dev-secret-key-change-in-production',
		env='SECRET_KEY'
	)

	algorithm: str = Field(
		default='HS256',
		env='ALGORITHM'
	)

	access_token_expire_minutes: int = Field(
		default=30,
		env='ACCESS_TOKEN_EXPIRE_MINUTES'
	)

	class Config:
		env_file = '.env'
		extra = 'forbid'


settings = Settings()