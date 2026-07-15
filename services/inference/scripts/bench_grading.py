"""Puanlayıcıyı değerlendirme setine karşı ölçer (SRS §4 — MLOps / ground truth).

    GRADING_ENGINE=qwen_text_mlx uv run python -m scripts.bench_grading

Asıl soru "model puan veriyor mu?" değil — verir, her zaman verir.
Asıl soru: **kötü cevabı kötü, iyi cevabı iyi puanlıyor mu?**

Bunu ölçmezsek, herkese 18/20 veren bir sistemi "çalışıyor" sanırız. Bir
akademisyen bunu ilk 10 kağıtta fark eder ve sistemi bir daha açmaz.

Üç metrik:
  KAPSAMA  — kaç vakada geçerli çıktı üretebildi? (parse hatası = sistem hatası)
  İSABET   — puan beklenen aralıkta mı?
  AYRIM    — kusursuz cevap ile boş cevap arasındaki puan farkı
"""

import time

from app.grading import chain
from app.llm.factory import get_llm
from scripts.eval_set import CASES, EXPECTED_ANSWER, MAX_SCORE, RUBRIC


def main() -> None:
    llm = get_llm()
    print(f"Puanlama motoru: {type(llm).__name__}")
    print(f"Model: {getattr(llm, 'model_path', '-')}")
    print("Model ısınıyor...\n")
    llm.warmup()

    rows = []
    for case in CASES:
        prompt = chain.build_prompt(
            question_number=1,
            max_score=MAX_SCORE,
            expected_answer=EXPECTED_ANSWER,
            rubric_criteria=RUBRIC,
            student_text=case.answer,
        )
        start = time.perf_counter()
        raw = llm.generate(prompt)
        elapsed = time.perf_counter() - start

        try:
            result = chain.clamp_to_rubric(chain.parse_result(raw, RUBRIC), MAX_SCORE)
        except chain.GradingParseError as exc:
            print(f"✗ {case.label}: ÇIKTI OKUNAMADI — {exc}")
            print(f"   ham çıktı: {raw[:200]}...\n")
            rows.append((case, None, elapsed))
            continue

        score = result.toplam_puan
        ok = case.lo <= score <= case.hi
        mark = "✓" if ok else "✗"

        print("─" * 76)
        print(f"{mark} {case.label}")
        print(f"   puan: {score} / {MAX_SCORE}   (beklenen: {case.lo}–{case.hi})   {elapsed:.0f} sn")
        if not ok:
            print(f"   ⚠ {case.why}")
        for c in result.kriterler:
            print(f"     • {c.kriter}: {c.verilen_puan}/{c.max_puan} — {c.gerekce[:90]}")
        rows.append((case, score, elapsed))

    # ── Özet ────────────────────────────────────────────────────────────
    print("\n" + "=" * 76)
    print("SONUÇ")
    print("=" * 76)

    for case, score, _ in rows:
        if score is None:
            bar, verdict = "", "OKUNAMADI"
        else:
            bar = "█" * int(score / MAX_SCORE * 24)
            verdict = "ok" if case.lo <= score <= case.hi else f"BEKLENEN {case.lo}-{case.hi}"
        shown = "—" if score is None else f"{score:>4.1f}"
        print(f"  {case.label[:44]:<46} {shown}  {bar:<24} {verdict}")

    scored = [(c, s) for c, s, _ in rows if s is not None]
    parsed_pct = len(scored) / len(rows) * 100
    in_range = sum(1 for c, s in scored if c.lo <= s <= c.hi)
    accuracy_pct = in_range / len(rows) * 100

    by_key = {c.key: s for c, s in scored}
    discrimination = None
    if "perfect" in by_key and "empty" in by_key:
        discrimination = by_key["perfect"] - by_key["empty"]

    avg_time = sum(t for _, _, t in rows) / len(rows)

    print()
    print(f"  KAPSAMA : {len(scored)}/{len(rows)} vakada geçerli çıktı  (%{parsed_pct:.0f})")
    print(f"  İSABET  : {in_range}/{len(rows)} vaka beklenen aralıkta   (%{accuracy_pct:.0f})")
    if discrimination is not None:
        print(f"  AYRIM   : kusursuz - boş = {discrimination:.1f} / {MAX_SCORE} puan")
    print(f"  HIZ     : ortalama {avg_time:.0f} sn / soru")

    print()
    if parsed_pct < 100:
        print("  ⚠ Bazı kağıtlarda model çıktısı okunamıyor. Bunlar FAILED olarak")
        print("    işaretlenip insana gider — ama oran yüksekse sistem işe yaramaz.")
    if accuracy_pct >= 70 and parsed_pct == 100 and (discrimination or 0) >= MAX_SCORE * 0.6:
        print("  ✓ Puanlayıcı üretim için yeterli seviyede ayrım yapıyor.")
    else:
        print("  ✗ Puanlayıcı henüz üretime hazır DEĞİL.")


if __name__ == "__main__":
    main()
