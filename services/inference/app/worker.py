"""SRS GÖREV 5 + 6 — Inference Worker.

RabbitMQ'yu dinler. Her mesaj bir sınav kağıdıdır:

  kuyruk -> MinIO'dan görseli indir -> HTR ile oku -> her soru için rubriğe göre
  puanla (CoT) -> paper_scores'a yaz -> kağıdı AI_SCORED yap

Hata yönetimi bilinçli:
  - Kalıcı hata (bozuk görsel, model çıktısı parse edilemiyor): kağıt FAILED
    işaretlenir ve mesaj ACK'lenir. Yeniden denemek aynı hatayı verecektir;
    NACK'lersek mesaj sonsuza kadar kuyrukta döner ve worker'ı kilitler.
  - Geçici hata (DB düştü, MinIO erişilemiyor): mesaj requeue edilir.

prefetch_count=1: worker aynı anda tek kağıt işler. SRS §1.3'ün "AI sunucusunun
çökmemesi" gereksinimi tam olarak bu — GPU'ya aynı anda 300 kağıt gitmez.
"""

import asyncio
import json
import logging

import aio_pika
from sinavokuma_shared import PaperScore, PaperStatus, Question, StudentPaper
from sinavokuma_shared.db import make_engine, make_session_factory
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app import storage
from app.config import settings
from app.grading import chain
from app.htr.factory import get_engine
from app.llm.factory import get_llm

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("worker")

engine = make_engine(settings.database_url)
SessionLocal = make_session_factory(engine)


class PermanentError(Exception):
    """Yeniden denemek çözmez — kağıt FAILED işaretlenmeli."""


async def process_paper(db: AsyncSession, paper_id: int, object_key: str) -> None:
    paper = await db.get(StudentPaper, paper_id)
    if paper is None:
        raise PermanentError(f"Kağıt bulunamadı: paper_id={paper_id}")

    if paper.status not in (PaperStatus.PENDING, PaperStatus.FAILED):
        logger.info("Kağıt zaten işlenmiş, atlanıyor: paper_id=%s (%s)", paper_id, paper.status)
        return

    questions = list(
        (
            await db.execute(
                select(Question)
                .where(Question.exam_id == paper.exam_id)
                .order_by(Question.question_number)
            )
        )
        .scalars()
        .all()
    )
    if not questions:
        raise PermanentError(f"Sınavda soru tanımlı değil: exam_id={paper.exam_id}")

    logger.info("Görsel indiriliyor: %s", object_key)
    image_bytes = storage.download(object_key)

    htr = get_engine()
    llm = get_llm()

    # Aynı kağıt yeniden işleniyorsa eski puanları temizle — yoksa unique
    # kısıtı (student_paper_id, question_id) patlar.
    existing = (
        (await db.execute(select(PaperScore).where(PaperScore.student_paper_id == paper.id)))
        .scalars()
        .all()
    )
    for old in existing:
        await db.delete(old)
    await db.flush()

    for question in questions:
        logger.info("Soru %s okunuyor...", question.question_number)
        # Görsel işleme CPU/GPU-yoğun ve senkron. Doğrudan çağırırsak event loop'u
        # bloklar ve RabbitMQ heartbeat'leri kaçar -> broker bağlantıyı koparır.
        htr_result = await asyncio.to_thread(
            htr.read, image_bytes, question.expected_answer
        )
        logger.info("Okunan metin (%s karakter)", len(htr_result.text))

        prompt = chain.build_prompt(
            question_number=question.question_number,
            max_score=float(question.max_score),
            expected_answer=question.expected_answer,
            rubric_criteria=question.rubric_criteria or [],
            student_text=htr_result.text,
        )

        logger.info("Soru %s puanlanıyor...", question.question_number)
        raw = await asyncio.to_thread(llm.generate, prompt)

        rubric = question.rubric_criteria or []
        try:
            result = chain.parse_result(raw, rubric)
        except chain.GradingParseError as exc:
            # Kritik: burada "0 puan" varsaymıyoruz. Model çıktısı okunamadıysa bu
            # ÖĞRENCİNİN hatası değil, SİSTEMİN hatasıdır. Kağıdı FAILED işaretleyip
            # insana gönderiyoruz. Sessizce sıfır vermek en kötü senaryo olurdu.
            logger.error("Puanlama çıktısı okunamadı. Ham çıktı:\n%s", raw[:800])
            raise PermanentError(
                f"Soru {question.question_number}: model çıktısı okunamadı ({exc}). "
                "Kağıt insan incelemesine gönderildi."
            ) from exc

        result = chain.clamp_to_rubric(result, float(question.max_score))

        # Gerekçe: düşünce zinciri + kriter kırılımı. Akademisyen web panelinde
        # bunu görüp notu onaylayacak ya da düzeltecek (SRS §3.2).
        reasoning_parts = [result.analiz, ""]
        for c in result.kriterler:
            reasoning_parts.append(f"• {c.kriter}: {c.verilen_puan}/{c.max_puan} — {c.gerekce}")
        reasoning_parts.extend(["", result.genel_gerekce])

        db.add(
            PaperScore(
                student_paper_id=paper.id,
                question_id=question.id,
                ai_raw_text=htr_result.text,
                ai_score=result.toplam_puan,
                ai_reasoning="\n".join(reasoning_parts),
                # final_score bilerek BOŞ. Notu insan onaylayana kadar kesinleşmez.
                final_score=None,
            )
        )
        logger.info(
            "Soru %s puanlandı: %s/%s",
            question.question_number,
            result.toplam_puan,
            question.max_score,
        )

    paper.status = PaperStatus.AI_SCORED
    paper.error_message = None
    await db.commit()
    logger.info("Kağıt tamamlandı: paper_id=%s -> AI_SCORED", paper_id)


