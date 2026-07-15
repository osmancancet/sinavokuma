"""Geliştirme verisi — gerçek OBS senaryosunu birebir kurar.

OBS ekran görüntüsündeki BVA1108 dersini örnek alır:
  Soru 1 (50 puan) → DÇ1(%25), DÇ2(%25), DÇ3(%25), DÇ4(%25) → PÇ1, PÇ3, PÇ4
  Soru 2 (50 puan) → aynı
  Toplam Etki Oranı: %100

    cd services/api && uv run python -m scripts.seed
"""

import asyncio

from sinavokuma_shared import (
    Course,
    CourseOutcome,
    Department,
    Exam,
    ProgramOutcome,
    Question,
    QuestionOutcome,
    User,
    UserRole,
)
from sqlalchemy import select

from app.core.security import hash_password
from app.db.session import AsyncSessionLocal

USERS = [
    ("admin@uni.edu.tr", "Sistem Yöneticisi", "admin1234", UserRole.ADMIN),
    ("hoca@uni.edu.tr", "Dr. Ayşe Yılmaz", "hoca1234", UserRole.TEACHER),
    ("denetci@uni.edu.tr", "MEDEK Denetçisi", "denetci1234", UserRole.AUDITOR),
]

RUBRIC = [
    {"kriter": "Değişken tanımlamaları", "puan": 12.5},
    {"kriter": "Döngü/işlem mantığı", "puan": 25},
    {"kriter": "Sözdizimi hatasızlığı", "puan": 12.5},
]


async def main() -> None:
    async with AsyncSessionLocal() as db:
        created: dict[UserRole, User] = {}
        for email, full_name, password, role in USERS:
            if await db.scalar(select(User).where(User.email == email)):
                print(f"  = {email} zaten var")
                continue
            user = User(
                email=email,
                full_name=full_name,
                password_hash=hash_password(password),
                role=role,
            )
            db.add(user)
            await db.flush()
            created[role] = user
            print(f"  + {email} ({role.value}) / parola: {password}")

        teacher = created.get(UserRole.TEACHER) or await db.scalar(
            select(User).where(User.role == UserRole.TEACHER)
        )

        if await db.scalar(select(Course).where(Course.code == "BVA1108")):
            print("  = BVA1108 zaten var")
            await db.commit()
            print("\nSeed tamamlandı.")
            return

        dept = Department(name="Bilgisayar Programcılığı", faculty="Meslek Yüksekokulu")
        db.add(dept)
        await db.flush()

        pc = {}
        for code, desc in [
            ("PÇ1", "Temel programlama kavramlarını uygulama"),
            ("PÇ3", "Algoritma geliştirme ve problem çözme"),
            ("PÇ4", "Bilgi teknolojilerini etkin kullanma"),
        ]:
            po = ProgramOutcome(department_id=dept.id, code=code, description=desc)
            db.add(po)
            pc[code] = po
        await db.flush()

        course = Course(
            code="BVA1108",
            name="Bilgi Teknolojileri",
            department_id=dept.id,
            teacher_id=teacher.id,
        )
        db.add(course)
        await db.flush()

        dc = {}
        for code, desc, po_codes in [
            ("DÇ1", "Değişken ve veri tiplerini kullanabilme", ["PÇ1"]),
            ("DÇ2", "Döngü ve koşul yapılarını kurabilme", ["PÇ1", "PÇ3"]),
            ("DÇ3", "Algoritma tasarlayabilme", ["PÇ3"]),
            ("DÇ4", "Kod yazım standartlarına uyabilme", ["PÇ4"]),
        ]:
            co = CourseOutcome(course_id=course.id, code=code, description=desc)
            co.program_outcomes = [pc[c] for c in po_codes]
            db.add(co)
            dc[code] = co
        await db.flush()

        exam = Exam(course_id=course.id, title="Bütünleme", total_score=100)
        db.add(exam)
        await db.flush()

        for qno in (1, 2):
            q = Question(
                exam_id=exam.id,
                question_number=qno,
                max_score=50,
                prompt="1'den n'e kadar olan sayıların toplamını bulan program yazın.",
                expected_answer="1'den n'e kadar toplama yapan döngü veya formül.",
                rubric_criteria=RUBRIC,
            )
            db.add(q)
            await db.flush()
            for code in ("DÇ1", "DÇ2", "DÇ3", "DÇ4"):
                db.add(
                    QuestionOutcome(
                        question_id=q.id, course_outcome_id=dc[code].id, weight_pct=25
                    )
                )

        await db.commit()
        print("  + Bölüm, 3 PÇ, ders BVA1108, 4 DÇ, Bütünleme sınavı (2 soru × 50p)")
        print(f"    exam_id={exam.id}, her soru DÇ1-4'e %25 ağırlıkla bağlı")

    print("\nSeed tamamlandı.")


if __name__ == "__main__":
    asyncio.run(main())
