"""Akreditasyon kanıt üretimi — MÜDEK / MEDEK / FEDEK / YÖKAK.

Hesap zinciri, üniversitenin gerçek OBS modelini izler:

    Soru ──(ağırlık %)──> DÇ (Ders Öğrenme Çıktısı) ──> PÇ (Program Öğrenme Çıktısı)

Bir sorunun bir DÇ'ye katkısı:

    katkı(soru, DÇ) = soru.max_score × ağırlık(soru, DÇ) / 100

Örnek (OBS ekranından): Soru 1 = 50 puan, DÇ1 ağırlığı %25
    → Soru 1'in DÇ1'e katkısı = 50 × 0.25 = 12.5 puan

Bir DÇ'nin sınıf edinim oranı:

    Σ (öğrencinin sorudan aldığı puan / sorunun tam puanı) × katkı(soru, DÇ)
    ────────────────────────────────────────────────────────────────────────
                    Σ katkı(soru, DÇ) × değerlendirilen öğrenci sayısı

PÇ edinimi ise, o PÇ'ye bağlı DÇ'lerin katkılarının toplamından hesaplanır.

Dört kural bilinçli ve hepsi kanıtın geçerliliği için kritik:

1. YALNIZCA ONAYLANMIŞ NOTLAR (`final_score`) sayılır. Yapay zekânın önerisi
   (`ai_score`) rapora GİRMEZ. Denetçiye sunulan sayı, bir akademisyenin
   imzaladığı nottur — makinenin tahmini değil.

2. SINAVA GİRMEYEN öğrenci paydaya girmez (OBS'nin "Girme Durum" alanı).
   Girseydi sınıfın başarı oranı yapay olarak düşer, rapor yalan söylerdi.

3. Hiçbir DÇ'ye bağlanmamış sorular hesaba katılmaz — ama raporda AÇIKÇA
   uyarı olarak listelenir. Sessizce yutmak, eksik kanıtı gizlemek olurdu.

4. OBS kısıtları (soru puanları toplamı %100, soru içi DÇ ağırlıkları toplamı
   %100) doğrulanır; ihlal varsa raporda uyarı olarak çıkar.
"""

from collections import defaultdict
from dataclasses import dataclass, field