async def mark_failed(paper_id: int, message: str) -> None:
    async with SessionLocal() as db:
        paper = await db.get(StudentPaper, paper_id)
        if paper is not None:
            paper.status = PaperStatus.FAILED
            paper.error_message = message[:2000]
            await db.commit()


async def handle_message(message: aio_pika.abc.AbstractIncomingMessage) -> None:
    payload = json.loads(message.body)
    paper_id = payload["paper_id"]
    object_key = payload["object_key"]
    logger.info("--- Mesaj alındı: paper_id=%s ---", paper_id)

    try:
        async with SessionLocal() as db:
            await process_paper(db, paper_id, object_key)
        await message.ack()

    except PermanentError as exc:
        # Yeniden denemek aynı sonucu verir. Kağıdı FAILED yap ve mesajı bitir —
        # aksi halde bu mesaj kuyrukta sonsuza kadar döner ve worker'ı tıkar.
        logger.error("Kalıcı hata (paper_id=%s): %s", paper_id, exc)
        await mark_failed(paper_id, str(exc))
        await message.ack()

    except Exception as exc:
        # Geçici olabilir (DB/MinIO erişilemedi). Kuyruğa geri koy.
        logger.exception("Geçici hata (paper_id=%s), mesaj kuyruğa iade ediliyor", paper_id)
        await message.nack(requeue=True)
        _ = exc


async def main() -> None:
    logger.info("HTR motoru: %s", settings.htr_engine)
    if settings.htr_engine != "mock":
        logger.info("Model ısıtılıyor (ilk seferde indirme uzun sürebilir)...")
        await asyncio.to_thread(get_engine().warmup)

    connection = await aio_pika.connect_robust(settings.rabbitmq_url)
    channel = await connection.channel()
    # SRS §1.3: aynı anda tek kağıt — GPU'yu boğmamak için.
    await channel.set_qos(prefetch_count=settings.prefetch_count)
    queue = await channel.declare_queue(settings.paper_queue, durable=True)

    logger.info(
        "Kuyruk dinleniyor: %s (prefetch=%s)", settings.paper_queue, settings.prefetch_count
    )
    await queue.consume(handle_message)

    await asyncio.Future()  # sonsuza kadar çalış


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Worker durduruldu.")
