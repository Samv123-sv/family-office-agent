from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    DATABASE_URL: str
    ANTHROPIC_API_KEY: str
    REDIS_URL: str
    CLERK_SECRET_KEY: str
    TWILIO_ACCOUNT_SID: str
    TWILIO_AUTH_TOKEN: str
    TWILIO_FROM_NUMBER: str
    GITHUB_TOKEN: str | None = None  # optional — raises GitHub rate limit from 60 to 5000 req/hr
    ALLOWED_ORIGINS: str = "http://localhost:3000"


settings = Settings()
