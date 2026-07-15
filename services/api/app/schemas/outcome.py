from pydantic import BaseModel, ConfigDict, Field, model_validator


class ProgramOutcomeCreate(BaseModel):
    """PÇ — Program Öğrenme Çıktısı. Bölüme aittir; MÜDEK/MEDEK bunu denetler."""

    code: str = Field(min_length=1, max_length=16, examples=["PÇ1"])
    description: str = Field(
        min_length=1, examples=["Karmaşık mühendislik problemlerini çözme becerisi"]
    )


class ProgramOutcomeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    department_id: int
    code: str
    description: str


class CourseOutcomeCreate(BaseModel):
    """DÇ — Ders Öğrenme Çıktısı. Bir veya çok PÇ'yi besler."""

    code: str = Field(min_length=1, max_length=16, examples=["DÇ1"])
    description: str = Field(min_length=1, examples=["Temel döngü yapılarını kullanabilme"])
    program_outcome_ids: list[int] = Field(
        default_factory=list, description="Bu DÇ'nin beslediği PÇ'ler (DÇ–PÇ ilişki matrisi)"
    )


class CourseOutcomeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    course_id: int
    code: str
    description: str
    program_outcomes: list[ProgramOutcomeRead] = Field(default_factory=list)


class OutcomeWeight(BaseModel):
    """Sorunun bir DÇ'ye katkı ağırlığı. OBS'deki `DÇ1(%25)` gösteriminin karşılığı."""

    course_outcome_id: int
    weight_pct: float = Field(gt=0, le=100, examples=[25])


class QuestionOutcomesUpdate(BaseModel):
    """Bir sorunun DÇ bağlantılarını (ağırlıklarıyla) topluca ayarlar.

    OBS kuralı: bir sorunun DÇ ağırlıkları toplamda %100 olmalıdır.
    Bunu burada zorluyoruz — yanlış ağırlıkla kaydedilen bir soru, dönem sonunda
    tüm akreditasyon raporunu bozar ve kimse fark etmez.
    """

    weights: list[OutcomeWeight] = Field(min_length=1)

    @model_validator(mode="after")
    def weights_must_total_100(self):
        total = sum(w.weight_pct for w in self.weights)
        if abs(total - 100.0) > 0.01:
            raise ValueError(
                f"Ders çıktısı ağırlıkları toplamı %{total:.1f}. "
                "OBS kuralı gereği %100 olmalıdır."
            )
        ids = [w.course_outcome_id for w in self.weights]
        if len(ids) != len(set(ids)):
            raise ValueError("Aynı ders çıktısı birden çok kez verilmiş.")
        return self


class QuestionOutcomeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    course_outcome_id: int
    weight_pct: float
