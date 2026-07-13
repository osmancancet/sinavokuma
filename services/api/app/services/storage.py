"""SRS §1.3 / GÖREV 3 — MinIO (S3 uyumlu) nesne depolama.

Neden presigned URL: mobil uygulama yüzlerce kağıt fotoğrafını yükleyecek. Bu
dosyalar API sunucusundan geçerse API bant genişliği ve bellek darboğazı olur.
Presigned URL ile istemci dosyayı DOĞRUDAN MinIO'ya yükler; API sadece imzalı
bir izin biletini üretir.
"""

from datetime import timedelta

from minio import Minio
from minio.error import S3Error

from app.core.config import settings

_client = Minio(
    settings.minio_endpoint,
    access_key=settings.minio_access_key,
    secret_key=settings.minio_secret_key,
    secure=settings.minio_secure,
)


def ensure_bucket() -> None:
    if not _client.bucket_exists(settings.minio_bucket):
        _client.make_bucket(settings.minio_bucket)


def build_object_key(exam_id: int, student_no: str, extension: str) -> str:
    """Nesne anahtarını sunucu üretir — istemciye bırakılmaz.

    İstemci anahtarı seçebilseydi `../` ile başka sınavların kağıtlarının üstüne
    yazabilirdi. Öğrenci numarasındaki tehlikeli karakterleri de burada eliyoruz.
    """
    safe_student_no = "".join(c for c in student_no if c.isalnum() or c in "-_")
    if not safe_student_no:
        raise ValueError("Geçersiz öğrenci numarası.")

    safe_ext = extension.lower().lstrip(".")
    if safe_ext not in {"jpg", "jpeg", "png", "webp", "heic"}:
        raise ValueError(f"Desteklenmeyen dosya uzantısı: {extension}")

    return f"exams/{exam_id}/papers/{safe_student_no}.{safe_ext}"


def presigned_put_url(object_key: str) -> str:
    """İstemcinin dosyayı doğrudan MinIO'ya PUT etmesi için imzalı URL."""
    return _client.presigned_put_object(
        settings.minio_bucket,
        object_key,
        expires=timedelta(seconds=settings.presigned_url_ttl_seconds),
    )


def object_exists(object_key: str) -> bool:
    """Nesne depoda gerçekten var mı? /confirm bunu doğrulamadan kuyruğa mesaj basmaz."""
    try:
        _client.stat_object(settings.minio_bucket, object_key)
    except S3Error as exc:
        if exc.code in ("NoSuchKey", "NoSuchObject"):
            return False
        raise
    return True


def presigned_get_url(object_key: str) -> str:
    """Web panelinin kağıt görselini göstermesi için imzalı okuma URL'i.

    Bucket public DEĞİL — görseller yalnızca süreli imzalı URL ile okunur (KVKK).
    """
    return _client.presigned_get_object(
        settings.minio_bucket,
        object_key,
        expires=timedelta(seconds=settings.presigned_url_ttl_seconds),
    )
