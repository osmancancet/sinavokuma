"""Qwen2.5-VL — Apple Silicon (MLX / Metal).

KVKK: model kendi donanımımızda çalışır; öğrenci kağıdı hiçbir dış servise gitmez.
"""

from app import mlx_backend
from app.htr.base import HTREngine, HTRResult

# Görsel dil modelleri bağlamla belirgin biçimde daha isabetli okur. Modele ne
# YAPACAĞINI değil, ne GÖRDÜĞÜNÜ söylüyoruz.
HTR_PROMPT = """Bu bir öğrencinin el yazısıyla doldurduğu sınav kağıdıdır.

Görevin SADECE yazılanları dijital metne çevirmektir. Kurallar:
- Yazılanı olduğu gibi aktar. Hataları DÜZELTME.
- Öğrencinin yazım/sözdizimi hataları varsa onları da aynen yaz — bu hatalar
  notlandırmada kullanılacak. Düzeltirsen öğrenciye hak etmediği puan verilir.
- Yorum ekleme, açıklama yapma, cevabı değerlendirme.
- Okunamayan yerler için [okunamadı] yaz.
- Sadece çevirdiğin metni döndür, başka hiçbir şey yazma."""


class QwenMLXEngine(HTREngine):
    def __init__(self, model_path: str, max_tokens: int = 1024) -> None:
        self.model_path = model_path
        self.max_tokens = max_tokens

    def warmup(self) -> None:
        mlx_backend.warmup(self.model_path)

    def read(self, image_bytes: bytes, prompt_hint: str | None = None) -> HTRResult:
        prompt = HTR_PROMPT
        if prompt_hint:
            prompt += (
                "\n\nBağlam — sorunun beklenen cevabı. Bu SADECE ne tür bir içerik "
                "(kod, formül, düz metin) okuyacağını anlaman içindir. Öğrencinin "
                "yazdığını buna BENZETME, gördüğünü yaz:\n" + prompt_hint
            )

        text = mlx_backend.generate(
            self.model_path, prompt, image_bytes=image_bytes, max_tokens=self.max_tokens
        )
        return HTRResult(text=text, confidence=None)
