# Yapay Zeka Destekli Sınav Otomasyonu Platformu

Akademisyenlerin el yazısı sınav kağıtlarını okuma yükünü ortadan kaldıran EdTech SaaS
platformu. Kağıdı fotoğraftan okur (HTR), rubriğe göre puanlar, gerekçesini yazar; son
sözü akademisyene bırakır (Human-in-the-Loop). Her soruyu MÜDEK çıktısına bağlayarak
akreditasyon kanıt dosyası üretir.

Tasarım dokümanları: [docs/](docs/)

## Durum

| Faz | Kapsam | Durum |
|---|---|---|
| FAZ 1 | Veritabanı şeması, JWT+RBAC, MinIO presigned URL | ✅ Tamam |
| FAZ 2 | RabbitMQ kuyruğu, Qwen2.5-VL okuma, rubrik puanlama | ⏳ Sırada |
| FAZ 3 | Web dashboard, değerlendirme ekranı, MÜDEK raporu | ⏳ |
| FAZ 4 | Mobil tarayıcı, çevrimdışı senkronizasyon | ⏳ |

## Kurulum

```bash
cp .env.example .env          # üretimde JWT_SECRET_KEY'i mutlaka değiştirin
docker compose up -d          # PostgreSQL + RabbitMQ + MinIO

cd services/api
uv sync
uv run alembic upgrade head
uv run python -m scripts.seed # geliştirme kullanıcıları + örnek ders
uv run uvicorn app.main:app --reload
```

Swagger arayüzü: http://localhost:8000/docs

### Geliştirme hesapları (seed)

| E-posta | Parola | Rol |
|---|---|---|
| admin@uni.edu.tr | admin1234 | ADMIN |
| hoca@uni.edu.tr | hoca1234 | TEACHER |
| denetci@uni.edu.tr | denetci1234 | AUDITOR |

### Yönetim panelleri

- MinIO: http://localhost:9001 (sinavokuma / sinavokuma123)
- RabbitMQ: http://localhost:15672 (sinavokuma / sinavokuma)

## Mimari notu

Inference servisi Apple Silicon'da MLX (Metal) ile çalışır; Metal macOS'ta Linux
konteynerlerine geçmediği için API ve inference servisleri geliştirmede **Docker
dışında**, yerel çalışır. Docker yalnızca altyapıyı (PostgreSQL/RabbitMQ/MinIO) taşır.
Üretim dağıtımı için CUDA tabanlı ayrı bir inference imajı yazılacak.
