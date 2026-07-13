from sqlalchemy import ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from sinavokuma_shared.models.base import Base, TimestampMixin


class Department(Base, TimestampMixin):
    """SRS'te tablo olarak tanımlanmamış ama `courses.department_id` ona işaret ediyor."""

    __tablename__ = "departments"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    faculty: Mapped[str | None] = mapped_column(String(255))

    courses: Mapped[list["Course"]] = relationship(back_populates="department")


class Course(Base, TimestampMixin):
    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(32), index=True, nullable=False)  # örn: BMG101
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
    mudek_outcomes: Mapped[list["MudekOutcome"]] = relationship(
        back_populates="course", cascade="all, delete-orphan"
    )


class MudekOutcome(Base, TimestampMixin):
    """SRS §4: MÜDEK ders kazanımları. Akreditasyon kanıt dosyasının temeli."""

    __tablename__ = "mudek_outcomes"
    __table_args__ = (
        # Aynı derste aynı çıktı kodu iki kez tanımlanamaz (Ç1, Ç2, ...).
        UniqueConstraint("course_id", "outcome_code", name="uq_mudek_course_code"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    course_id: Mapped[int] = mapped_column(
        ForeignKey("courses.id", ondelete="CASCADE"), index=True, nullable=False
    )
    outcome_code: Mapped[str] = mapped_column(String(16), nullable=False)  # örn: Ç1
    description: Mapped[str] = mapped_column(Text, nullable=False)

    course: Mapped["Course"] = relationship(back_populates="mudek_outcomes")
    questions: Mapped[list["Question"]] = relationship(  # noqa: F821
        back_populates="mudek_outcome"
    )
