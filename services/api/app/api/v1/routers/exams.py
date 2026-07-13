from typing import Annotated

from fastapi import APIRouter, Depends, status
from sinavokuma_shared import Exam, Question, UserRole
from sqlalchemy import select

from app.core.deps import Course, DbSession, get_owned_course, get_readable_exam, require_role
from app.schemas.course import ExamCreate, ExamRead, QuestionCreate, QuestionRead

router = APIRouter(tags=["exams"])

WriteAccess = Annotated[object, Depends(require_role(UserRole.TEACHER, UserRole.ADMIN))]


@router.post(
    "/courses/{course_id}/exams",
    response_model=ExamRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_exam(
    payload: ExamCreate,
    course: Annotated[Course, Depends(get_owned_course)],
    db: DbSession,
    _: WriteAccess,
):
    exam = Exam(**payload.model_dump(), course_id=course.id)
    db.add(exam)
    await db.commit()
    await db.refresh(exam)
    return exam


@router.get("/courses/{course_id}/exams", response_model=list[ExamRead])
async def list_exams(course: Annotated[Course, Depends(get_owned_course)], db: DbSession):
    result = await db.execute(
        select(Exam).where(Exam.course_id == course.id).order_by(Exam.date.desc())
    )
    return list(result.scalars().all())


@router.get("/exams/{exam_id}", response_model=ExamRead)
async def get_exam(exam: Annotated[Exam, Depends(get_readable_exam)]):
    return exam


@router.post(
    "/exams/{exam_id}/questions",
    response_model=QuestionRead,
    status_code=status.HTTP_201_CREATED,
    summary="Sınava soru + rubrik ekle",
)
async def add_question(
    payload: QuestionCreate,
    exam: Annotated[Exam, Depends(get_readable_exam)],
    db: DbSession,
    _: WriteAccess,
):
    data = payload.model_dump()
    # Pydantic modellerini JSONB'ye yazılabilir düz dict listesine çeviriyoruz.
    data["rubric_criteria"] = [c.model_dump() for c in payload.rubric_criteria]

    question = Question(**data, exam_id=exam.id)
    db.add(question)
    await db.commit()
    await db.refresh(question)
    return question


@router.get("/exams/{exam_id}/questions", response_model=list[QuestionRead])
async def list_questions(exam: Annotated[Exam, Depends(get_readable_exam)], db: DbSession):
    result = await db.execute(
        select(Question).where(Question.exam_id == exam.id).order_by(Question.question_number)
    )
    return list(result.scalars().all())
