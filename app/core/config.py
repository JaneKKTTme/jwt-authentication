from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):

	database_url: str = Field(
		default='postgresql+asyncpg://postgres:postgres@postgres:5432/auth_db',
		env='DATABASE_URL'
	)

	class Config:
		env_file = '.env'
		extra = 'forbid'


settings = Settings()