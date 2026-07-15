from sqlalchemy import ForeignKey, Numeric, String, Text, UniqueConstraint
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from sinavokuma_shared.enums import PaperStatus
from sinavokuma_shared.models.base import Base, TimestampMixin


class StudentPaper(Base, TimestampMixin):
    __tablename__ = "student_papers"
    __table_args__ = (
        # Bir sınavda bir öğrencinin tek kağıdı olur. Mobil uygulamanın çevrimdışı
        # senkronizasyonu aynı kağıdı iki kez göndermeye çalışırsa DB'de durur.
        UniqueConstraint("exam_id", "student_no", name="uq_paper_exam_student"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    exam_id: Mapped[int] = mapped_column(
        ForeignKey("exams.id", ondelete="CASCADE"), index=True, nullable=False
    )
    # Öğrenci numarası tek tanımlayıcıdır. Ad/soyad BİLEREK tutulmuyor: kağıtta
    # sadece numara yazılı, ad-soyad eşleştirmesi OBS'de zaten var. İsim saklamak
    # gereksiz hassas veri biriktirmek olurdu (KVKK — veri minimizasyonu).
    student_no: Mapped[str] = mapped_column(String(32), index=True, nullable=False)

    # OBS: "Girme Durum" (Girdi / Girmedi).
    # Sınava girmeyen öğrenci kazanım hesabının PAYDASINA girmez — girerse sınıfın
    # başarı oranı yapay olarak düşer ve akreditasyon raporu yanlış çıkar.
    attended: Mapped[bool] = mapped_column(nullable=False, default=True)

    # MinIO nesne anahtarı (örn: "exams/12/papers/20210101.jpg"). Tam URL değil —
    # URL'ler presigned olarak anlık üretilir, kalıcı saklanmaz.
    # Sınava girmeyen öğrencinin kağıdı yoktur; bu yüzden boş olabilir.
    image_url: Mapped[str | None] = mapped_column(String(512))

    status: Mapped[PaperStatus] = mapped_column(
        SAEnum(PaperStatus, name="paper_status"), nullable=False, default=PaperStatus.PENDING
    )
    error_message: Mapped[str | None] = mapped_column(Text)

    exam: Mapped["Exam"] = relationship(back_populates="papers")  # noqa: F821
    scores: Mapped[list["PaperScore"]] = relationship(
        back_populates="paper", cascade="all, delete-orphan"
    )


class PaperScore(Base, TimestampMixin):
    """Bir kağıdın tek bir sorusuna verilen not.

    SRS §3.2 (Human-in-the-Loop): `ai_score` yapay zekânın ÖNERİSİDİR ve asla
    değiştirilmez — denetim izi olarak kalır. Akademisyenin onayladığı/düzelttiği
    not `final_score`'a yazılır.

    İkisini ayrı tutmak, denetçinin "makine ne dedi, insan ne karar verdi" sorusunu
    her kağıt için cevaplayabilmesini sağlar. Akreditasyon raporuna YALNIZCA
    `final_score` girer.
    """

    __tablename__ = "paper_scores"
    __table_args__ = (
        UniqueConstraint("student_paper_id", "question_id", name="uq_score_paper_question"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    student_paper_id: Mapped[int] = mapped_column(
        ForeignKey("student_papers.id", ondelete="CASCADE"), index=True, nullable=False
    )
    question_id: Mapped[int] = mapped_column(
        ForeignKey("questions.id", ondelete="CASCADE"), index=True, nullable=False
    )

    ai_raw_text: Mapped[str | None] = mapped_column(Text)  # HTR'ın okuduğu ham metin
    ai_score: Mapped[float | None] = mapped_column(Numeric(6, 2))
    ai_reasoning: Mapped[str | None] = mapped_column(Text)  # neden bu puanı verdi (CoT)

    final_score: Mapped[float | None] = mapped_column(Numeric(6, 2))
    reviewed_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))

    paper: Mapped["StudentPaper"] = relationship(back_populates="scores")
    question: Mapped["Question"] = relationship(back_populates="scores")  # noqa: F821
