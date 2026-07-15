from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=("../../.env", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = "postgresql+asyncpg://sinavokuma:sinavokuma@localhost:5432/sinavokuma"

    rabbitmq_url: str = "amqp://sinavokuma:sinavokuma@localhost:5672/"
    paper_queue: str = "paper_processing_queue"

    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "sinavokuma"
    minio_secret_key: str = "sinavokuma123"
    minio_bucket: str = "sinav-kagitlari"
    minio_secure: bool = False

    # ── HTR (el yazısı okuma) ──
    # mock | qwen_mlx | qwen_cuda
    htr_engine: str = "mock"
    qwen_mlx_model: str = "mlx-community/Qwen2.5-VL-3B-Instruct-4bit"
    qwen_cuda_model: str = "Qwen/Qwen2.5-VL-7B-Instruct"
    htr_max_tokens: int = 1024

    # ── Puanlama (rubrik akıl yürütmesi) — HTR'dan AYRI model ──
    # SRS §1.4 zaten ayrı öngörüyordu. Ölçüm doğruladı: 3B-VL okumada iyi, akıl
    # yürütmede yetersiz (gerekçe olarak tekrar eden dejenere metin üretiyor).
    # mock | qwen_text_mlx | qwen_cuda
    grading_engine: str = "mock"
    grading_mlx_model: str = "mlx-community/Qwen2.5-7B-Instruct-4bit"
    grading_cuda_model: str = "Qwen/Qwen2.5-14B-Instruct"
    grading_max_tokens: int = 2560

    # SRS §1.3: GPU'yu boğmamak için aynı anda tek kağıt işlenir.
    prefetch_count: int = 1


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
