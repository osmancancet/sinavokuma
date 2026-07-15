"""SRS §3.2 — Human-in-the-Loop onay uçları.

Bu dosya ürünün ahlaki merkezidir. Yapay zekânın önerisi (`ai_score`) hiçbir zaman
değişmez; akademisyenin kararı (`final_score`) ayrı bir alana yazılır. İkisini ayrı
tutmak, dönem sonunda denetçinin "makine ne dedi, insan ne karar verdi" sorusunu
cevaplayabilmemizi sağlar.

Bir kağıt, TÜM sorularının notu onaylanmadan APPROVED olamaz — yarım onaylanmış bir
kağıdın notu akreditasyon raporuna girerse rapor yalan söyler.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sinavokuma_shared import Exam, ExamStatus, PaperStatus, StudentPaper, UserRole
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.deps import CurrentUser, DbSession, get_readable_exam, require_role
from app.services import storage

router = APIRouter(tags=["degerlendirme"])

WriteAccess = Annotated[object, Depends(require_role(UserRole.TEACHER, UserRole.ADMIN))]


class ScoreRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    question_id: int
    ai_raw_text: str | None
    ai_score: float | None
    ai_reasoning: str | None
    final_score: float | None
    reviewed_by_id: int | None


class ReviewScreen(BaseModel):
    """Değerlendirme ekranının ihtiyaç duyduğu her şey, tek çağrıda.

    Sol tarafta gösterilecek kağıt görselinin imzalı URL'i de burada — bucket
    public değil, görsel yalnızca süreli imzalı bağlantıyla okunur (KVKK).
    """

    paper_id: int
    student_no: str
    status: PaperStatus
    image_url: str
    scores: list[ScoreRead]


class ScoreDecision(BaseModel):
    score_id: int
    final_score: float = Field(ge=0)


class ApprovePaper(BaseModel):
    """Boş bırakılırsa AI'ın önerdiği puanlar aynen onaylanır (tek tıkla onay)."""

    decisions: list[ScoreDecision] = Field(default_factory=list)


@router.get("/papers/{paper_id}/review", response_model=ReviewScreen)
async def get_review_screen(paper_id: int, user: CurrentUser, db: DbSession):
    paper = await db.get(
        StudentPaper, paper_id, options=[selectinload(StudentPaper.scores)]
    )
    if paper is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Kağıt bulunamadı.")
    await get_readable_exam(paper.exam_id, user, db)

    return ReviewScreen(
        paper_id=paper.id,
        student_no=paper.student_no,
        status=paper.status,
        image_url=storage.presigned_get_url(paper.image_url),
        scores=[ScoreRead.model_validate(s) for s in paper.scores],
    )


@router.post(
    "/papers/{paper_id}/approve",
    response_model=ReviewScreen,
    summary="Notları onayla (SRS §3.2 — notun kesinleştiği tek yer)",
)
async def approve_paper(
    paper_id: int, payload: ApprovePaper, user: CurrentUser, db: DbSession, _: WriteAccess
):
    paper = await db.get(StudentPaper, paper_id, options=[selectinload(StudentPaper.scores)])
    if paper is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Kağıt bulunamadı.")
    await get_readable_exam(paper.exam_id, user, db)

    if paper.status not in (PaperStatus.AI_SCORED, PaperStatus.APPROVED):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Kağıt henüz değerlendirilmemiş (durum: {paper.status.value}).",
        )

    overrides = {d.score_id: d.final_score for d in payload.decisions}
    by_id = {s.id: s for s in paper.scores}

    unknown = set(overrides) - set(by_id)
    if unknown:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Bu kağıda ait olmayan puan kaydı: {sorted(unknown)}",
        )

    for score in paper.scores:
        # Hoca değer verdiyse onu; vermediyse AI'ın önerisini onaylamış sayılır.
        # ai_score'a DOKUNULMAZ — denetim izi olarak kalır.
        score.final_score = overrides.get(score.id, score.ai_score)
        score.reviewed_by_id = user.id

    # Notu olmayan bir soru kalırsa kağıt onaylanmış sayılamaz; aksi halde eksik
    # notlu bir kağıt akreditasyon raporuna dahil olur ve rapor yanlış çıkar.
    if any(s.final_score is None for s in paper.scores) or not paper.scores:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Tüm soruların notu belirlenmeden kağıt onaylanamaz.",
        )

    paper.status = PaperStatus.APPROVED
    await db.commit()

    # Sınavdaki tüm kağıtlar onaylandıysa sınavı COMPLETED yap.
    remaining = await db.scalar(
        select(StudentPaper.id)
        .where(
            StudentPaper.exam_id == paper.exam_id,
            StudentPaper.status != PaperStatus.APPROVED,
        )
        .limit(1)
    )
    if remaining is None:
        exam = await db.get(Exam, paper.exam_id)
        if exam is not None:
            exam.status = ExamStatus.COMPLETED
            await db.commit()

    await db.refresh(paper)
    return ReviewScreen(
        paper_id=paper.id,
        student_no=paper.student_no,
        status=paper.status,
        image_url=storage.presigned_get_url(paper.image_url),
        scores=[ScoreRead.model_validate(s) for s in paper.scores],
    )
