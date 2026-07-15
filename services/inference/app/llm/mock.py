"""Mock puanlayıcı — model indirmeden boru hattını uçtan uca çalıştırmak için.

Prompt'tan rubriği ve öğrenci cevabını geri okuyup basit anahtar-kelime eşleşmesiyle
puan üretir. Gerçekçi puanlama değil; amacı kuyruk → okuma → puanlama → DB zincirinin
çalıştığını kanıtlamak.
"""

import re

from app.llm.base import LLMEngine

# Prompt'taki "- <kriter>: <puan> puan" satırlarını yakalar.
RUBRIC_LINE = re.compile(r"^- (?P<kriter>.+?): (?P<puan>[\d.]+) puan$", re.MULTILINE)


class MockLLM(LLMEngine):
    def generate(self, prompt: str) -> str:
        criteria = [
            (m.group("kriter"), float(m.group("puan"))) for m in RUBRIC_LINE.finditer(prompt)
        ]

        section = prompt.split("## ÖĞRENCİNİN CEVABI", 1)
        student = section[1] if len(section) > 1 else ""
        student = student.split("## DEĞERLENDİRME KURALLARI", 1)[0].strip()
        lowered = student.lower()

        bos = (not student) or "cevaplayamad" in lowered
        iyi = ("for" in lowered or "while" in lowered) and "toplam" in lowered

        lines = [
            "ANALIZ: [MOCK PUANLAYICI] Bu sahte bir değerlendirmedir — gerçek model "
            "kullanılmıyor. Cevap anahtar kelimelere göre incelendi."
        ]
        for name, max_score in criteria:
            if bos:
                puan, gerekce = 0.0, "Öğrenci soruyu cevaplamamış. [MOCK]"
            elif iyi:
                puan, gerekce = max_score, "Kriter tam olarak karşılanmış. [MOCK]"
            else:
                puan, gerekce = max_score / 2, "Kriter kısmen karşılanmış. [MOCK]"
            lines.append(f"KRITER: {name} | PUAN: {puan} | GEREKCE: {gerekce}")

        lines.append(
            "SONUC: Öğrenci soruyu cevaplamamış. [MOCK]"
            if bos
            else "SONUC: Kriterler anahtar kelimelere göre değerlendirildi. [MOCK]"
        )
        return "\n".join(lines)
