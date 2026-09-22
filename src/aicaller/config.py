from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Aicaller"
    app_version: str = "0.1.0"
    app_env: str = "development"
    host: str = "0.0.0.0"
    port: int = 8000
    telephony_provider: str = "exotel"
    database_url: str = ""
    redis_url: str = ""
    object_storage_endpoint: str = ""
    object_storage_bucket: str = ""
    object_storage_access_key: str = ""
    object_storage_secret_key: str = ""
    exotel_api_key: str = ""
    exotel_api_token: str = ""
    ai_provider: str = "openai"
    openai_api_key: str = ""
    human_ring_seconds: float = 7.0
    ai_answer_timeout_seconds: float = 3.0
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()
