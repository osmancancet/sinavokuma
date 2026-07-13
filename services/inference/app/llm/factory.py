import logging

from app.config import settings
from app.llm.base import LLMEngine

logger = logging.getLogger(__name__)

_engine: LLMEngine | None = None


def get_llm() -> LLMEngine:
    global _engine
    if _engine is not None:
        return _engine

    name = settings.htr_engine.lower()
    if name == "mock":
        from app.llm.mock import MockLLM

        _engine = MockLLM()
    elif name == "qwen_mlx":
        from app.llm.qwen_mlx import QwenMLXLLM

        _engine = QwenMLXLLM(settings.qwen_mlx_model, settings.grading_max_tokens)
    elif name == "qwen_cuda":
        from app.llm.qwen_cuda import QwenCUDALLM

        _engine = QwenCUDALLM(settings.qwen_cuda_model, settings.grading_max_tokens)
    else:
        raise ValueError(f"Bilinmeyen HTR_ENGINE: {settings.htr_engine!r}")

    logger.info("Puanlama motoru: %s", name)
    return _engine
