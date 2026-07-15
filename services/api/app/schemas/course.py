# `date` alanı sınıf gövdesinde `datetime.date` tipini gölgelediği için takma ad şart.
from datetime import date as Date

from pydantic import BaseModel, ConfigDict, Field
from sinavokuma_shared import ExamStatus


class DepartmentCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255, examples=["Bilgisayar Programcılığı"])
    faculty: str | None = Field(default=None, examples=["Meslek Yüksekokulu"])


class DepartmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    faculty: str | None


class CourseCreate(BaseModel):
    code: str = Field(min_length=1, max_length=32, examples=["BVA1108"])
    name: str = Field(min_length=1, max_length=255, examples=["Bilgi Teknolojileri"])
    department_id: int | None = None


class CourseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str
    department_id: int | None
    teacher_id: int


class ExamCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255, examples=["Bütünleme"])
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
    # OBS: "Soru Puan" = sınav içi etki oranı. Sınavdaki soruların toplamı %100 olmalı.
    max_score: float = Field(gt=0, le=100, examples=[50])
    prompt: str | None = Field(default=None, description="Sorunun metni")
    expected_answer: str | None = None
    rubric_criteria: list[RubricCriterion] = Field(default_factory=list)


class QuestionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    exam_id: int
    question_number: int
    max_score: float
    prompt: str | None
    expected_answer: str | None
    rubric_criteria: list[dict]
