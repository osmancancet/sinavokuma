"""SRS GÖREV 6 + §4 — Chain-of-Thought rubrik puanlama.

SRS §4 aynen şunu istiyor:
  "Önce öğrencinin kodunu analiz et, sonra rubrikteki 1. şarta uyup uymadığını yaz,
   sonra 2. şarta bak ve en son notu ver."

Prompt bu sırayı zorlar. Düşünce zinciri puandan ÖNCE gelir — sonra değil. Model
önce puanı verip sonra gerekçe uydurursa, gerekçe süslemeden ibaret olur.

── ÇIKTI BİÇİMİ: NEDEN JSON DEĞİL ──────────────────────────────────────────

İlk tasarımda çıktıyı JSON olarak istedik. Ölçüm gösterdi ki bu KIRIK:

  Qwen2.5-7B, 4 vakanın 2'sinde geçerli JSON üretemedi. Ama ham çıktıya bakınca
  AKIL YÜRÜTMESİ DOĞRUYDU — hatta 'i < n' hatasını doğru teşhis etmişti:
  "döngü koşulu i < n olarak belirlenmiş, bu da 1'den (n-1)'e kadar toplar..."

  Sorun modelin zekâsı değil, biçimdi: uzun Türkçe gerekçeyi JSON string'ine
  sıkıştırmak kaçış karakteri sorunları yaratıyor ve token limitinde cümle
  ortasında kesilince JSON tamamen geçersiz oluyor. Tek bir kesik tırnak,
  doğru yapılmış tüm değerlendirmeyi çöpe atıyor.

Çözüm: SATIR TABANLI biçim. Kaçış yok, süslü parantez eşleştirme yok, çıktı
kesilse bile okunabilen satırlar okunur. Yerel modellerle bu, JSON'dan çok daha
dayanıklı.
"""

import logging
import re

from langchain_core.prompts import PromptTemplate

from app.grading.schemas import CriterionScore, GradingResult

logger = logging.getLogger(__name__)

