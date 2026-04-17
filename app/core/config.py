from pydantic_settings import BaseSettings

class Settings(BaseSettings):

	database_url: str = 'postgresql+asyncpg://postgres:postgres@postgres:5432/auth_db'

	class Config:
		env_file = '.env'
		extra = 'ignore'


settings = Settings()