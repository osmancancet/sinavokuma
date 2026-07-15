"""Veritabanı şeması — gerçek OBS akreditasyon modeline göre.

Çıktı zinciri iki katmanlı ve ağırlıklıdır:

    Soru ──(ağırlık %)──> DÇ (Ders Öğrenme Çıktısı) ──> PÇ (Program Öğrenme Çıktısı)
                                                          ↑ MÜDEK/MEDEK burayı denetler
"""

from sinavokuma_shared.models.base import Base, TimestampMixin
from sinavokuma_shared.models.course import Course, Department
from sinavokuma_shared.models.exam import Exam, Question
from sinavokuma_shared.models.outcome import (
    CourseOutcome,
    CourseOutcomeProgramOutcome,
    ProgramOutcome,
    QuestionOutcome,
)
from sinavokuma_shared.models.paper import PaperScore, StudentPaper
from sinavokuma_shared.models.user import User

__all__ = [
    "Base",
    "Course",
    "CourseOutcome",
    "CourseOutcomeProgramOutcome",
    "Department",
    "Exam",
    "PaperScore",
    "ProgramOutcome",
    "Question",
    "QuestionOutcome",
    "StudentPaper",
    "TimestampMixin",
    "User",
]
