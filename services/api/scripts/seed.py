"""Geliştirme verisi: ilk ADMIN + örnek TEACHER/AUDITOR + bir ders/sınav/rubrik.

`/auth/register` ucu ADMIN yetkisi ister; ilk ADMIN'i API üzerinden açmanın yolu yok.
Bu script o kilidi açar.

    cd services/api && uv run python -m scripts.seed
"""

import asyncio

from sqlalchemy import select

from app.core.security import hash_password
from app.db.session import AsyncSessionLocal
from app.models import Course, Exam, MudekOutcome, Question, User, UserRole

USERS = [
    ("admin@uni.edu.tr", "Sistem Yöneticisi", "admin1234", UserRole.ADMIN),
    ("hoca@uni.edu.tr", "Dr. Ayşe Yılmaz", "hoca1234", UserRole.TEACHER),
    ("denetci@uni.edu.tr", "MÜDEK Denetçisi", "denetci1234", UserRole.AUDITOR),
]


async def main() -> None:
    async with AsyncSessionLocal() as db:
        created: dict[UserRole, User] = {}

        for email, full_name, password, role in USERS:
            existing = await db.scalar(select(User).where(User.email == email))
            if existing:
                print(f"  = {email} zaten var")
                created[role] = existing
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

        teacher = created[UserRole.TEACHER]

        course = await db.scalar(select(Course).where(Course.code == "BMG101"))
        if course is None:
            course = Course(code="BMG101", name="Programlamaya Giriş", teacher_id=teacher.id)
            db.add(course)
            await db.flush()

            outcome = MudekOutcome(
                course_id=course.id,
                outcome_code="Ç1",
                description="Karmaşık mühendislik problemlerini çözme becerisi",
            )
            db.add(outcome)
            await db.flush()

            exam = Exam(course_id=course.id, title="Vize Sınavı", total_score=100)
            db.add(exam)
            await db.flush()

            # SRS §2'deki rubrik örneği birebir.
            db.add(
                Question(
                    exam_id=exam.id,
                    question_number=1,
                    max_score=20,
                    mudek_outcome_id=outcome.id,
                    expected_answer="1'den N'e kadar olan sayıların toplamını bulan döngü.",
                    rubric_criteria=[
                        {"kriter": "Değişken tanımlamaları", "puan": 5},
                        {"kriter": "Döngü mantığı", "puan": 10},
                        {"kriter": "Sözdizimi hatasızlığı", "puan": 5},
                    ],
                )
            )
            print(f"  + Ders BMG101 (id={course.id}), Vize Sınavı (id={exam.id}), 1 soru + rubrik")
        else:
            print("  = BMG101 zaten var")

        await db.commit()

    print("\nSeed tamamlandı.")


if __name__ == "__main__":
    asyncio.run(main())
