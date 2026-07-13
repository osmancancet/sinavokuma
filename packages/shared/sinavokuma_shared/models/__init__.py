"""SRS §2 — Core Schema.

Tablolar SRS'teki tanımı birebir izler. Tek ekleme: `departments`. SRS
`courses.department_id` alanını istiyor ama tabloyu tanımlamamış; foreign key'in
bir hedefi olması için ekledik.
"""

from sinavokuma_shared.models.base import Base, TimestampMixin
from sinavokuma_shared.models.course import Course, Department, MudekOutcome
from sinavokuma_shared.models.exam import Exam, Question
from sinavokuma_shared.models.paper import PaperScore, StudentPaper
from sinavokuma_shared.models.user import User

__all__ = [
    "Base",
    "Course",
    "Department",
    "Exam",
    "MudekOutcome",
    "PaperScore",
    "Question",
    "StudentPaper",
    "TimestampMixin",
    "User",
]
