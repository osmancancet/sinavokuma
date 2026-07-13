"""SRS GÖREV 6 + §4 — LangChain tabanlı Chain-of-Thought rubrik puanlama.

SRS §4 (Prompting) aynen şunu istiyor:
  "Önce öğrencinin kodunu analiz et, sonra rubrikteki 1. şarta uyup uymadığını yaz,
   sonra 2. şarta bak ve en son notu ver."

Prompt bu sırayı zorluyor. Modelin önce puanı verip sonra gerekçe uydurmasını
engellemek kritik — düşünce zinciri puandan ÖNCE gelmeli, sonra değil.

LangChain'in `PromptTemplate` + `PydanticOutputParser` bileşenlerini kullanıyoruz;
model çağrısı ise kendi motor soyutlamamızdan geçiyor (KVKK: model yerelde çalışır,
LangChain'in dış sağlayıcı entegrasyonları kullanılmaz).
"""

import json
import logging
import re

from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import PromptTemplate

from app.grading.schemas import CriterionScore, GradingResult

logger = logging.getLogger(__name__)

parser = PydanticOutputParser(pydantic_object=GradingResult)

GRADING_TEMPLATE = PromptTemplate(
    template="""Sen deneyimli bir üniversite öğretim görevlisisin. Bir öğrencinin
sınav cevabını, verilen rubriğe göre adil biçimde değerlendireceksin.

## SORU
{soru_no}. soru (tam puan: {max_puan})

## BEKLENEN CEVAP
{beklenen_cevap}

## RUBRİK (değerlendirme anahtarı)
{rubrik}

## ÖĞRENCİNİN CEVABI (el yazısından okundu)
{ogrenci_cevabi}

## NASIL DEĞERLENDİRECEKSİN
Bu sırayı BOZMA:
1. Önce öğrencinin cevabını analiz et. Ne yapmaya çalışmış, mantığı doğru mu?
2. Sonra rubrikteki HER kriteri tek tek ele al. Her biri için:
   - Öğrenci bu kriteri karşılamış mı?
   - Kısmen karşılamışsa kısmi puan ver — hep-ya-hiç davranma.
   - Verdiğin puanın gerekçesini yaz.
3. EN SON toplam puanı hesapla.

Kurallar:
- Toplam puan, kriter puanlarının toplamı olmalı ve {max_puan} puanı GEÇEMEZ.
- Cevap boşsa veya tamamen alakasızsa 0 ver.
- Öğrenci beklenen cevaptan farklı ama DOĞRU bir yol izlemişse tam puan ver.
  Beklenen cevap tek doğru yol değildir.
- El yazısı okuma hatası olabileceğini hesaba kat; [okunamadı] işaretli yerler
  için öğrenciyi cezalandırma, gerekçende belirt.

{format_instructions}""",
    input_variables=[
        "soru_no",
        "max_puan",
        "beklenen_cevap",
        "rubrik",
        "ogrenci_cevabi",
    ],
    partial_variables={"format_instructions": parser.get_format_instructions()},
)


def build_prompt(
    question_number: int,
    max_score: float,
    expected_answer: str | None,
    rubric_criteria: list[dict],
    student_text: str,
) -> str:
    rubric_lines = "\n".join(
        f"- {c.get('kriter', '?')}: {c.get('puan', 0)} puan" for c in rubric_criteria
    )
    return GRADING_TEMPLATE.format(
        soru_no=question_number,
        max_puan=max_score,
        beklenen_cevap=expected_answer or "(belirtilmemiş)",
        rubrik=rubric_lines or "(rubrik tanımlanmamış — cevabın doğruluğuna göre puanla)",
        ogrenci_cevabi=student_text or "(boş)",
    )


def parse_result(raw_output: str) -> GradingResult:
    """Modelin çıktısını GradingResult'a çevirir.

    Yerel modeller JSON'ı ```json bloğu içine sarmayı sever; parser bunu tolere
    etmezse kendimiz ayıklıyoruz.
    """
    try:
        return parser.parse(raw_output)
    except Exception:
        match = re.search(r"\{.*\}", raw_output, re.DOTALL)
        if not match:
            raise
        return GradingResult.model_validate(json.loads(match.group(0)))


def clamp_to_rubric(result: GradingResult, max_score: float) -> GradingResult:
    """Modelin verdiği puanı rubriğin sınırlarına zorlar.

    LLM'ler aritmetikte hata yapar: 20 puanlık soruya 25 verebilir, ya da kriter
    puanları toplamı beyan ettiği toplamı tutmayabilir. Notu doğrudan öğrencinin
    transkriptini etkileyen bir sayı olarak kabul edemeyiz — sınırı KOD zorlar,
    modelin iyi niyeti değil.
    """
    criteria: list[CriterionScore] = []
    for c in result.kriterler:
        verilen = min(max(c.verilen_puan, 0), c.max_puan)
        if verilen != c.verilen_puan:
            logger.warning(
                "Kriter puanı sınır dışıydı, kırpıldı: %s (%s -> %s)",
                c.kriter,
                c.verilen_puan,
                verilen,
            )
        criteria.append(c.model_copy(update={"verilen_puan": verilen}))

    # Toplamı modele değil, kriterlerin gerçek toplamına güveniyoruz.
    total = min(sum(c.verilen_puan for c in criteria), max_score) if criteria else 0.0
    if criteria and abs(total - result.toplam_puan) > 0.01:
        logger.warning(
            "Modelin bildirdiği toplam (%s) kriter toplamıyla (%s) uyuşmadı; "
            "kriter toplamı esas alındı.",
            result.toplam_puan,
            total,
        )

    return result.model_copy(update={"kriterler": criteria, "toplam_puan": total})
