# `date` kolon adı sınıf gövdesinde `datetime.date` tipini gölgeler; gölgelenince
# SQLAlchemy Optional'ı çözemez ve kolonu NOT NULL yapar. Takma ad şart.
from datetime import date as DateType

from sqlalchemy import Date, ForeignKey, Numeric, String, Text, UniqueConstraint
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from sinavokuma_shared.models.base import Base, TimestampMixin
from sinavokuma_shared.enums import ExamStatus


class Exam(Base, TimestampMixin):
    __tablename__ = "exams"

    id: Mapped[int] = mapped_column(primary_key=True)
    course_id: Mapped[int] = mapped_column(
        ForeignKey("courses.id", ondelete="CASCADE"), index=True, nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    date: Mapped[DateType | None] = mapped_column(Date)
    total_score: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False, default=100)
    status: Mapped[ExamStatus] = mapped_column(
        SAEnum(ExamStatus, name="exam_status"), nullable=False, default=ExamStatus.DRAFT
    )

    course: Mapped["Course"] = relationship(back_populates="exams")  # noqa: F821
    questions: Mapped[list["Question"]] = relationship(
        back_populates="exam", cascade="all, delete-orphan", order_by="Question.question_number"
    )
    papers: Mapped[list["StudentPaper"]] = relationship(  # noqa: F821
        back_populates="exam", cascade="all, delete-orphan"
    )


class Question(Base, TimestampMixin):
    __tablename__ = "questions"
    __table_args__ = (
        UniqueConstraint("exam_id", "question_number", name="uq_question_exam_number"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    exam_id: Mapped[int] = mapped_column(
        ForeignKey("exams.id", ondelete="CASCADE"), index=True, nullable=False
    )
    question_number: Mapped[int] = mapped_column(nullable=False)
    max_score: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False)

    # SRS §4: bu FK olmadan akreditasyon raporu üretilemez.
    mudek_outcome_id: Mapped[int | None] = mapped_column(
        ForeignKey("mudek_outcomes.id", ondelete="SET NULL"), index=True
    )

    expected_answer: Mapped[str | None] = mapped_column(Text)

    # Değerlendirme anahtarı. Örn:
    #   [{"kriter": "Değişken tanımlamaları", "puan": 5},
    #    {"kriter": "Döngü mantığı", "puan": 10},
    #    {"kriter": "Sözdizimi hatasızlığı", "puan": 5}]
    rubric_criteria: Mapped[list[dict]] = mapped_column(JSONB, nullable=False, default=list)

    exam: Mapped["Exam"] = relationship(back_populates="questions")
    mudek_outcome: Mapped["MudekOutcome | None"] = relationship(  # noqa: F821
        back_populates="questions"
    )
    scores: Mapped[list["PaperScore"]] = relationship(  # noqa: F821
        back_populates="question", cascade="all, delete-orphan"
    )
