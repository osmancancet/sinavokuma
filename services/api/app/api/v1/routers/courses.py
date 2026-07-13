from typing import Annotated

from fastapi import APIRouter, Depends, status
from sinavokuma_shared import Course, MudekOutcome, UserRole
from sqlalchemy import select

from app.core.deps import CurrentUser, DbSession, get_owned_course, require_role
from app.schemas.course import CourseCreate, CourseRead, MudekOutcomeCreate, MudekOutcomeRead

router = APIRouter(prefix="/courses", tags=["courses"])

# Ders oluşturmak/düzenlemek TEACHER ve ADMIN'e açık; AUDITOR salt-okunur (SRS §5).
WriteAccess = Annotated[object, Depends(require_role(UserRole.TEACHER, UserRole.ADMIN))]


@router.post("", response_model=CourseRead, status_code=status.HTTP_201_CREATED)
async def create_course(payload: CourseCreate, user: CurrentUser, db: DbSession, _: WriteAccess):
    course = Course(**payload.model_dump(), teacher_id=user.id)
    db.add(course)
    await db.commit()
    await db.refresh(course)
    return course


@router.get("", response_model=list[CourseRead], summary="Derslerimi listele")
async def list_courses(user: CurrentUser, db: DbSession):
    query = select(Course).order_by(Course.code)
    # TEACHER yalnızca kendi derslerini görür; ADMIN/AUDITOR hepsini.
    if user.role == UserRole.TEACHER:
        query = query.where(Course.teacher_id == user.id)
    result = await db.execute(query)
    return list(result.scalars().all())


@router.get("/{course_id}", response_model=CourseRead)
async def get_course(course: Annotated[Course, Depends(get_owned_course)]):
    return course


@router.post(
    "/{course_id}/mudek-outcomes",
    response_model=MudekOutcomeRead,
    status_code=status.HTTP_201_CREATED,
    summary="Derse MÜDEK çıktısı ekle",
)
async def add_mudek_outcome(
    payload: MudekOutcomeCreate,
    course: Annotated[Course, Depends(get_owned_course)],
    db: DbSession,
    _: WriteAccess,
):
    outcome = MudekOutcome(**payload.model_dump(), course_id=course.id)
    db.add(outcome)
    await db.commit()
    await db.refresh(outcome)
    return outcome


@router.get("/{course_id}/mudek-outcomes", response_model=list[MudekOutcomeRead])
async def list_mudek_outcomes(
    course: Annotated[Course, Depends(get_owned_course)],
    db: DbSession,
):
    result = await db.execute(
        select(MudekOutcome)
        .where(MudekOutcome.course_id == course.id)
        .order_by(MudekOutcome.outcome_code)
    )
    return list(result.scalars().all())
