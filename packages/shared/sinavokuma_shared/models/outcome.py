"""Akreditasyon çıktı modeli — gerçek OBS yapısına göre.

İLK TASARIMIM YANLIŞTI. `questions.mudek_outcome_id` diye tek bir foreign key
koymuştum: bir soru, bir çıktı. Üniversitenin gerçek OBS ekranı bunun böyle
olmadığını gösterdi.

Gerçek yapı iki katmanlı ve ağırlıklı:

    Soru ──(ağırlık %)──> DÇ (Ders Öğrenme Çıktısı) ──> PÇ (Program Öğrenme Çıktısı)
                                                          ↑
                                              MÜDEK/MEDEK burayı denetler

OBS ekranından birebir örnek:

    Soru 1 (50 puan) → DÇ1(%25), DÇ2(%25), DÇ3(%25), DÇ4(%25) → PÇ1, PÇ3, PÇ4
    Soru 2 (50 puan) → DÇ1(%25), DÇ2(%25), DÇ3(%25), DÇ4(%25) → PÇ1, PÇ3, PÇ4
    Toplam Etki Oranı: %100

İki kısıt OBS'nin kendi kuralları:
  - Soru puanları (etki oranları) sınav genelinde %100'e tamamlanmalı.
  - Bir sorunun DÇ ağırlıkları o soru içinde %100'e tamamlanmalı.

Bu kısıtları veritabanı seviyesinde zorlayamayız (satırlar arası toplam), ama
API katmanında zorluyoruz ve raporda ihlalleri açıkça bildiriyoruz.
"""

from sqlalchemy import ForeignKey, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from sinavokuma_shared.models.base import Base, TimestampMixin


class ProgramOutcome(Base, TimestampMixin):
    """PÇ — Program Öğrenme Çıktısı.

    Bölümün/programın çıktısı. MÜDEK, MEDEK, FEDEK ve YÖKAK bu seviyeyi denetler.
    Derse değil, PROGRAMA aittir — aynı PÇ birden çok dersten beslenir.
    """

    __tablename__ = "program_outcomes"
    __table_args__ = (
        UniqueConstraint("department_id", "code", name="uq_program_outcome_dept_code"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    department_id: Mapped[int] = mapped_column(
        ForeignKey("departments.id", ondelete="CASCADE"), index=True, nullable=False
    )
    code: Mapped[str] = mapped_column(String(16), nullable=False)  # PÇ1, PÇ2, ...
    description: Mapped[str] = mapped_column(Text, nullable=False)

    department: Mapped["Department"] = relationship(  # noqa: F821
        back_populates="program_outcomes"
    )
    course_outcomes: Mapped[list["CourseOutcome"]] = relationship(
        secondary="course_outcome_program_outcomes", back_populates="program_outcomes"
    )


class CourseOutcome(Base, TimestampMixin):
    """DÇ — Ders Öğrenme Çıktısı. Derse aittir; bir veya çok PÇ'yi besler."""

    __tablename__ = "course_outcomes"
    __table_args__ = (UniqueConstraint("course_id", "code", name="uq_course_outcome_code"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    course_id: Mapped[int] = mapped_column(
        ForeignKey("courses.id", ondelete="CASCADE"), index=True, nullable=False
    )
    code: Mapped[str] = mapped_column(String(16), nullable=False)  # DÇ1, DÇ2, ...
    description: Mapped[str] = mapped_column(Text, nullable=False)

    course: Mapped["Course"] = relationship(back_populates="course_outcomes")  # noqa: F821
    program_outcomes: Mapped[list["ProgramOutcome"]] = relationship(
        secondary="course_outcome_program_outcomes", back_populates="course_outcomes"
    )
    question_links: Mapped[list["QuestionOutcome"]] = relationship(
        back_populates="course_outcome", cascade="all, delete-orphan"
    )


class CourseOutcomeProgramOutcome(Base):
    """DÇ–PÇ ilişki matrisi. Akreditasyon dosyalarının klasik "ilişki matrisi" tablosu."""

    __tablename__ = "course_outcome_program_outcomes"

    course_outcome_id: Mapped[int] = mapped_column(
        ForeignKey("course_outcomes.id", ondelete="CASCADE"), primary_key=True
    )
    program_outcome_id: Mapped[int] = mapped_column(
        ForeignKey("program_outcomes.id", ondelete="CASCADE"), primary_key=True
    )


class QuestionOutcome(Base):
    """Soru–DÇ bağı, AĞIRLIKLI.

    OBS'deki `DÇ1(%25), DÇ2(%25), DÇ3(%25), DÇ4(%25)` satırının karşılığı.
    Bir sorunun ağırlıkları o soru içinde %100'e tamamlanmalıdır (OBS kuralı).

    Bu tablo olmadan "bir soru birden çok çıktıyı ölçer" gerçeği ifade edilemez —
    ilk şemamın en büyük eksiği buydu.
    """

    __tablename__ = "question_outcomes"

    question_id: Mapped[int] = mapped_column(
        ForeignKey("questions.id", ondelete="CASCADE"), primary_key=True
    )
    course_outcome_id: Mapped[int] = mapped_column(
        ForeignKey("course_outcomes.id", ondelete="CASCADE"), primary_key=True
    )
    # Bu sorunun puanının yüzde kaçı bu DÇ'yi ölçüyor (örn. 25.00 = %25)
    weight_pct: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)

    question: Mapped["Question"] = relationship(back_populates="outcome_links")  # noqa: F821
    course_outcome: Mapped["CourseOutcome"] = relationship(back_populates="question_links")
