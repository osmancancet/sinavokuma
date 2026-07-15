from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from sinavokuma_shared.models.base import Base, TimestampMixin


class Department(Base, TimestampMixin):
    """Bölüm / program. Program Öğrenme Çıktıları (PÇ) buraya aittir — derse değil.

    Aynı PÇ birden çok dersten beslenir; MÜDEK/MEDEK bu seviyeyi denetler.
    """

    __tablename__ = "departments"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    faculty: Mapped[str | None] = mapped_column(String(255))

    courses: Mapped[list["Course"]] = relationship(back_populates="department")
    program_outcomes: Mapped[list["ProgramOutcome"]] = relationship(  # noqa: F821
        back_populates="department", cascade="all, delete-orphan"
    )


class Course(Base, TimestampMixin):
    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(32), index=True, nullable=False)  # örn: BVA1108
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    department_id: Mapped[int | None] = mapped_column(
        ForeignKey("departments.id", ondelete="SET NULL")
    )
    teacher_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )

    department: Mapped["Department | None"] = relationship(back_populates="courses")
    teacher: Mapped["User"] = relationship(back_populates="courses")  # noqa: F821
    exams: Mapped[list["Exam"]] = relationship(  # noqa: F821
        back_populates="course", cascade="all, delete-orphan"
    )
    course_outcomes: Mapped[list["CourseOutcome"]] = relationship(  # noqa: F821
        back_populates="course", cascade="all, delete-orphan"
    )
