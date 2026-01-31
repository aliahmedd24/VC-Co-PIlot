from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Application
    app_name: str = "AI VC Co-Pilot"
    app_version: str = "1.0.0"
    debug: bool = False
    environment: str = "development"

    # API
    api_prefix: str = "/api/v1"
    cors_origins: str = "http://localhost:3000"  # Comma-separated, parsed at runtime

    # Database
    database_url: str
    database_pool_size: int = 5
    database_max_overflow: int = 10

    # Redis
    redis_url: str

    # Auth
    secret_key: str
    access_token_expire_minutes: int = 60 * 24
    algorithm: str = "HS256"

    # AI APIs
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    default_model: str = "claude-sonnet-4-20250514"
    embedding_model: str = "text-embedding-3-small"
    embedding_dimensions: int = 1536

    # Tool APIs
    brave_api_key: str = ""
    serper_api_key: str = ""  # Optional fallback for web search

    # Tool Configuration
    max_tool_iterations: int = 5
    tool_timeout_seconds: int = 30
    enable_tool_use: bool = True

    # Vision Settings
    vision_enabled: bool = False  # Feature flag for vision capabilities
    vision_model: str = "claude-sonnet-4-20250514"  # Model with vision support
    vision_max_images_per_document: int = 50  # Max pages to process per document
    vision_processing_mode: str = "parallel"  # 'parallel' or 'sequential'

    # Vision Rate Limiting & Cost Control
    vision_max_requests_per_minute: int = 50  # API rate limit
    vision_daily_cost_limit: float = 100.0  # USD daily cost limit
    vision_cost_per_image: float = 0.005  # Estimated cost per image

    # Vision Image Processing
    vision_image_max_dimension: int = 1568  # Claude's max dimension
    vision_image_format: str = "PNG"  # Output format
    vision_thumbnail_size: tuple[int, int] = (300, 300)  # Thumbnail dimensions
    vision_target_file_size_kb: int = 500  # Target file size after optimization

    # Vision Caching
    vision_cache_enabled: bool = True  # Enable result caching
    vision_cache_ttl_days: int = 7  # Cache time-to-live

    # Storage
    s3_endpoint: str | None = None
    s3_access_key: str = ""
    s3_secret_key: str = ""
    s3_bucket: str = "uploads"
    s3_region: str = "us-east-1"

    # Celery
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/0"

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse comma-separated CORS origins."""
        return [origin.strip() for origin in self.cors_origins.split(",")]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