GRADING_TEMPLATE = PromptTemplate(
    template="""Sen deneyimli bir üniversite öğretim görevlisisin. Bir öğrencinin
sınav cevabını, verilen rubriğe göre adil biçimde değerlendireceksin.

## SORU
{soru_no}. soru (tam puan: {max_puan})

## BEKLENEN CEVAP
{beklenen_cevap}

## RUBRİK
{rubrik}

## ÖĞRENCİNİN CEVABI (el yazısından okundu)
{ogrenci_cevabi}

## DEĞERLENDİRME KURALLARI

### 1. Puan kırmak için KANIT göstermek zorundasın
Bir kriterden puan kıracaksan, gerekçende ÖĞRENCİNİN CEVABINDAN ilgili satırı
AYNEN ALINTILA:

- Yanlış bir şey yazmışsa: yanlış satırı alıntıla.
  Örn: gerekçe → `for (int i = 1; i < n; i++)` satırında koşul i<n; n hiç toplanmıyor.
- Bir şey EKSİKSE: eksikliğin bulunduğu satırı alıntıla ve neyin eksik olduğunu söyle.
  Eksiklik alıntılanamaz ama eksikliğin OLDUĞU satır alıntılanabilir.
  Örn: gerekçe → `int toplam = 0` satırının sonunda noktalı virgül yok.

İlgili satırı gösteremiyorsan o hata yoktur — puan KIRMA, tam puan ver.

Uydurma hata en tehlikeli davranıştır: öğrenci yazmadığı bir hatadan puan kaybeder
ve bunu asla öğrenemez. Puan kırmadan önce cevabı bir kez daha oku ve iddia ettiğin
hatanın GERÇEKTEN orada olduğunu doğrula. Benzer sorularda sık görülen hatalar bu
cevapta olmayabilir.

### 2. Kriterler BECERİYİ ölçer, yazım biçimini değil
Rubrikteki kriter adı bir şablon değil, ölçülen beceridir. Öğrenci aynı DOĞRU
sonucu FARKLI (hatta daha verimli) bir yolla elde ettiyse o kriterden TAM PUAN alır.

Örnek: "Döngü mantığı" kriteri, "doğru sonucu üreten hesaplama mantığı" demektir.
Öğrenci döngü yerine `toplam = n * (n + 1) / 2` formülünü kullandıysa, sonuç doğru
olduğu için bu kriterden TAM PUAN alır — "döngü yazmamış" gerekçesiyle puan KIRMA.
Matematiksel olarak daha iyi bir çözümü cezalandırmak, öğrenciye yapılan en büyük
haksızlıktır.

Puan yalnızca SONUÇ yanlışsa veya beceri gösterilmemişse kırılır.

### 3. Yüzeysel bakma
- Kod varsa satır satır oku: eksik noktalı virgül, kapanmamış parantez, yanlış
  operatör, yanlış sınır koşulu (i < n ile i <= n aynı şey DEĞİLDİR).
- Sözdizimi kusursuz ama SONUÇ yanlışsa, bu ciddi bir hatadır — mantık kriterinden
  puan kırılır (ama önce kural 1: hatalı satırı alıntıla).
- Akıcı ama soruyu cevaplamayan metne puan verme.
- Kısmen doğru cevaba kısmi puan ver — hep-ya-hiç davranma.
- [okunamadı] işaretli yerler için öğrenciyi cezalandırma; gerekçende belirt.

## ÇIKTI BİÇİMİ

Tam olarak bu biçimde yaz. Başka hiçbir şey yazma. JSON kullanma.

ANALIZ: <öğrencinin cevabını 1-3 cümlede analiz et: ne yapmaya çalışmış, sonuç doğru mu>
{kriter_satirlari}
SONUC: <1-2 cümlede özetle>

Kurallar:
- KRITER satırlarında puan bir sayı olmalı (örn: 7.5).
- Rubrikteki HER kriter için ayrı bir KRITER satırı yaz.
- Puan kırdığın her kriterde, gerekçe içinde hatalı satırı tırnak içinde alıntıla.
- Tam puan verdiğin kriterlerde alıntıya gerek yok.
- Toplamı sen hesaplama — kriter puanlarından hesaplanacak.""",
    input_variables=[
        "soru_no",
        "max_puan",
        "beklenen_cevap",
        "rubrik",
        "ogrenci_cevabi",
        "kriter_satirlari",
    ],
)


def build_prompt(
    question_number: int,
    max_score: float,
    expected_answer: str | None,
    rubric_criteria: list[dict],
    student_text: str,
) -> str:
    criteria = rubric_criteria or []

    rubric_lines = "\n".join(
        f"- {c.get('kriter', '?')}: {c.get('puan', 0)} puan" for c in criteria
    )

    # Modele doldurması gereken satırların iskeletini veriyoruz. Serbest bırakırsak
    # kriter adlarını kendi uydurup rubrikten sapıyor.
    kriter_satirlari = "\n".join(
        f"KRITER: {c.get('kriter', '?')} | PUAN: <0-{c.get('puan', 0)} arası sayı> | "
        f"GEREKCE: <bu kritere neden bu puanı verdin>"
        for c in criteria
    )

    return GRADING_TEMPLATE.format(
        soru_no=question_number,
        max_puan=max_score,
        beklenen_cevap=expected_answer or "(belirtilmemiş)",
        rubrik=rubric_lines or "(rubrik tanımlanmamış — cevabın doğruluğuna göre puanla)",
        ogrenci_cevabi=student_text or "(boş)",
        kriter_satirlari=kriter_satirlari
        or "KRITER: Genel doğruluk | PUAN: <sayı> | GEREKCE: <gerekçe>",
    )


