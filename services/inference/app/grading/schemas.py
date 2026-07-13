from pydantic import BaseModel, Field


class CriterionScore(BaseModel):
    """Rubrikteki tek bir kriterin değerlendirmesi."""

    kriter: str
    max_puan: float
    verilen_puan: float = Field(ge=0)
    gerekce: str = Field(description="Bu kritere neden bu puan verildi")


class GradingResult(BaseModel):
    """LangChain zincirinin ürettiği yapılandırılmış çıktı.

    Serbest metin yerine şema zorluyoruz: `ai_score` ve `ai_reasoning` alanlarını
    düzyazıdan regex ile ayıklamaya çalışmak kırılgan olurdu.
    """

    analiz: str = Field(description="Öğrencinin cevabının genel analizi (düşünce zinciri)")
    kriterler: list[CriterionScore]
    toplam_puan: float = Field(ge=0)
    genel_gerekce: str
