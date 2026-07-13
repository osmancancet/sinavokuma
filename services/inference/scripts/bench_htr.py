"""HTR motorunu tek bir kağıt üzerinde ölçer.

    HTR_ENGINE=qwen_mlx uv run python -m scripts.bench_htr

Ground truth ile karşılaştırıp karakter hata oranını (CER) verir. SRS §2'nin
"%95 üzeri doğruluk" iddiası ancak böyle bir ölçümle savunulabilir.
"""

import sys
import time
from pathlib import Path

from app.htr.factory import get_engine
from scripts.make_test_paper import GROUND_TRUTH


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

    engine = get_engine()
    print(f"Motor: {type(engine).__name__}")
    print("Model yükleniyor / okunuyor...\n")

    start = time.perf_counter()
    result = engine.read(image_path.read_bytes())
    elapsed = time.perf_counter() - start

    truth = normalize(GROUND_TRUTH)
    read = normalize(result.text)
    distance = levenshtein(truth, read)
    cer = distance / max(len(truth), 1)

    print("=" * 70)
    print("KAĞITTA YAZAN (ground truth):")
    print(GROUND_TRUTH)
    print("=" * 70)
    print("MODELİN OKUDUĞU:")
    print(result.text)
    print("=" * 70)
    print(f"Süre               : {elapsed:.1f} sn")
    print(f"Karakter hatası    : {distance} / {len(truth)}")
    print(f"CER (hata oranı)   : {cer:.1%}")
    print(f"Doğruluk           : {1 - cer:.1%}")


if __name__ == "__main__":
    main()
