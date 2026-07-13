"""Motor seçimi tek noktadan. Çağıran kod hangi motorun döndüğünü bilmez."""

import logging

from app.config import settings
from app.htr.base import HTREngine

logger = logging.getLogger(__name__)

_engine: HTREngine | None = None


def get_engine() -> HTREngine:
    global _engine
    if _engine is not None:
        return _engine

    name = settings.htr_engine.lower()
    if name == "mock":
        from app.htr.mock import MockHTR

        _engine = MockHTR()
    elif name == "qwen_mlx":
        from app.htr.qwen_mlx import QwenMLXEngine

        _engine = QwenMLXEngine(settings.qwen_mlx_model, settings.htr_max_tokens)
    elif name == "qwen_cuda":
        from app.htr.qwen_cuda import QwenCUDAEngine

        _engine = QwenCUDAEngine(settings.qwen_cuda_model, settings.htr_max_tokens)
    else:
        raise ValueError(
            f"Bilinmeyen HTR_ENGINE: {settings.htr_engine!r}. "
            "Geçerli değerler: mock, qwen_mlx, qwen_cuda"
        )

    logger.info("HTR motoru: %s", name)
    return _engine
