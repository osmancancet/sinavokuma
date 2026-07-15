"""Puanlayıcının KARARLILIĞINI ölçer.

    GRADING_ENGINE=qwen_text_mlx uv run python -m scripts.bench_stability

Neden bu test her şeyden önemli:

Prompt'u üç kez iyileştirdim ve aynı KUSURSUZ cevaba sırasıyla 20, 12, 15 puan
aldım. "Prompt'u geliştiriyorum" sanırken aslında GÜRÜLTÜNÜN peşinde koşuyor
olabilirim.

Model aynı girdiye aynı promptla farklı puanlar veriyorsa, öğrencinin notu
kağıdının kalitesine değil ŞANSA bağlı demektir. Bu, sistemin en temel vaadini
— "adil ve tutarlı değerlendirme" — çürütür. SRS §2 tam olarak bunu iddia ediyor:
"Yapay zeka yorgunluk, dikkat dağınıklığı veya önyargı barındırmadığı için tüm
öğrencilere standart ve adil bir değerlendirme sunulur."

Bu iddia ancak model KARARLIYSA doğrudur. Ölçmeden söylenemez.
"""

import statistics
import sys
import time

from app.grading import chain
from app.llm.factory import get_llm
from scripts.eval_set import CASES, EXPECTED_ANSWER, MAX_SCORE, RUBRIC

RUNS = 5
# Ölçüm süresini makul tutmak için üç temsili vaka: iyi / yanlış / boş.
TEST_KEYS = ["perfect", "wrong_logic", "empty"]


def main() -> None:
    llm = get_llm()
    print(f"Motor: {type(llm).__name__} | Model: {getattr(llm, 'model_path', '-')}")
    print(f"Her vaka {RUNS} kez, AYNI prompt ile çalıştırılıyor.\n")
    llm.warmup()

    cases = [c for c in CASES if c.key in TEST_KEYS]
    unstable = False

    for case in cases:
        prompt = chain.build_prompt(
            question_number=1,
            max_score=MAX_SCORE,
            expected_answer=EXPECTED_ANSWER,
            rubric_criteria=RUBRIC,
            student_text=case.answer,
        )

        scores: list[float] = []
        failures = 0
        start = time.perf_counter()

        for _ in range(RUNS):
            raw = llm.generate(prompt)
            try:
                result = chain.clamp_to_rubric(chain.parse_result(raw, RUBRIC), MAX_SCORE)
                scores.append(result.toplam_puan)
            except chain.GradingParseError:
                failures += 1

        elapsed = time.perf_counter() - start

        print("─" * 72)
        print(f"{case.label}")
        print(f"  beklenen aralık : {case.lo}–{case.hi}")
        print(f"  {RUNS} çalıştırma : {[f'{s:g}' for s in scores]}"
              + (f"  (+{failures} okunamadı)" if failures else ""))

        if len(scores) >= 2:
            spread = max(scores) - min(scores)
            stdev = statistics.stdev(scores)
            print(f"  ortalama        : {statistics.mean(scores):.1f}")
            print(f"  YAYILIM         : {spread:g} puan  (std sapma {stdev:.1f})")
            print(f"  süre            : {elapsed / RUNS:.0f} sn/çalıştırma")

            # 20 puanlık bir soruda 3 puandan fazla yayılım, harf notunu değiştirebilir.
            if spread > MAX_SCORE * 0.15:
                unstable = True
                print(
                    f"  ⚠ KARARSIZ — aynı cevap {spread:g} puan aralığında dalgalanıyor. "
                    "Öğrencinin notu şansa bağlı."
                )
            else:
                print("  ✓ kararlı")
        else:
            unstable = True
            print("  ⚠ yeterli geçerli çıktı yok")

    print("\n" + "=" * 72)
    if unstable:
        print("SONUÇ: Model KARARSIZ.")
        print()
        print("Prompt ayarlamak bu sorunu çözmez — gürültünün peşinde koşmak olur.")
        print("Seçenekler:")
        print("  1. Daha büyük model (14B) — akıl yürütme kararlılığı modelle artar.")
        print("  2. Self-consistency: aynı soruyu 3 kez puanla, MEDYANI al.")
        print("     Maliyet 3 katına çıkar ama rastgele sapmaları söndürür.")
        print("  3. Kabullen ve insan onayına güven — ama o zaman 'tutarlı")
        print("     değerlendirme' iddiasını üründen çıkarmak gerekir.")
        sys.exit(1)

    print("SONUÇ: Model kararlı. Aynı cevap aynı puanı alıyor.")


if __name__ == "__main__":
    main()
