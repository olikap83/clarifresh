from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    database_url: str = "postgresql+asyncpg://user:password@localhost:5432/clarifresh"

    apify_api_token: str = ""
    apify_tiktok_actor_id: str = "clockworks~tiktok-scraper"
    apify_instagram_actor_id: str = "apify~instagram-scraper"
    apify_max_posts_per_run: int = 50
    apify_poll_interval_seconds: int = 10
    apify_poll_timeout_seconds: int = 300

    anthropic_api_key: str = ""
    claude_model: str = "claude-sonnet-4-6"

    sentiment_cache_hours: int = 6
    retention_days: int = 14


settings = Settings()
