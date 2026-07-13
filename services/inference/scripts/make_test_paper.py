"""Test için sentetik "el yazısı" sınav kağıdı üretir.

Gerçek taranmış kağıt elimizde olmadığı için, HTR motorunu ölçebilmek adına
el yazısı fontuyla render edip gerçek tarama koşullarını taklit ediyoruz:
hafif eğim, kağıt dokusu/gürültü, düzensiz satır aralıkları.

Bu GERÇEK el yazısının yerini TUTMAZ. Modelin gerçek doğruluğu ancak gerçek
taranmış kağıtlarla ölçülebilir — bu sadece boru hattını ve modelin genel
okuma yeteneğini sınamak için.

    uv run python -m scripts.make_test_paper
"""

import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HANDWRITING_FONT = "/System/Library/Fonts/Supplemental/Bradley Hand Bold.ttf"

# Öğrencinin kağıda yazdığı varsayılan cevap. HTR'ın bunu ne kadar doğru
# okuduğunu ölçmek için "ground truth" olarak saklıyoruz.
GROUND_TRUTH = """Soru 1:

int toplam = 0;
for (int i = 1; i <= n; i++) {
    toplam = toplam + i;
}
printf("%d", toplam);"""


def make_paper(out_path: Path, seed: int = 42) -> None:
    rng = random.Random(seed)
    W, H = 900, 700

    # Hafif sarımsı kağıt rengi (beyaz değil — gerçek tarama beyaz çıkmaz)
    img = Image.new("RGB", (W, H), (250, 248, 240))
    draw = ImageDraw.Draw(img)

    # Çizgili defter satırları
    for y in range(90, H, 45):
        draw.line([(60, y), (W - 60, y)], fill=(200, 215, 230), width=1)

    header_font = ImageFont.truetype(HANDWRITING_FONT, 26)
    body_font = ImageFont.truetype(HANDWRITING_FONT, 30)

    draw.text((60, 30), "Ogrenci No: 20210777", font=header_font, fill=(40, 40, 90))

    y = 100
    for line in GROUND_TRUTH.split("\n"):
        # Her satırı biraz kaydır ve döndür — insan eli düz yazmaz
        x_jitter = rng.randint(-4, 4)
        y_jitter = rng.randint(-3, 3)
        draw.text((70 + x_jitter, y + y_jitter), line, font=body_font, fill=(20, 30, 90))
        y += 45

    # Tarama gürültüsü
    pixels = img.load()
    for _ in range(4000):
        px, py = rng.randint(0, W - 1), rng.randint(0, H - 1)
        r, g, b = pixels[px, py]
        n = rng.randint(-18, 18)
        pixels[px, py] = (max(0, min(255, r + n)), max(0, min(255, g + n)), max(0, min(255, b + n)))

    # Tarayıcıya eğri konmuş kağıt
    img = img.rotate(-1.2, resample=Image.BICUBIC, fillcolor=(250, 248, 240), expand=False)

    img.save(out_path)
    print(f"Test kağıdı üretildi: {out_path}")
    print(f"\nGROUND TRUTH (kağıtta yazan):\n{GROUND_TRUTH}")


if __name__ == "__main__":
    out = Path(__file__).parent / "test_kagit.png"
    make_paper(out)
