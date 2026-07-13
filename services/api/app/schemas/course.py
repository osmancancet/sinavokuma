# `date` alanı sınıf gövdesinde `datetime.date` tipini gölgelediği için takma ad şart.
from datetime import date as Date

from pydantic import BaseModel, ConfigDict, Field

from app.models import ExamStatus


class CourseCreate(BaseModel):
    code: str = Field(min_length=1, max_length=32, examples=["BMG101"])
    name: str = Field(min_length=1, max_length=255)
    department_id: int | None = None


class CourseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str
    department_id: int | None
    teacher_id: int


class MudekOutcomeCreate(BaseModel):
    outcome_code: str = Field(min_length=1, max_length=16, examples=["Ç1"])
    description: str = Field(
        min_length=1, examples=["Karmaşık mühendislik problemlerini çözme becerisi"]
    )


class MudekOutcomeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    course_id: int
    outcome_code: str
    description: str


class ExamCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255, examples=["Vize Sınavı"])
    date: Date | None = None
    total_score: float = Field(default=100, gt=0, le=1000)


class ExamRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    course_id: int
    title: str
    date: Date | None
    total_score: float
    status: ExamStatus


class RubricCriterion(BaseModel):
    """`questions.rubric_criteria` JSONB dizisinin tek bir elemanı."""

    kriter: str = Field(min_length=1, examples=["Döngü mantığı"])
    puan: float = Field(gt=0, examples=[10])


class QuestionCreate(BaseModel):
    question_number: int = Field(ge=1)
    max_score: float = Field(gt=0)
    mudek_outcome_id: int | None = None
    expected_answer: str | None = None
    rubric_criteria: list[RubricCriterion] = Field(default_factory=list)


class QuestionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    exam_id: int
    question_number: int
    max_score: float
    mudek_outcome_id: int | None
    expected_answer: str | None
    rubric_criteria: list[dict]
