from pydantic_settings import BaseSettings, SettingsConfigDict

from .db_url import backend_local_db_url


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)

    app_env: str = "dev"
    auto_create_tables: bool = False
    log_level: str = "INFO"
    log_json: bool = False
    app_api_key: str | None = None
    app_read_api_key: str | None = None
    app_write_api_key: str | None = None
    auth_enforce_read: bool = False

    # JWT Authentication settings
    jwt_secret_key: str = "CHANGE_ME_IN_PRODUCTION_use_openssl_rand_hex_32"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7
    auth_mode: str = "jwt"  # "jwt" or "api_key" for backward compatibility
    database_url: str = backend_local_db_url()
    redis_url: str = "redis://localhost:6379/0"
    timezone: str = "Africa/Johannesburg"
    posting_window_start: str = "08:00"
    posting_window_end: str = "17:00"
    posting_enabled: bool = True
    comment_replies_enabled: bool = True
    max_auto_replies: int = 5
    escalation_follower_threshold: int = 10000
    telegram_bot_token: str | None = None
    telegram_chat_id: str | None = None
    kill_switch: bool = False
    llm_provider: str = "claude"
    llm_api_key: str | None = None
    llm_model: str = "claude-3-5-sonnet-latest"
    llm_mock_mode: bool = False  # Force mock mode even if API key is set
    anthropic_base_url: str = "https://api.anthropic.com/v1/messages"
    linkedin_api_mode: str = "manual"
    linkedin_api_token: str | None = None
    linkedin_api_base_url: str = "https://api.linkedin.com"
    linkedin_api_timeout_seconds: int = 10
    linkedin_api_retries: int = 2
    linkedin_api_page_size: int = 25
    linkedin_mock_comments_json: str = ""
    research_feed_urls: str = ""
    cors_allowed_origins: str = "http://127.0.0.1:5173,http://localhost:5173"


settings = Settings()
