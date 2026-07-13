from app import mlx_backend
from app.llm.base import LLMEngine


class QwenMLXLLM(LLMEngine):
    """Puanlama için Qwen2.5-VL'in metin yeteneğini kullanır.

    HTR motoruyla AYNI model örneğini paylaşır (mlx_backend tek kopya tutar) —
    16 GB'ta iki model yüklemek belleği tüketirdi.
    """

    def __init__(self, model_path: str, max_tokens: int = 2048) -> None:
        self.model_path = model_path
        self.max_tokens = max_tokens

    def warmup(self) -> None:
        mlx_backend.warmup(self.model_path)

    def generate(self, prompt: str) -> str:
        return mlx_backend.generate(self.model_path, prompt, max_tokens=self.max_tokens)
