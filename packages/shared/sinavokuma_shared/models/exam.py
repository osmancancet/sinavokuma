# `date` kolon adı sınıf gövdesinde `datetime.date` tipini gölgeler; gölgelenince
# SQLAlchemy Optional'ı çözemez ve kolonu NOT NULL yapar. Takma ad şart.
from datetime import date as DateType

from sqlalchemy import Date, ForeignKey, Numeric, String, Text, UniqueConstraint
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from sinavokuma_shared.enums import ExamStatus
from sinavokuma_shared.models.base import Base, TimestampMixin


class Exam(Base, TimestampMixin):
    __tablename__ = "exams"

    id: Mapped[int] = mapped_column(primary_key=True)
    course_id: Mapped[int] = mapped_column(
        ForeignKey("courses.id", ondelete="CASCADE"), index=True, nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)  # Vize / Final / Bütünleme
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
    """Sınav sorusu.

    `max_score` OBS'deki "Soru Puan" / etki oranıdır. OBS kuralı: bir sınavdaki
    soruların puanları toplamda %100 olmalı, ve girilen puan sorunun etki oranını
    AŞAMAZ. Bu kısıt satırlar arası olduğu için DB'de zorlanamaz; API katmanında
    doğrulanır ve raporda ihlal açıkça bildirilir.

    Çıktı bağlantısı `outcome_links` üzerinden AĞIRLIKLI ve ÇOKA-ÇOK'tur — bir soru
    birden çok Ders Öğrenme Çıktısını (DÇ) farklı ağırlıklarla ölçebilir. (İlk şemada
    tek bir `mudek_outcome_id` FK'i vardı; gerçek OBS'yi ifade edemiyordu.)
    """

    __tablename__ = "questions"
    __table_args__ = (
        UniqueConstraint("exam_id", "question_number", name="uq_question_exam_number"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    exam_id: Mapped[int] = mapped_column(
        ForeignKey("exams.id", ondelete="CASCADE"), index=True, nullable=False
    )
    question_number: Mapped[int] = mapped_column(nullable=False)

    # OBS: "Soru Puan" — sınav içindeki etki oranı. Girilen puan bunu AŞAMAZ.
    max_score: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False)

    prompt: Mapped[str | None] = mapped_column(Text)  # sorunun metni
    expected_answer: Mapped[str | None] = mapped_column(Text)

    # Değerlendirme anahtarı. Örn:
    #   [{"kriter": "Değişken tanımlamaları", "puan": 5},
    #    {"kriter": "Döngü mantığı", "puan": 10}]
    rubric_criteria: Mapped[list[dict]] = mapped_column(JSONB, nullable=False, default=list)

    exam: Mapped["Exam"] = relationship(back_populates="questions")
    outcome_links: Mapped[list["QuestionOutcome"]] = relationship(  # noqa: F821
        back_populates="question", cascade="all, delete-orphan"
    )
    scores: Mapped[list["PaperScore"]] = relationship(  # noqa: F821
        back_populates="question", cascade="all, delete-orphan"
    )
