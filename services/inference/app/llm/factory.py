import logging

from app.config import settings
from app.llm.base import LLMEngine

logger = logging.getLogger(__name__)

_engine: LLMEngine | None = None


def get_llm() -> LLMEngine:
    """Puanlama motoru. HTR motorundan BAĞIMSIZ seçilir (SRS §1.4)."""
    global _engine
    if _engine is not None:
        return _engine

    name = settings.grading_engine.lower()
    if name == "mock":
        from app.llm.mock import MockLLM

        _engine = MockLLM()
    elif name == "qwen_text_mlx":
        from app.llm.qwen_text_mlx import QwenTextMLXLLM

        _engine = QwenTextMLXLLM(settings.grading_mlx_model, settings.grading_max_tokens)
    elif name == "qwen_cuda":
        from app.llm.qwen_cuda import QwenCUDALLM

        _engine = QwenCUDALLM(settings.grading_cuda_model, settings.grading_max_tokens)
    else:
        raise ValueError(
            f"Bilinmeyen GRADING_ENGINE: {settings.grading_engine!r}. "
            "Geçerli değerler: mock, qwen_text_mlx, qwen_cuda"
        )

    logger.info("Puanlama motoru: %s (%s)", name, getattr(_engine, "model_path", "-"))
    return _engine