from sinavokuma_shared import (
    Course,
    CourseOutcome,
    Exam,
    PaperScore,
    ProgramOutcome,
    Question,
    QuestionOutcome,
    StudentPaper,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

VARSAYILAN_ESIK = 50.0


@dataclass
class Attainment:
    code: str
    description: str
    earned: float  # öğrencilerin aldığı ağırlıklı puan toplamı
    possible: float  # alınabilecek ağırlıklı puan toplamı
    student_count: int
    question_numbers: list[int]
    threshold: float

    @property
    def pct(self) -> float:
        return round(self.earned / self.possible * 100, 1) if self.possible > 0 else 0.0

    @property
    def is_attained(self) -> bool:
        return self.pct >= self.threshold


@dataclass
class Report:
    exam_id: int
    exam_title: str
    course_code: str
    course_name: str
    department: str | None

    attended_students: int  # sınava giren
    approved_students: int  # notu onaylanmış (hesaba giren)
    total_students: int

    course_outcomes: list[Attainment] = field(default_factory=list)  # DÇ
    program_outcomes: list[Attainment] = field(default_factory=list)  # PÇ

    unmapped_questions: list[int] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


async def build_report(db: AsyncSession, exam: Exam, threshold: float = VARSAYILAN_ESIK) -> Report:
    course = await db.get(Course, exam.course_id, options=[selectinload(Course.department)])

    questions = list(
        (
            await db.execute(
                select(Question)
                .where(Question.exam_id == exam.id)
                .options(selectinload(Question.outcome_links))
                .order_by(Question.question_number)
            )
        )
        .scalars()
        .all()
    )

    papers = list(
        (await db.execute(select(StudentPaper).where(StudentPaper.exam_id == exam.id)))
        .scalars()
        .all()
    )
    attended = [p for p in papers if p.attended]
    # Kural 1 + 2: yalnızca sınava GİRMİŞ ve notu ONAYLANMIŞ öğrenciler.
    counted = [p for p in attended if p.status.value == "APPROVED"]
    counted_ids = {p.id for p in counted}

    warnings: list[str] = []

    # ── OBS kısıtı: soru puanları toplamı %100 olmalı ──
    total_weight = sum(float(q.max_score) for q in questions)
    if questions and abs(total_weight - 100.0) > 0.01:
        warnings.append(
            f"Soru puanları toplamı %{total_weight:.1f} — OBS kuralı %100 olmasını gerektirir."
        )

    # ── OBS kısıtı: her sorunun DÇ ağırlıkları %100'e tamamlanmalı ──
    unmapped: list[int] = []
    for q in questions:
        if not q.outcome_links:
            unmapped.append(q.question_number)
            continue
        w = sum(float(link.weight_pct) for link in q.outcome_links)
        if abs(w - 100.0) > 0.01:
            warnings.append(
                f"Soru {q.question_number}: ders çıktısı ağırlıkları toplamı %{w:.1f} "
                "— OBS kuralı %100 olmasını gerektirir."
            )

    # ── Onaylı puanları (soru, öğrenci) olarak topla ──
    earned_by_question: dict[int, float] = defaultdict(float)
    if counted_ids:
        rows = (
            await db.execute(
                select(PaperScore).where(
                    PaperScore.student_paper_id.in_(counted_ids),
                    PaperScore.final_score.is_not(None),
                )
            )
        ).scalars()
        for score in rows:
            earned_by_question[score.question_id] += float(score.final_score)

    n_students = len(counted)

    # ── DÇ (Ders Öğrenme Çıktısı) edinimi ──
    outcomes = list(
        (
            await db.execute(
                select(CourseOutcome)
                .where(CourseOutcome.course_id == exam.course_id)
                .options(selectinload(CourseOutcome.program_outcomes))
                .order_by(CourseOutcome.code)
            )
        )
        .scalars()
        .all()
    )

    links = list(
        (
            await db.execute(
                select(QuestionOutcome).where(
                    QuestionOutcome.question_id.in_([q.id for q in questions] or [0])
                )
            )
        )
        .scalars()
        .all()
    )
    links_by_outcome: dict[int, list[QuestionOutcome]] = defaultdict(list)
    for link in links:
        links_by_outcome[link.course_outcome_id].append(link)

    q_by_id = {q.id: q for q in questions}

    course_attainments: list[Attainment] = []
    # DÇ başına (earned, possible) — PÇ hesabında yeniden kullanılacak.
    dc_totals: dict[int, tuple[float, float, list[int]]] = {}

    for outcome in outcomes:
        outcome_links = links_by_outcome.get(outcome.id, [])
        if not outcome_links:
            continue

        earned = 0.0
        possible = 0.0
        q_numbers: list[int] = []

        for link in outcome_links:
            q = q_by_id.get(link.question_id)
            if q is None:
                continue
            q_max = float(q.max_score)
            if q_max <= 0:
                continue

            # Bu sorunun bu DÇ'ye katkısı (öğrenci başına)
            contribution = q_max * float(link.weight_pct) / 100.0

            # Öğrencilerin bu sorudan aldığı oran × katkı
            ratio_sum = earned_by_question.get(q.id, 0.0) / q_max  # öğrenci-oran toplamı
            earned += ratio_sum * contribution
            possible += contribution * n_students
            q_numbers.append(q.question_number)

        dc_totals[outcome.id] = (earned, possible, sorted(set(q_numbers)))
        course_attainments.append(
            Attainment(
                code=outcome.code,
                description=outcome.description,
                earned=round(earned, 2),
                possible=round(possible, 2),
                student_count=n_students,
                question_numbers=sorted(set(q_numbers)),
                threshold=threshold,
            )
        )

    # ── PÇ (Program Öğrenme Çıktısı) edinimi — DÇ'lerden toplanır ──
    program_attainments: list[Attainment] = []
    if course and course.department_id:
        program_outcomes = list(
            (
                await db.execute(
                    select(ProgramOutcome)
                    .where(ProgramOutcome.department_id == course.department_id)
                    .options(selectinload(ProgramOutcome.course_outcomes))
                    .order_by(ProgramOutcome.code)
                )
            )
            .scalars()
            .all()
        )

        for po in program_outcomes:
            earned = 0.0
            possible = 0.0
            q_numbers: list[int] = []
            for co in po.course_outcomes:
                totals = dc_totals.get(co.id)
                if totals is None:
                    continue
                e, p, qs = totals
                earned += e
                possible += p
                q_numbers.extend(qs)

            if possible <= 0:
                continue  # bu sınav bu PÇ'yi ölçmüyor

            program_attainments.append(
                Attainment(
                    code=po.code,
                    description=po.description,
                    earned=round(earned, 2),
                    possible=round(possible, 2),
                    student_count=n_students,
                    question_numbers=sorted(set(q_numbers)),
                    threshold=threshold,
                )
            )

    if unmapped:
        warnings.append(
            "Şu sorular hiçbir ders öğrenme çıktısına bağlanmamış ve kazanım hesabına "
            "DAHİL EDİLMEMİŞTİR: " + ", ".join(f"S{n}" for n in unmapped)
        )
    if n_students == 0:
        warnings.append(
            "Hiçbir kağıt onaylanmamış. Kazanım oranları yalnızca onaylanmış notlardan "
            "hesaplanır; rapor şu an boştur."
        )

    return Report(
        exam_id=exam.id,
        exam_title=exam.title,
        course_code=course.code if course else "?",
        course_name=course.name if course else "?",
        department=course.department.name if course and course.department else None,
        attended_students=len(attended),
        approved_students=n_students,
        total_students=len(papers),
        course_outcomes=course_attainments,
        program_outcomes=program_attainments,
        unmapped_questions=unmapped,
        warnings=warnings,
    )
