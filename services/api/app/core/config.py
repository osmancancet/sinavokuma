from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=("../../.env", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # PostgreSQL
    database_url: str = "postgresql+asyncpg://sinavokuma:sinavokuma@localhost:5432/sinavokuma"

    # RabbitMQ
    rabbitmq_url: str = "amqp://sinavokuma:sinavokuma@localhost:5672/"
    paper_queue: str = "paper_processing_queue"

    # MinIO
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "sinavokuma"
    minio_secret_key: str = "sinavokuma123"
    minio_bucket: str = "sinav-kagitlari"
    minio_secure: bool = False
    presigned_url_ttl_seconds: int = 900

    # Güvenlik
    jwt_secret_key: str = "gelistirme-icin-guvensiz-anahtar-uretimde-degistirin"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    # API
    api_port: int = 8000
    cors_origins: str = "http://localhost:3000"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
