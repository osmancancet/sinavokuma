"""SRS GÖREV 5 — "Qwen-VL modelini taklit eden (mock) bir fonksiyon".

Amacı: model indirmeden kuyruk → indirme → okuma → puanlama → DB zincirinin
tamamını çalıştırabilmek. Boru hattındaki bir hata ile modelin isabetsizliğini
birbirine karıştırmamak için.
"""

import hashlib

from app.htr.base import HTREngine, HTRResult

# Görselin hash'ine göre deterministik olarak seçilir — aynı kağıt hep aynı metni
# üretir, testler tekrarlanabilir olur.
SAMPLE_ANSWERS = [
    (
        "int toplam = 0;\n"
        "for (int i = 1; i <= n; i++) {\n"
        "    toplam = toplam + i;\n"
        "}\n"
        "printf(\"%d\", toplam);"
    ),
    (
        "int toplam = 0\n"
        "for i = 1 to n\n"
        "    toplam += i\n"
        "yazdir(toplam)"
    ),
    (
        "toplam = n * (n + 1) / 2\n"
        "printf(toplam)"
    ),
    "Bu soruyu cevaplayamadım.",
]


class MockHTR(HTREngine):
    def read(self, image_bytes: bytes, prompt_hint: str | None = None) -> HTRResult:
        digest = hashlib.sha256(image_bytes).digest()
        index = digest[0] % len(SAMPLE_ANSWERS)
        return HTRResult(text=SAMPLE_ANSWERS[index], confidence=None)
