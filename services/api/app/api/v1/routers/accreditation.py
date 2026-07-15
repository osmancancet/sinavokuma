"""Akreditasyon kanıt uçları — MÜDEK / MEDEK / FEDEK / YÖKAK.

İki Excel çıktısı var ve ikisi farklı işe yarar:

  /accreditation.xlsx  → denetçiye verilecek kanıt dosyası (PÇ + DÇ edinimi + yöntem)
  /grades.xlsx         → OBS'ye yüklenecek not giriş listesi

İkincisi ürünün en somut faydası: hoca 312 satırı OBS'ye elle girmiyor.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sinavokuma_shared import Course, Exam, Question, StudentPaper
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.deps import DbSession, get_readable_exam
from app.services import accreditation, excel_export

router = APIRouter(tags=["akreditasyon"])

XLSX_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def _safe_filename(name: str) -> str:
    return "".join(c if c.isalnum() or c in "-_." else "_" for c in name)


class AttainmentRead(BaseModel):
    code: str
    description: str
    earned: float
    possible: float
    pct: float
    student_count: int
    question_numbers: list[int]
    threshold: float
    is_attained: bool


class ReportRead(BaseModel):
    exam_id: int
    exam_title: str
    course_code: str
    course_name: str
    department: str | None
    attended_students: int
    approved_students: int
    total_students: int
    program_outcomes: list[AttainmentRead]
    course_outcomes: list[AttainmentRead]
    unmapped_questions: list[int]
    warnings: list[str]


def _to_read(a) -> AttainmentRead:
    return AttainmentRead(
        code=a.code,
        description=a.description,
        earned=a.earned,
        possible=a.possible,
        pct=a.pct,
        student_count=a.student_count,
        question_numbers=a.question_numbers,
        threshold=a.threshold,
        is_attained=a.is_attained,
    )


@router.get(
    "/exams/{exam_id}/accreditation",
    response_model=ReportRead,
    summary="Kazanım edinim oranları (PÇ ve DÇ)",
)
async def get_report(
    exam: Annotated[Exam, Depends(get_readable_exam)],
    db: DbSession,
    threshold: Annotated[float, Query(ge=0, le=100, description="Edinim eşiği (%)")] = 50.0,
):
    """Yalnızca ONAYLANMIŞ notlardan ve SINAVA GİRMİŞ öğrencilerden hesaplanır."""
    r = await accreditation.build_report(db, exam, threshold)
    return ReportRead(
        exam_id=r.exam_id,
        exam_title=r.exam_title,
        course_code=r.course_code,
        course_name=r.course_name,
        department=r.department,
        attended_students=r.attended_students,
        approved_students=r.approved_students,
        total_students=r.total_students,
        program_outcomes=[_to_read(a) for a in r.program_outcomes],
        course_outcomes=[_to_read(a) for a in r.course_outcomes],
        unmapped_questions=r.unmapped_questions,
        warnings=r.warnings,
    )


@router.get(
    "/exams/{exam_id}/accreditation.xlsx",
    summary="Akreditasyon kanıt dosyası (Excel) — denetçiye verilir",
    response_class=StreamingResponse,
)
async def download_accreditation_xlsx(
    exam: Annotated[Exam, Depends(get_readable_exam)],
    db: DbSession,
    threshold: Annotated[float, Query(ge=0, le=100)] = 50.0,
):
    report = await accreditation.build_report(db, exam, threshold)
    content = excel_export.accreditation_workbook(report)
    name = _safe_filename(f"{report.course_code}_{report.exam_title}_kazanim_raporu.xlsx")
    return StreamingResponse(
        iter([content]),
        media_type=XLSX_MIME,
        headers={"Content-Disposition": f'attachment; filename="{name}"'},
    )


@router.get(
    "/exams/{exam_id}/grades.xlsx",
    summary="OBS not giriş listesi (Excel) — OBS'ye yüklenir",
    response_class=StreamingResponse,
)
async def download_obs_grades_xlsx(
    exam: Annotated[Exam, Depends(get_readable_exam)], db: DbSession
):
    """OBS'nin "Listeyi Excel'e Aktar" biçiminde not listesi.

    Yalnızca ONAYLANMIŞ notlar yazılır. Onaylanmamış kağıtların puan hücreleri boş
    kalır — yapay zekânın önerisi OBS'ye asla gitmez.
    """
    questions = list(
        (
            await db.execute(
                select(Question)
                .where(Question.exam_id == exam.id)
                .order_by(Question.question_number)
            )
        )
        .scalars()
        .all()
    )

    papers = list(
        (
            await db.execute(
                select(StudentPaper)
                .where(StudentPaper.exam_id == exam.id)
                .options(selectinload(StudentPaper.scores))
                .order_by(StudentPaper.student_no)
            )
        )
        .scalars()
        .all()
    )

    q_no_by_id = {q.id: q.question_number for q in questions}

    students = []
    for p in papers:
        scores: dict[int, float] = {}
        if p.status.value == "APPROVED":
            for s in p.scores:
                if s.final_score is not None:
                    q_no = q_no_by_id.get(s.question_id)
                    if q_no is not None:
                        scores[q_no] = float(s.final_score)
        students.append(
            {"student_no": p.student_no, "attended": p.attended, "scores": scores}
        )

    # exam.course lazy-load — async'te patlar. Ders kodunu ayrı çekiyoruz.
    course = await db.get(Course, exam.course_id)
    course_code = course.code if course else "?"
    content = excel_export.obs_grade_sheet(
        course_code=course_code,
        exam_title=exam.title,
        questions=[
            {"number": q.question_number, "max_score": float(q.max_score)} for q in questions
        ],
        students=students,
    )

    name = _safe_filename(f"{course_code}_{exam.title}_not_girisi.xlsx")
    return StreamingResponse(
        iter([content]),
        media_type=XLSX_MIME,
        headers={"Content-Disposition": f'attachment; filename="{name}"'},
    )
