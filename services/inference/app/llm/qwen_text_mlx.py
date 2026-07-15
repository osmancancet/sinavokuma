"""Rubrik puanlaması için AYRI ve daha büyük bir metin modeli (MLX).

Neden ayrı: ölçüm gösterdi ki Qwen2.5-VL-3B görsel okumada mükemmel ama akıl
yürütmede yetersiz — gerekçe olarak aynı cümleyi tekrarlayan dejenere metin
üretiyordu ("...döngü mantığı doğru ve doğru bir yol izlemiş olduğunu belirlemek
için döngü mantığı kriterine bakabiliriz." ×3).

Bir akademisyen böyle bir gerekçeyi okuduğunda sisteme güvenmeyi bırakır.
Gerekçe, ürünün asıl teslim ettiği şey — puandan bile önemli.

SRS §1.4 zaten okuma ve puanlama için ayrı modeller öngörüyordu. Doğruymuş.

Bellek: 3B-VL (~2.5 GB) + 7B metin (~4.5 GB) = ~7 GB. 16 GB'lık makinede Docker
ve Next.js ile birlikte sığar.
"""

import logging
import threading

from app.llm.base import LLMEngine

logger = logging.getLogger(__name__)

_lock = threading.Lock()
_loaded: dict[str, tuple] = {}


def _load(model_path: str) -> tuple:
    with _lock:
        if model_path in _loaded:
            return _loaded[model_path]
        from mlx_lm import load

        logger.info("Puanlama modeli yükleniyor: %s", model_path)
        _loaded[model_path] = load(model_path)
        logger.info("Puanlama modeli belleğe alındı.")
        return _loaded[model_path]


class QwenTextMLXLLM(LLMEngine):
    def __init__(self, model_path: str, max_tokens: int = 2048) -> None:
        self.model_path = model_path
        self.max_tokens = max_tokens

    def warmup(self) -> None:
        _load(self.model_path)

    def generate(self, prompt: str) -> str:
        model, tokenizer = _load(self.model_path)

        from mlx_lm import generate as mlx_generate

        messages = [{"role": "user", "content": prompt}]
        formatted = tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        text = mlx_generate(
            model, tokenizer, prompt=formatted, max_tokens=self.max_tokens, verbose=False
        )
        return text.strip()
