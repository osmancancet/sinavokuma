"""Program (PÇ) ve Ders (DÇ) Öğrenme Çıktıları — akreditasyonun temeli.

Zincir: Soru ──(ağırlık %)──> DÇ ──> PÇ

Bu bağlantılar kurulmadan hiçbir akreditasyon raporu üretilemez. Rubrik hazırlanırken
bir kez yapılır, dönem sonunda kanıt kendiliğinden çıkar.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sinavokuma_shared import (
    Course,
    CourseOutcome,
    Department,
    Exam,
    ProgramOutcome,
    Question,
    QuestionOutcome,
    UserRole,
)
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload

from app.core.deps import CurrentUser, DbSession, get_owned_course, get_readable_exam, require_role
from app.schemas.outcome import (
    CourseOutcomeCreate,
    CourseOutcomeRead,
    ProgramOutcomeCreate,
    ProgramOutcomeRead,
    QuestionOutcomeRead,
    QuestionOutcomesUpdate,
)

router = APIRouter(tags=["kazanimlar"])

WriteAccess = Annotated[object, Depends(require_role(UserRole.TEACHER, UserRole.ADMIN))]
AdminOnly = Annotated[object, Depends(require_role(UserRole.ADMIN))]


# ── PÇ: Program Öğrenme Çıktıları (bölüm seviyesi) ──────────────────────


@router.post(
    "/departments/{department_id}/program-outcomes",
    response_model=ProgramOutcomeRead,
    status_code=status.HTTP_201_CREATED,
    summary="Bölüme program çıktısı (PÇ) ekle — yalnızca ADMIN",
)
async def create_program_outcome(
    department_id: int, payload: ProgramOutcomeCreate, db: DbSession, _: AdminOnly
):
    # PÇ'ler programın kimliğidir; bir hoca kendi başına değiştiremez.
    if await db.get(Department, department_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bölüm bulunamadı.")

    outcome = ProgramOutcome(**payload.model_dump(), department_id=department_id)
    db.add(outcome)
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Bu bölümde '{payload.code}' kodlu çıktı zaten var.",
        ) from exc
    await db.refresh(outcome)
    return outcome


@router.get(
    "/departments/{department_id}/program-outcomes", response_model=list[ProgramOutcomeRead]
)
async def list_program_outcomes(department_id: int, db: DbSession, user: CurrentUser):
    result = await db.execute(
        select(ProgramOutcome)
        .where(ProgramOutcome.department_id == department_id)
        .order_by(ProgramOutcome.code)
    )
    return list(result.scalars().all())


# ── DÇ: Ders Öğrenme Çıktıları (ders seviyesi) ──────────────────────────


@router.post(
    "/courses/{course_id}/outcomes",
    response_model=CourseOutcomeRead,
    status_code=status.HTTP_201_CREATED,
    summary="Derse ders çıktısı (DÇ) ekle ve PÇ'lere bağla",
)
async def create_course_outcome(
    payload: CourseOutcomeCreate,
    course: Annotated[Course, Depends(get_owned_course)],
    db: DbSession,
    _: WriteAccess,
):
    outcome = CourseOutcome(
        course_id=course.id, code=payload.code, description=payload.description
    )

    if payload.program_outcome_ids:
        pos = list(
            (
                await db.execute(
                    select(ProgramOutcome).where(
                        ProgramOutcome.id.in_(payload.program_outcome_ids)
                    )
                )
            )
            .scalars()
            .all()
        )
        missing = set(payload.program_outcome_ids) - {p.id for p in pos}
        if missing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Program çıktısı bulunamadı: {sorted(missing)}",
            )
        # DÇ, dersin bölümüne ait olmayan bir PÇ'yi besleyemez.
        yabanci = [p.code for p in pos if p.department_id != course.department_id]
        if yabanci:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Şu program çıktıları dersin bölümüne ait değil: {', '.join(yabanci)}"
                ),
            )
        outcome.program_outcomes = pos

    db.add(outcome)
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Bu derste '{payload.code}' kodlu çıktı zaten var.",
        ) from exc

    await db.refresh(outcome, ["program_outcomes"])
    return outcome


@router.get("/courses/{course_id}/outcomes", response_model=list[CourseOutcomeRead])
async def list_course_outcomes(
    course: Annotated[Course, Depends(get_owned_course)], db: DbSession
):
    result = await db.execute(
        select(CourseOutcome)
        .where(CourseOutcome.course_id == course.id)
        .options(selectinload(CourseOutcome.program_outcomes))
        .order_by(CourseOutcome.code)
    )
    return list(result.scalars().all())


# ── Soru ──(ağırlık)──> DÇ ─────────────────────────────────────────────


@router.put(
    "/questions/{question_id}/outcomes",
    response_model=list[QuestionOutcomeRead],
    summary="Sorunun ders çıktısı ağırlıklarını ayarla (OBS: DÇ1(%25), DÇ2(%25)...)",
)
async def set_question_outcomes(
    question_id: int,
    payload: QuestionOutcomesUpdate,
    user: CurrentUser,
    db: DbSession,
    _: WriteAccess,
):
    """Ağırlıkların toplamı %100 olmalı — şema katmanında zorlanıyor.

    Yanlış ağırlıkla kaydedilen bir soru, dönem sonunda tüm akreditasyon raporunu
    sessizce bozar. Hatayı burada yakalamak, denetim gününde yakalamaktan iyidir.
    """
    question = await db.get(
        Question, question_id, options=[selectinload(Question.outcome_links)]
    )
    if question is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Soru bulunamadı.")

    exam = await get_readable_exam(question.exam_id, user, db)

    # Verilen DÇ'ler gerçekten bu derse mi ait?
    outcome_ids = [w.course_outcome_id for w in payload.weights]
    valid = set(
        (
            await db.execute(
                select(CourseOutcome.id).where(
                    CourseOutcome.id.in_(outcome_ids),
                    CourseOutcome.course_id == exam.course_id,
                )
            )
        )
        .scalars()
        .all()
    )
    invalid = set(outcome_ids) - valid
    if invalid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Bu derse ait olmayan ders çıktısı: {sorted(invalid)}",
        )

    for link in list(question.outcome_links):
        await db.delete(link)
    await db.flush()

    for w in payload.weights:
        db.add(
            QuestionOutcome(
                question_id=question.id,
                course_outcome_id=w.course_outcome_id,
                weight_pct=w.weight_pct,
            )
        )
    await db.commit()

    result = await db.execute(
        select(QuestionOutcome).where(QuestionOutcome.question_id == question.id)
    )
    return list(result.scalars().all())


@router.get("/exams/{exam_id}/question-outcomes", summary="Sınavın soru–çıktı eşleştirme haritası")
async def question_outcome_map(
    exam: Annotated[Exam, Depends(get_readable_exam)], db: DbSession
):
    """OBS'nin 'Akreditasyon Soru Tanımları' ekranının verisi."""
    questions = list(
        (
            await db.execute(
                select(Question)
                .where(Question.exam_id == exam.id)
                .options(selectinload(Question.outcome_links))
                .order_by(Question.question_number)
            )
        )
        .scalars()
        .all()
    )

    outcomes = {
        o.id: o
        for o in (
            await db.execute(
                select(CourseOutcome)
                .where(CourseOutcome.course_id == exam.course_id)
                .options(selectinload(CourseOutcome.program_outcomes))
            )
        )
        .scalars()
        .all()
    }

    rows = []
    total_weight = 0.0
    for q in questions:
        total_weight += float(q.max_score)
        dc = []
        pc_codes: set[str] = set()
        for link in q.outcome_links:
            o = outcomes.get(link.course_outcome_id)
            if o is None:
                continue
            dc.append({"code": o.code, "weight_pct": float(link.weight_pct)})
            pc_codes.update(p.code for p in o.program_outcomes)

        rows.append(
            {
                "question_number": q.question_number,
                "max_score": float(q.max_score),
                "course_outcomes": sorted(dc, key=lambda d: d["code"]),
                "program_outcomes": sorted(pc_codes),
                "weight_total_pct": round(sum(d["weight_pct"] for d in dc), 2),
            }
        )

    return {
        "exam_id": exam.id,
        "questions": rows,
        # OBS: "Toplam Etki Oranı: %100"
        "total_question_weight_pct": round(total_weight, 2),
        "is_valid": abs(total_weight - 100.0) < 0.01
        and all(abs(r["weight_total_pct"] - 100.0) < 0.01 for r in rows if r["course_outcomes"]),
    }
