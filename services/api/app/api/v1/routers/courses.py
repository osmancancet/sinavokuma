from typing import Annotated

from fastapi import APIRouter, Depends, status
from sinavokuma_shared import Course, Department, UserRole
from sqlalchemy import select

from app.core.deps import CurrentUser, DbSession, get_owned_course, require_role
from app.schemas.course import CourseCreate, CourseRead, DepartmentCreate, DepartmentRead

router = APIRouter(tags=["dersler"])

# Ders oluşturmak/düzenlemek TEACHER ve ADMIN'e açık; AUDITOR salt-okunur (SRS §5).
WriteAccess = Annotated[object, Depends(require_role(UserRole.TEACHER, UserRole.ADMIN))]
AdminOnly = Annotated[object, Depends(require_role(UserRole.ADMIN))]


# ── Bölümler (PÇ'ler buraya bağlanır) ──────────────────────────────────


@router.post(
    "/departments",
    response_model=DepartmentRead,
    status_code=status.HTTP_201_CREATED,
    summary="Bölüm oluştur — yalnızca ADMIN",
)
async def create_department(payload: DepartmentCreate, db: DbSession, _: AdminOnly):
    dept = Department(**payload.model_dump())
    db.add(dept)
    await db.commit()
    await db.refresh(dept)
    return dept


@router.get("/departments", response_model=list[DepartmentRead])
async def list_departments(db: DbSession, user: CurrentUser):
    result = await db.execute(select(Department).order_by(Department.name))
    return list(result.scalars().all())


# ── Dersler ────────────────────────────────────────────────────────────


@router.post("/courses", response_model=CourseRead, status_code=status.HTTP_201_CREATED)
async def create_course(payload: CourseCreate, user: CurrentUser, db: DbSession, _: WriteAccess):
    course = Course(**payload.model_dump(), teacher_id=user.id)
    db.add(course)
    await db.commit()
    await db.refresh(course)
    return course


@router.get("/courses", response_model=list[CourseRead], summary="Derslerimi listele")
async def list_courses(user: CurrentUser, db: DbSession):
    query = select(Course).order_by(Course.code)
    # TEACHER yalnızca kendi derslerini görür; ADMIN/AUDITOR hepsini.
    if user.role == UserRole.TEACHER:
        query = query.where(Course.teacher_id == user.id)
    result = await db.execute(query)
    return list(result.scalars().all())


@router.get("/courses/{course_id}", response_model=CourseRead)
async def get_course(course: Annotated[Course, Depends(get_owned_course)]):
    return course
