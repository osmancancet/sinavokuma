"""Mock puanlayıcı — model indirmeden boru hattını uçtan uca çalıştırmak için.

Prompt'tan rubriği ve öğrenci cevabını geri okuyup basit bir anahtar-kelime eşleşmesiyle
puan üretir. Amacı gerçekçi puanlama değil; kuyruk → okuma → puanlama → DB zincirinin
çalıştığını kanıtlamak.
"""

import json
import re

from app.llm.base import LLMEngine

# Prompt'taki "- <kriter>: <puan> puan" satırlarını yakalar.
RUBRIC_LINE = re.compile(r"^- (?P<kriter>.+?): (?P<puan>[\d.]+) puan$", re.MULTILINE)


class MockLLM(LLMEngine):
    def generate(self, prompt: str) -> str:
        criteria = [
            {"kriter": m.group("kriter"), "puan": float(m.group("puan"))}
            for m in RUBRIC_LINE.finditer(prompt)
        ]

        student_section = prompt.split("## ÖĞRENCİNİN CEVABI", 1)
        student_text = student_section[1] if len(student_section) > 1 else ""
        student_text = student_text.split("## NASIL DEĞERLENDİRECEKSİN", 1)[0].strip()

        cevaplayamadi = "cevaplayamad" in student_text.lower() or not student_text
        # Gerçekçi bir dağılım için: boş/teslim edilmemiş cevaba 0, doğru görünen
        # cevaba tam, "toplam" geçmiyorsa kısmi puan.
        has_loop = any(k in student_text.lower() for k in ("for", "while", "döngü"))
        has_sum = "toplam" in student_text.lower() or "sum" in student_text.lower()

        scored = []
        for c in criteria:
            if cevaplayamadi:
                verilen, gerekce = 0.0, "Öğrenci soruyu cevaplamamış."
            elif has_loop and has_sum:
                verilen, gerekce = c["puan"], "Kriter tam olarak karşılanmış. [MOCK]"
            else:
                verilen, gerekce = c["puan"] / 2, "Kriter kısmen karşılanmış. [MOCK]"
            scored.append(
                {
                    "kriter": c["kriter"],
                    "max_puan": c["puan"],
                    "verilen_puan": verilen,
                    "gerekce": gerekce,
                }
            )

        total = sum(c["verilen_puan"] for c in scored)
        return json.dumps(
            {
                "analiz": (
                    "[MOCK PUANLAYICI] Bu bir sahte değerlendirmedir — gerçek model "
                    "kullanılmıyor. Öğrenci cevabı anahtar kelimelere göre incelendi."
                ),
                "kriterler": scored,
                "toplam_puan": total,
                "genel_gerekce": (
                    "Öğrenci soruyu cevaplamamış. [MOCK]"
                    if cevaplayamadi
                    else f"Kriterlerin toplamından {total} puan hesaplandı. [MOCK]"
                ),
            },
            ensure_ascii=False,
        )
