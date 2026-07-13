"""Rubrik puanlamasını yapan metin modeli soyutlaması.

HTR'dan ayrı tutuluyor: SRS §1.4 okuma ve puanlama için farklı modeller öngörüyor.
Şu an ikisi de aynı Qwen2.5-VL örneğini kullanıyor (16 GB bellek kısıtı), ama
arayüz ayrı olduğu için ileride ayrı bir puanlama modeli takmak tek satırlık iş.
"""

from abc import ABC, abstractmethod


class LLMEngine(ABC):
    @abstractmethod
    def generate(self, prompt: str) -> str:
        """Verilen prompt'a metin yanıtı üretir."""

    def warmup(self) -> None:  # noqa: B027 — bilerek soyut değil: mock motorun ısınmaya ihtiyacı yok
        """Modeli belleğe yükler."""
