"""Puanlayıcı değerlendirme seti (SRS §4 — "ground truth ile test").

Her vaka için beklenen puan ARALIĞI var, tek bir sayı değil. Çünkü iki insan
öğretim görevlisi de aynı kağıda tam olarak aynı puanı vermez; ölçmek istediğimiz
şey modelin makul aralıkta kalıp kalmadığı.

Vakalar bilinçli seçildi. Her biri farklı bir başarısızlık türünü yakalar:

  perfect        — tam puan verebiliyor mu?
  syntax_error   — küçük hatayı KISMİ puanla cezalandırıyor mu, yoksa hep-ya-hiç mi?
  wrong_logic    — YANLIŞ algoritmayı yakalıyor mu? (3B bunu 20/20 vermişti!)
  empty          — boş cevaba 0 veriyor mu?
  off_topic      — alakasız ama akıcı metne kanıyor mu?
  different_ok   — DOĞRU ama farklı yöntemi cezalandırıyor mu? (cezalandırırsa
                   öğrenciye haksızlık eder — SRS'in "tek doğru yol yoktur" ilkesi)
  partial_effort — yarım bırakılmış cevaba kısmi puan veriyor mu?
"""

from dataclasses import dataclass

MAX_SCORE = 20.0
EXPECTED_ANSWER = "1'den n'e kadar olan sayıların toplamını bulan bir döngü yazın."
RUBRIC = [
    {"kriter": "Değişken tanımlamaları", "puan": 5},
    {"kriter": "Döngü mantığı", "puan": 10},
    {"kriter": "Sözdizimi hatasızlığı", "puan": 5},
]


@dataclass
class Case:
    key: str
    label: str
    answer: str
    lo: float  # kabul edilebilir en düşük puan
    hi: float  # kabul edilebilir en yüksek puan
    why: str


CASES: list[Case] = [
    Case(
        key="perfect",
        label="Kusursuz",
        answer=(
            "int toplam = 0;\n"
            "for (int i = 1; i <= n; i++) {\n"
            "    toplam = toplam + i;\n"
            "}\n"
            'printf("%d", toplam);'
        ),
        lo=18,
        hi=20,
        why="Her kriter karşılanmış. Tam veya tama yakın puan almalı.",
    ),
    Case(
        key="different_ok",
        label="Doğru ama farklı yöntem (Gauss formülü)",
        answer=("int toplam = n * (n + 1) / 2;\n" 'printf("%d", toplam);'),
        lo=14,
        hi=20,
        why=(
            "Döngü kullanmamış ama SONUÇ DOĞRU ve daha verimli. Rubrikte 'döngü' geçse "
            "de, doğru çözümü cezalandırmak öğrenciye haksızlıktır. Düşük puan verirse "
            "model fazla katı demektir."
        ),
    ),
    Case(
        key="syntax_error",
        label="Doğru mantık, noktalı virgüller eksik",
        answer=(
            "int toplam = 0\n"
            "for (int i = 1; i <= n; i++) {\n"
            "    toplam = toplam + i\n"
            "}\n"
            'printf("%d", toplam)'
        ),
        lo=12,
        hi=17,
        why="Değişken + döngü tam (15 puan), sözdiziminden kırılmalı. Sıfır vermemeli.",
    ),
    Case(
        key="partial_effort",
        label="Yarım bırakılmış (döngü açılmış, gövde boş)",
        answer=("int toplam = 0;\n" "for (int i = 1; i <= n; i++) {\n" "    \n" "}"),
        lo=4,
        hi=10,
        why="Değişken doğru, döngü iskeleti var ama toplama yok. Kısmi puan hak ediyor.",
    ),
    Case(
        key="wrong_logic",
        label="Döngü mantığı YANLIŞ (i < n — son sayıyı atlıyor)",
        answer=(
            "int toplam = 0;\n"
            "for (int i = 1; i < n; i++) {\n"
            "    toplam = toplam + i;\n"
            "}\n"
            'printf("%d", toplam);'
        ),
        lo=6,
        hi=14,
        why=(
            "Sözdizimi kusursuz ama ALGORİTMA YANLIŞ — n'i toplama katmıyor. "
            "Döngü mantığı kriterinden ciddi puan kırılmalı. 3B bu vakaya 20/20 verdi."
        ),
    ),
    Case(
        key="off_topic",
        label="Akıcı ama tamamen alakasız",
        answer=(
            "Döngüler programlamanın temel yapı taşlarındandır. C dilinde for, while "
            "ve do-while olmak üzere üç tür döngü bulunur. Bunlar tekrarlı işlemleri "
            "kolaylaştırır ve kodun okunabilirliğini artırır."
        ),
        lo=0,
        hi=4,
        why=(
            "Doğru bilgiler içeriyor ama SORUYU CEVAPLAMIYOR. Model akıcı metne kanıp "
            "puan verirse, ezber yapan öğrenci kazanır."
        ),
    ),
    Case(
        key="empty",
        label="Boş / cevaplanmamış",
        answer="Bu soruyu cevaplayamadım.",
        lo=0,
        hi=1,
        why="Sıfır olmalı. Sıfırdan büyük veriyorsa model her kağıda puan dağıtıyor.",
    ),
]
