"""HTR motorunu ölçer: doğruluk (CER) + soğuk/sıcak hız.

    HTR_ENGINE=qwen_mlx uv run python -m scripts.bench_htr

Neden iki geçiş: ilk çağrı modeli diskten belleğe yükler. O süreyi "kağıt başına
süre" diye raporlamak yanıltıcı olur — worker modeli bir kez yükleyip yüzlerce
kağıt işler. Asıl önemli olan SICAK süredir.

SRS §2'nin "%95 üzeri doğruluk" iddiası ancak böyle bir ölçümle savunulabilir.
"""

import sys
import time
from pathlib import Path

from app.htr.factory import get_engine
from scripts.make_test_paper import GROUND_TRUTH_FULL


def levenshtein(a: str, b: str) -> int:
    if len(a) < len(b):
        a, b = b, a
    previous = list(range(len(b) + 1))
    for i, ca in enumerate(a):
        current = [i + 1]
        for j, cb in enumerate(b):
            current.append(min(previous[j + 1] + 1, current[j] + 1, previous[j] + (ca != cb)))
        previous = current
    return previous[-1]


def normalize(s: str) -> str:
    """Boşluk farklarını yok say — asıl mesele karakterlerin doğru okunması."""
    return " ".join(s.split())


def main() -> None:
    image_path = Path(__file__).parent / "test_kagit.png"
    if not image_path.exists():
        sys.exit("Önce `uv run python -m scripts.make_test_paper` çalıştırın.")

    image_bytes = image_path.read_bytes()
    engine = get_engine()
    print(f"Motor: {type(engine).__name__}\n")

    print("1. geçiş (SOĞUK — model diskten yükleniyor)...")
    t0 = time.perf_counter()
    first = engine.read(image_bytes)
    cold = time.perf_counter() - t0

    print("2. geçiş (SICAK — model zaten bellekte)...")
    t0 = time.perf_counter()
    second = engine.read(image_bytes)
    warm = time.perf_counter() - t0

    truth = normalize(GROUND_TRUTH_FULL)
    read = normalize(second.text)
    distance = levenshtein(truth, read)
    cer = distance / max(len(truth), 1)

    print("\n" + "=" * 72)
    print("KAĞITTA YAZAN (ground truth):")
    print(GROUND_TRUTH_FULL)
    print("=" * 72)
    print("MODELİN OKUDUĞU (temizlenmiş):")
    print(second.text)
    print("=" * 72)
    print(f"Karakter hatası  : {distance} / {len(truth)}")
    print(f"CER (hata oranı) : {cer:.1%}")
    print(f"DOĞRULUK         : {max(0, 1 - cer):.1%}")
    print("-" * 72)
    print(f"Soğuk geçiş      : {cold:.1f} sn  (model yükleme dahil — bir kereye mahsus)")
    print(f"SICAK geçiş      : {warm:.1f} sn  <- kağıt başına gerçek maliyet")
    print(f"312 kağıt tahmini: {warm * 312 / 60:.0f} dakika")
    if first.text != second.text:
        print("\nUYARI: iki geçiş farklı sonuç verdi — model deterministik değil.")


if __name__ == "__main__":
    main()