# "KRITER: <ad> | PUAN: <sayı> | GEREKCE: <metin>"
# Model bazen "PUAN: 7.5/10" yazar — bölü işaretinden sonrasını yok sayıyoruz.
CRITERION_LINE = re.compile(
    r"^\s*KRITER\s*:\s*(?P<kriter>[^|]+?)\s*\|\s*"
    r"PUAN\s*:\s*(?P<puan>-?\d+(?:[.,]\d+)?)\s*(?:/\s*[\d.,]+)?\s*\|\s*"
    r"GEREK[CÇ]E\s*:\s*(?P<gerekce>.+?)\s*$",
    re.MULTILINE | re.IGNORECASE,
)
ANALYSIS_LINE = re.compile(r"^\s*ANALIZ\s*:\s*(?P<v>.+?)\s*$", re.MULTILINE | re.IGNORECASE)
SUMMARY_LINE = re.compile(r"^\s*SONUC\s*:\s*(?P<v>.+?)\s*$", re.MULTILINE | re.IGNORECASE)


class GradingParseError(Exception):
    """Model çıktısından hiçbir kriter puanı okunamadı."""


def parse_result(raw_output: str, rubric_criteria: list[dict]) -> GradingResult:
    """Satır tabanlı çıktıyı GradingResult'a çevirir.

    Rubrikteki her kriter için model bir satır yazmalı. Yazmadıysa o kriteri
    0 varsaymıyoruz — bu, hatayı öğrencinin sırtına yıkmak olurdu. Bunun yerine
    hata fırlatıyoruz; worker kağıdı FAILED işaretler ve hoca elle bakar.
    """
    found: dict[str, tuple[float, str]] = {}
    for match in CRITERION_LINE.finditer(raw_output):
        name = match.group("kriter").strip()
        score = float(match.group("puan").replace(",", "."))
        found[name.casefold()] = (score, match.group("gerekce").strip())

    if not found:
        raise GradingParseError(
            "Model çıktısında hiçbir 'KRITER: ... | PUAN: ... | GEREKCE: ...' satırı yok."
        )

    criteria: list[CriterionScore] = []
    missing: list[str] = []
    for c in rubric_criteria:
        name = str(c.get("kriter", "?"))
        max_score = float(c.get("puan", 0))
        hit = found.get(name.casefold())
        if hit is None:
            missing.append(name)
            continue
        score, reason = hit
        criteria.append(
            CriterionScore(
                kriter=name, max_puan=max_score, verilen_puan=score, gerekce=reason
            )
        )

    if missing:
        raise GradingParseError(
            f"Model şu kriterleri değerlendirmedi: {', '.join(missing)}. "
            "Eksik kriteri 0 saymak öğrenciye haksızlık olurdu; kağıt insan incelemesine gidiyor."
        )

    analysis = ANALYSIS_LINE.search(raw_output)
    summary = SUMMARY_LINE.search(raw_output)

    return GradingResult(
        analiz=analysis.group("v").strip() if analysis else "(model analiz yazmadı)",
        kriterler=criteria,
        toplam_puan=sum(c.verilen_puan for c in criteria),
        genel_gerekce=summary.group("v").strip() if summary else "",
    )


def clamp_to_rubric(result: GradingResult, max_score: float) -> GradingResult:
    """Puanı rubriğin sınırlarına ZORLAR.

    LLM'ler aritmetikte hata yapar: 5 puanlık kritere 7 verebilir. Bu sayı
    doğrudan öğrencinin transkriptine gidiyor — sınırı KOD zorlar, modelin iyi
    niyeti değil.
    """
    criteria: list[CriterionScore] = []
    for c in result.kriterler:
        clamped = min(max(c.verilen_puan, 0.0), c.max_puan)
        if clamped != c.verilen_puan:
            logger.warning(
                "Kriter puanı sınır dışıydı, kırpıldı: %s (%s -> %s / %s)",
                c.kriter,
                c.verilen_puan,
                clamped,
                c.max_puan,
            )
        criteria.append(c.model_copy(update={"verilen_puan": clamped}))

    total = min(sum(c.verilen_puan for c in criteria), max_score)
    return result.model_copy(update={"kriterler": criteria, "toplam_puan": total})
