"""Qwen2.5-VL — Apple Silicon (MLX / Metal).

KVKK: model kendi donanımımızda çalışır; öğrenci kağıdı hiçbir dış servise gitmez.

ÖNEMLİ — ölçümden çıkan iki bulgu bu dosyanın tasarımını belirledi:

1) Model, "yorum ekleme" talimatına UYMUYOR. Okuduğu metnin sonuna kendi
   açıklamasını ekliyor ("Bu kodun amacı ... bulmaktır."). Bu açıklama
   öğrencinin cevabıymış gibi puanlayıcıya giderse, öğrenci yazmadığı bir
   açıklamadan puan alır. Bu bir puanlama bütünlüğü hatasıdır.

   Çözüm: talimata güvenmiyoruz. Modelden çıktıyı <metin>...</metin> etiketleri
   arasına almasını istiyoruz ve YALNIZCA etiket içini alıyoruz. Etiketin dışında
   ne yazarsa yazsın atılır.

2) Büyük görseller çok yavaş. Görsel token sayısı çözünürlükle karesel büyüyor.
   Kağıdı okunabilirliği bozmayacak bir üst sınıra küçültüyoruz.
"""

import io
import logging
import re

from PIL import Image

from app import mlx_backend
from app.htr.base import HTREngine, HTRResult

logger = logging.getLogger(__name__)

# El yazısı okunabilirliğini korurken görsel token sayısını makul tutan üst sınır.
MAX_EDGE_PX = 1280

HTR_PROMPT = """Bu bir öğrencinin el yazısıyla doldurduğu sınav kağıdıdır.

Görevin SADECE kağıtta yazanları dijital metne çevirmektir.

Kurallar:
- Yazılanı olduğu gibi aktar. Hataları DÜZELTME.
- Öğrencinin yazım/sözdizimi hataları varsa onları da aynen yaz. Bu hatalar
  notlandırmada kullanılacak; düzeltirsen öğrenciye hak etmediği puan verilir.
- Cevabı YORUMLAMA, açıklama, özetleme veya değerlendirme.
- Okunamayan yerler için [okunamadı] yaz.

Çevirdiğin metni <metin> ve </metin> etiketleri arasına yaz. Etiketlerin dışına
hiçbir şey yazma.

Örnek çıktı biçimi:
<metin>
(kağıtta ne yazıyorsa aynen burada)
</metin>"""

# Model etiketleri unutursa diye: kendi eklediği açıklama cümlelerini yakalar.
CHATTER_PATTERNS = [
    re.compile(r"^\s*Bu (kod|cevap|metin|soru)[^\n]*\.\s*$", re.MULTILINE),
    re.compile(r"^\s*(Görselde|Kağıtta|Öğrenci)[^\n]*şunlar[^\n]*:\s*$", re.MULTILINE),
]


def _downscale(image_bytes: bytes) -> bytes:
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    longest = max(image.size)
    if longest > MAX_EDGE_PX:
        ratio = MAX_EDGE_PX / longest
        new_size = (round(image.width * ratio), round(image.height * ratio))
        logger.info("Görsel küçültüldü: %s -> %s", image.size, new_size)
        image = image.resize(new_size, Image.LANCZOS)
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def extract_transcription(raw: str) -> str:
    """Modelin çıktısından yalnızca öğrencinin yazdığını ayıklar.

    Etiket varsa etiket içi alınır — modelin dışarıya yazdığı her şey atılır.
    Etiket yoksa (model unutmuşsa) bilinen "kendi yorumu" kalıpları temizlenir.
    """
    match = re.search(r"<metin>(.*?)</metin>", raw, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()

    logger.warning("Model <metin> etiketlerini kullanmadı; yedek temizlik uygulanıyor.")
    cleaned = raw
    for pattern in CHATTER_PATTERNS:
        cleaned = pattern.sub("", cleaned)
    return cleaned.strip()


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

        raw = mlx_backend.generate(
            self.model_path,
            prompt,
            image_bytes=_downscale(image_bytes),
            max_tokens=self.max_tokens,
        )
        return HTRResult(text=extract_transcription(raw), confidence=None)
