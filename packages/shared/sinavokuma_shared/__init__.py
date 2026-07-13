"""Core API ile Inference servisinin ortak veritabanı katmanı.

Şema tek yerde tanımlanır. İki servise kopyalansaydı, biri değişip diğeri
değişmediğinde ortaya çıkacak sessiz veri bozulmasını hiçbir test yakalayamazdı.
"""

from sinavokuma_shared.enums import ExamStatus, PaperStatus, UserRole
from sinavokuma_shared.models import (
    Base,
    Course,
    Department,
    Exam,
    MudekOutcome,
    PaperScore,
    Question,
    StudentPaper,
    User,
)

__all__ = [
    "Base",
    "Course",
    "Department",
    "Exam",
    "ExamStatus",
    "MudekOutcome",
    "PaperScore",
    "PaperStatus",
    "Question",
    "StudentPaper",
    "User",
    "UserRole",
]
