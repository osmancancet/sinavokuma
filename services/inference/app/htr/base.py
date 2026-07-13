"""SRS §2 (Çözüm) — HTR (Handwritten Text Recognition) soyutlaması.

İş mantığı hangi modelin çalıştığını BİLMEZ. Üç uygulama var:

  MockHTR       -> model indirmeden tüm boru hattını test etmek için (SRS GÖREV 5)
  QwenMLXEngine -> Apple Silicon / Metal, yerel geliştirme
  QwenCUDAEngine-> prod GPU sunucusu

Motor seçimi HTR_ENGINE ortam değişkeniyle yapılır. Modeli değiştirmek tek satırlık
config değişikliğidir — çağıran kodda hiçbir şey değişmez.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class HTRResult:
    text: str
    # Modelin kendi güven skoru. Mock'ta ve bazı modellerde None olur — bu yüzden
    # zorunlu değil; iş mantığı buna bel bağlamamalı.
    confidence: float | None = None


class HTREngine(ABC):
    """Bir sınav kağıdı görselini dijital metne çeviren motor."""

    @abstractmethod
    def read(self, image_bytes: bytes, prompt_hint: str | None = None) -> HTRResult:
        """Görseldeki el yazısını metne çevirir.

        `prompt_hint`: sorunun beklenen cevabı gibi bağlam. Görsel dil modelleri
        bağlamla belirgin biçimde daha isabetli okur (örn. kod mu, formül mü, düz
        metin mi olduğunu bilirse).
        """

    def warmup(self) -> None:  # noqa: B027 — bilerek soyut değil: mock motorun ısınmaya ihtiyacı yok
        """Modeli belleğe yükler. İlk kağıdın gecikmesini önlemek için opsiyonel."""
