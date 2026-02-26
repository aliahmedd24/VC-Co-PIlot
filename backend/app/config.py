from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql+asyncpg://vccopilot:vccopilot@localhost:5432/vccopilot"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # JWT
    jwt_secret_key: str = "change-me-to-a-random-secret-key"
    jwt_algorithm: str = "HS256"
    jwt_expire_hours: int = 24

    # S3 / MinIO
    s3_endpoint_url: str = "http://localhost:9000"
    s3_access_key: str = "minioadmin"
    s3_secret_key: str = "minioadmin"
    s3_bucket_name: str = "vccopilot-documents"
    s3_region: str = "us-east-1"

    # OpenAI
    openai_api_key: str = ""

    # Anthropic (entity extraction)
    anthropic_api_key: str = ""

    # Tavily (web search for agents)
    tavily_api_key: str = ""

    # CORS
    cors_origins: list[str] = ["http://localhost:3000"]

    # App
    app_name: str = "AI VC Co-Pilot"
    debug: bool = True

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
