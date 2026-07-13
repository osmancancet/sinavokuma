"""SRS GÖREV 4 — RabbitMQ yayıncısı.

SRS §1.3: "Yüzlerce fotoğraf aynı anda yüklendiğinde AI sunucusunun çökmemesi için
istekler sıraya dizilir." Kuyruğun asıl işi bu — GPU'yu bir anda gelen 300 istekle
boğmamak.

Dayanıklılık ayarları bilinçli:
  - durable=True   : RabbitMQ yeniden başlarsa kuyruk kaybolmaz
  - PERSISTENT     : mesajlar diske yazılır, broker çökse de kaybolmaz
Bir sınav kağıdının işleme isteği kaybolursa o öğrencinin notu hiç oluşmaz ve
kimse fark etmez. Bu yüzden "en az bir kez" teslimat şart.
"""

import json
import logging

import aio_pika
from aio_pika.abc import AbstractRobustConnection

from app.core.config import settings

logger = logging.getLogger(__name__)

_connection: AbstractRobustConnection | None = None
_channel: aio_pika.abc.AbstractChannel | None = None


async def connect() -> None:
    """Uygulama açılışında çağrılır. connect_robust otomatik yeniden bağlanır."""
    global _connection, _channel
    _connection = await aio_pika.connect_robust(settings.rabbitmq_url)
    _channel = await _connection.channel()
    await _channel.declare_queue(settings.paper_queue, durable=True)
    logger.info("RabbitMQ bağlantısı kuruldu, kuyruk: %s", settings.paper_queue)


async def disconnect() -> None:
    if _connection is not None and not _connection.is_closed:
        await _connection.close()


async def publish_paper_for_processing(paper_id: int, exam_id: int, object_key: str) -> None:
    """Bir sınav kağıdını AI işleme kuyruğuna gönderir."""
    if _channel is None:
        raise RuntimeError("RabbitMQ bağlantısı yok — connect() çağrılmamış.")

    message = aio_pika.Message(
        body=json.dumps(
            {"paper_id": paper_id, "exam_id": exam_id, "object_key": object_key}
        ).encode(),
        content_type="application/json",
        delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
    )
    await _channel.default_exchange.publish(message, routing_key=settings.paper_queue)
    logger.info("Kağıt kuyruğa gönderildi: paper_id=%s", paper_id)
