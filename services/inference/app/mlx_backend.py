"""Tek bir Qwen2.5-VL örneğini süreç boyunca bellekte tutar.

Hem HTR (görselden okuma) hem puanlama (metinden değerlendirme) bu örneği kullanır.
16 GB'lık bir makinede iki ayrı model yüklemek belleği tüketirdi; Qwen2.5-VL zaten
bir instruct modeli, metin görevini de yapar.

Ayrı bir puanlama modeli istenirse `LLMEngine` arayüzüne yeni bir uygulama eklenir —
çağıran kod değişmez.
"""

import io
import logging
import tempfile
import threading
from pathlib import Path

from PIL import Image

logger = logging.getLogger(__name__)

_lock = threading.Lock()
_loaded: dict[str, tuple] = {}


def _load(model_path: str) -> tuple:
    with _lock:
        if model_path in _loaded:
            return _loaded[model_path]

        # İçeride import: mlx-vlm yalnızca Apple Silicon'da kurulu olur. Modül
        # tepesinde import edersek mock motoruyla çalışan Linux/CI ortamı çöker.
        from mlx_vlm import load
        from mlx_vlm.utils import load_config

        logger.info("Qwen2.5-VL yükleniyor (ilk seferde indirilir): %s", model_path)
        model, processor = load(model_path)
        config = load_config(model_path)
        _loaded[model_path] = (model, processor, config)
        logger.info("Model belleğe alındı.")
        return _loaded[model_path]


def generate(
    model_path: str,
    prompt: str,
    image_bytes: bytes | None = None,
    max_tokens: int = 1024,
) -> str:
    """Görselli veya görselsiz üretim. Görsel yoksa saf metin görevi çalışır."""
    model, processor, config = _load(model_path)

    from mlx_vlm import generate as mlx_generate
    from mlx_vlm.prompt_utils import apply_chat_template

    num_images = 1 if image_bytes else 0
    formatted = apply_chat_template(processor, config, prompt, num_images=num_images)

    if image_bytes is None:
        result = mlx_generate(model, processor, formatted, [], max_tokens=max_tokens, verbose=False)
    else:
        # mlx-vlm dosya yolu bekliyor; baytları geçici dosyaya yazıyoruz.
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        with tempfile.TemporaryDirectory() as tmpdir:
            image_path = Path(tmpdir) / "kagit.png"
            image.save(image_path)
            result = mlx_generate(
                model,
                processor,
                formatted,
                [str(image_path)],
                max_tokens=max_tokens,
                verbose=False,
            )

    # mlx-vlm sürümüne göre str veya GenerationResult dönebiliyor.
    text = result if isinstance(result, str) else getattr(result, "text", str(result))
    return text.strip()


def warmup(model_path: str) -> None:
    _load(model_path)
