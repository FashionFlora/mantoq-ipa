# arabic_g2p_mega_suite.py
import csv
import re
import unicodedata
from dataclasses import dataclass
from collections import Counter
from pathlib import Path
from typing import List, Dict, Optional

from mantoq.lib.buck.phonetise_buckwalter import arabic_to_buckwalter, process_utterance
from mantoq.lib.buck.ipa import arabic_to_ipa


# ============================================================
# 1. MODEL TEST CASE
# ============================================================

@dataclass(frozen=True)
class TestCase:
    category: str
    text: str


# ============================================================
# 2. STAŁE I ZASOBY
# ============================================================

SUN_LETTERS = set("تثدذرزسشصضطظلن")
CASE_ENDINGS = ["ُ", "َ", "ِ", "ٌ", "ً", "ٍ"]

# Bezpieczne rzeczowniki do masowej kombinatoryki
SAFE_NOUNS = [
    "كِتَاب", "بَيْت", "قَلَم", "وَلَد", "بِنْت", "رَجُل", "طَالِب", "مُدِير",
    "مَسْجِد", "بَاب", "فَصْل", "سُوق", "طَرِيق", "نُور", "حَقّ", "عِلْم",
    "دِين", "صَدِيق", "شَارِع", "مَكْتَب", "غُرْفَة", "قَمَر", "شَمْس",
    "نَجْم", "صَبَاح", "لَيْل", "نَهَار", "قَلْب", "صَوْت", "زَمَن"
]

# Rzeczowniki nadające się dobrze do fraz z AL-
ARTICLE_NOUNS = [
    "شَمْس", "نَاس", "رَجُل", "طَالِب", "صَدِيق", "نُور", "لَيْل", "نَجْم",
    "قَمَر", "بَيْت", "كِتَاب", "مَسْجِد", "بَاب", "فَصْل", "سُوق", "شَارِع",
    "صَبَاح", "نَهَار", "قَلْب", "صَوْت"
]

# Rzeczowniki do dołączania zaimków
ATTACHABLE_NOUNS = [
    "كِتَاب", "بَيْت", "قَلَم", "طَالِب", "مُدِير", "رَجُل", "صَدِيق",
    "طَرِيق", "نُور", "عِلْم", "دِين", "بَاب", "فَصْل", "مَكْتَب", "قَلْب"
]

NOUN_PRONOUNS = ["هُ", "هَا", "هُمْ", "هُنَّ", "كَ", "كِ", "كُمْ", "كُنَّ", "نَا", "ي"]

ADJECTIVES = [
    "كَبِير", "صَغِير", "جَدِيد", "قَدِيم", "جَمِيل", "صَعْب", "مُهِمّ",
    "خَطِير", "وَاضِح", "قَرِيب", "بَعِيد", "سَرِيع", "بَطِيء", "طَوِيل",
    "قَصِير", "قَوِيّ", "ضَعِيف", "مُمْتَاز", "مَفْتُوح", "مُغْلَق"
]

PREPOSITIONS = ["فِي", "مِنْ", "إِلَى", "عَلَى", "عَنْ", "مَعَ"]

# Czasowniki "bezpieczne" do masowych kombinacji z zaimkami
SAFE_VERBS_PERF = [
    "كَتَبَ", "قَرَأَ", "سَمِعَ", "دَخَلَ", "خَرَجَ",
    "فَتَحَ", "غَسَلَ", "عَلَّمَ", "دَرَّسَ", "اِسْتَخْدَمَ"
]

SAFE_VERBS_IMPF = [
    "يَكْتُبُ", "يَقْرَأُ", "يَسْمَعُ", "يَدْخُلُ", "يَخْرُجُ",
    "يَفْتَحُ", "يَغْسِلُ", "يُعَلِّمُ", "يُدَرِّسُ", "يَسْتَخْدِمُ"
]

SAFE_VERBS_IMPV = [
    "اُكْتُبْ", "اِقْرَأْ", "اِسْمَعْ", "اُدْخُلْ", "اُخْرُجْ",
    "اِفْتَحْ", "اِغْسِلْ", "عَلِّمْ", "دَرِّسْ", "اِسْتَخْدِمْ"
]

VERB_OBJECT_PRONOUNS = ["هُ", "هَا", "هُمْ", "هُنَّ", "كَ", "كِ", "كُمْ", "كُنَّ", "نِي", "نَا"]

SUBJECTS = [
    "رَجُل", "طَالِب", "مُدِير", "صَدِيق", "وَلَد", "بِنْت",
    "شَمْس", "قَمَر", "بَيْت", "كِتَاب", "مَسْجِد", "شَارِع"
]

OBJECTS = [
    "كِتَاب", "بَيْت", "قَلَم", "بَاب", "فَصْل", "طَرِيق",
    "نُور", "صَوْت", "قَلْب", "مَكْتَب", "شَارِع", "مَسْجِد"
]


# ============================================================
# 3. STATYCZNE EDGE CASES
# ============================================================

STATIC_CASES: Dict[str, List[str]] = {
    "silent_letters": [
        "كَتَبُوا", "يَسْمَعُوا", "لَمْ يَدْعُوا", "مِائَةٌ", "مِائَتَانِ",
        "أُولَئِكَ", "أُولُو", "أُولِي", "عَمْرًا", "عَمْرٍو", "عَمْرٌو"
    ],
    "hidden_alif_khanjariyya": [
        "هَذَا", "هَذِهِ", "هَذَانِ", "هَؤُلَاءِ", "ذَلِكَ", "كَذَلِكَ",
        "اللَّهُ", "اللَّهُمَّ", "إِلَهٌ", "الرَّحْمَنُ", "لَكِنْ", "لَكِنَّ",
        "طَهَ", "إِسْحَاقُ"
    ],
    "hamza_extreme": [
        "يَسْتَأْذِنُ", "مَسْئُولِيَّةٌ", "شُئُونٌ", "رُؤَسَاءُ", "تَبَاطُؤٌ",
        "تَبَاطُؤًا", "شَيْءٌ", "شَيْئًا", "شَيْءٍ", "دِفْءٌ", "دِفْئًا",
        "مُتَلَأْلِئٌ", "قُرِئَ", "بِيئَةٌ", "هَيْئَةٌ", "سَوْءَةٌ",
        "مُؤَامَرَةٌ", "رُؤْيَا", "اِقْرَأْ", "مَبْدَأٌ", "مَلْجَأٌ", "سُؤَالٌ"
    ],
    "sun_letter_assimilation": [
        "وَبِالشَّمْسِ", "فَكَالنَّجْمِ", "لِلرَّجُلِ", "لِلَّذِينَ", "فَلِلَّهِ",
        "بِالضَّبْطِ", "كَالطَّائِرِ", "وَالظِّلِّ", "فِي السَّيَّارَةِ", "مِنَ النَّاسِ"
    ],
    "long_quranic_morphology": [
        "فَأَسْقَيْنَاكُمُوهُ", "أَنُلْزِمُكُمُوهَا", "فَسَيَكْفِيكَهُمُ",
        "وَاسْتَخْلَفْنَاهُمْ", "فَلَيَسْتَخْلِفَنَّهُمْ", "وَالْمُسْتَضْعَفِينَ",
        "اِسْتِقْلَالِيَّتُهُمْ", "أَفَإِنْ"
    ],
    "taa_marbuta_vs_haa": [
        "مَدْرَسَةٌ", "مَدْرَسَتُهُ", "حَيَاةٌ", "مِيَاهٌ", "وَجْهٌ", "تَوْجِيهٌ",
        "فَاطِمَةُ", "قُضَاةٌ", "صَلَاةٌ", "زَكَاةٌ", "مِشْكَاةٌ",
        "شَجَرَةٌ", "شَجَرَتُهَا", "سَيَّارَةٌ", "سَيَّارَتُهُمْ"
    ],
    "alif_maqsura_and_tanween": [
        "فَتًى", "هُدًى", "مُسْتَشْفًى", "مُصْطَفًى", "مُحَامٍ", "قَاضٍ", "غَازٍ",
        "عَصًا", "رِضًا", "مَقْهًى", "دُعَاءً", "سَمَاءً"
    ],
    "shadda_and_vowel_interaction": [
        "مُدَرِّسٌ", "مُدَرَّسٌ", "مُسْتَقِرٌّ", "مُسْتَقَرٌّ", "أُمِّيٌّ", "عَرَبِيٌّ",
        "يُوَجِّهُونَهُ", "الطَّامَّةُ", "الصَّاخَّةُ", "مَادَّةٌ", "حَادَّةٌ"
    ],
    "loanwords": [
        "دِيمُوقْرَاطِيَّةٌ", "إِسْتِرَاتِيجِيَّةٌ", "تِكْنُولُوجِيَا", "كُومْبْيُوتَر",
        "بَلَاسْتِيك", "فِيرُوسَات", "مِيكْرُوفُون", "أُكْسُجِين", "سِينِيمَائِيٌّ"
    ],
    "hamzat_wasl": [
        "وَابْنُ", "فَاسْتَغْفَرَ", "بِاسْمِ", "بِسْمِ", "وَامْرَأَةٌ", "يَا ابْنَ",
        "اِقْرَأْ وَاسْتَمِعْ", "اَلْحَمْدُ لِلَّهِ", "مِنَ الْمَاءِ", "أَبُو الْفَضْلِ"
    ],
    "weak_verbs_exceptions": [
        "قَالَ", "يَقُولُ", "قُلْ", "بَاعَ", "يَبِيعُ", "بِعْ",
        "دَعَا", "يَدْعُو", "اُدْعُ", "رَمَى", "يَرْمِي", "اِرْمِ",
        "رَأَى", "يَرَى"
    ],
    "boundary_phrases": [
        "فِي الْبَيْتِ", "مِنَ الْقَمَرِ", "عَلَى الطَّرِيقِ", "إِلَى الْمَسْجِدِ",
        "وَالشَّمْسُ", "فَالنَّجْمُ", "بِالرَّجُلِ", "كَالصَّوْتِ"
    ]
}


# ============================================================
# 4. FUNKCJE POMOCNICZE
# ============================================================

def normalize_arabic_text(text: str) -> str:
    text = unicodedata.normalize("NFC", text.strip())
    text = re.sub(r"\s+", " ", text)
    # Usuwamy tylko identyczne, wielokrotne znaki diakrytyczne obok siebie
    text = re.sub(r"([\u064B-\u0652\u0670])\1+", r"\1", text)
    return text


def normalize_ipa(ipa: str) -> str:
    ipa = ipa.strip()
    ipa = ipa.replace("ˈ", "").replace("ˌ", "")
    ipa = re.sub(r"\s+", "", ipa)
    return ipa


def ordered_unique(cases: List[TestCase]) -> List[TestCase]:
    seen = set()
    out = []
    for case in cases:
        txt = normalize_arabic_text(case.text)
        if txt not in seen:
            seen.add(txt)
            out.append(TestCase(case.category, txt))
    return out


def with_definite_article(word: str, proclitic: str = "") -> str:
    """
    Zwraca formę z rodzajnikiem 'ال', uwzględniając asymilację liter słonecznych.
    Przykłady:
      شَمْس -> الشَّمْس
      قَمَر -> الْقَمَر
      proclitic='وَ' + شَمْس -> وَالشَّمْس
    """
    first = word[0]
    if first in SUN_LETTERS:
        return f"{proclitic}ال{first}ّ{word[1:]}"
    return f"{proclitic}الْ{word}"


def with_li_article(word: str) -> str:
    """
    Obsługa لِ + ال = لِلْ / لِلّ...
    """
    first = word[0]
    if first in SUN_LETTERS:
        return f"لِل{first}ّ{word[1:]}"
    return f"لِلْ{word}"


def load_gold_tsv(path: Optional[str]) -> Dict[str, str]:
    gold = {}
    if not path:
        return gold

    p = Path(path)
    if not p.exists():
        print(f"UWAGA: gold file nie istnieje: {path}")
        return gold

    with p.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            line = line.rstrip("\n")
            if not line or line.startswith("#"):
                continue
            parts = line.split("\t")
            if len(parts) < 2:
                print(f"Pomijam błędny wiersz gold [{line_no}]: {line}")
                continue
            text = normalize_arabic_text(parts[0])
            ipa = parts[1].strip()
            gold[text] = ipa
    return gold


# ============================================================
# 5. GENERATORY DYNAMICZNE
# ============================================================

def gen_static_cases() -> List[TestCase]:
    cases = []
    for category, items in STATIC_CASES.items():
        for item in items:
            cases.append(TestCase(category, item))
    return cases


def gen_case_endings() -> List[TestCase]:
    cases = []
    for noun in SAFE_NOUNS:
        for ending in CASE_ENDINGS:
            cases.append(TestCase("case_endings", noun + ending))
    return cases


def gen_article_forms() -> List[TestCase]:
    cases = []

    # Formy bazowe z AL-
    for noun in ARTICLE_NOUNS:
        cases.append(TestCase("article_nominative", with_definite_article(noun) + "ُ"))
        cases.append(TestCase("article_accusative", with_definite_article(noun) + "َ"))
        cases.append(TestCase("article_genitive", with_definite_article(noun) + "ِ"))

    # Proklityki
    for noun in ARTICLE_NOUNS:
        cases.append(TestCase("article_with_wa", with_definite_article(noun, "وَ") + "ُ"))
        cases.append(TestCase("article_with_fa", with_definite_article(noun, "فَ") + "ُ"))
        cases.append(TestCase("article_with_bi", with_definite_article(noun, "بِ") + "ِ"))
        cases.append(TestCase("article_with_ka", with_definite_article(noun, "كَ") + "ِ"))
        cases.append(TestCase("article_with_li", with_li_article(noun) + "ِ"))
        cases.append(TestCase("article_with_wabi", with_definite_article(noun, "وَبِ") + "ِ"))
        cases.append(TestCase("article_with_fabi", with_definite_article(noun, "فَبِ") + "ِ"))

    return cases


def gen_noun_pronoun_forms() -> List[TestCase]:
    cases = []
    for noun in ATTACHABLE_NOUNS:
        for pron in NOUN_PRONOUNS:
            cases.append(TestCase("noun_with_pronoun", noun + pron))
    return cases


def gen_verb_pronoun_forms() -> List[TestCase]:
    cases = []
    for verb in SAFE_VERBS_PERF:
        for pron in VERB_OBJECT_PRONOUNS:
            cases.append(TestCase("perfect_with_object_pronoun", verb + pron))

    for verb in SAFE_VERBS_IMPF:
        for pron in VERB_OBJECT_PRONOUNS:
            cases.append(TestCase("imperfect_with_object_pronoun", verb + pron))

    for verb in SAFE_VERBS_IMPV:
        for pron in VERB_OBJECT_PRONOUNS:
            cases.append(TestCase("imperative_with_object_pronoun", verb + pron))

    return cases


def gen_preposition_phrases() -> List[TestCase]:
    cases = []

    # Typowe frazy przyimkowe
    for prep in PREPOSITIONS:
        for noun in ARTICLE_NOUNS:
            cases.append(TestCase("prepositional_phrase", f"{prep} {with_definite_article(noun)}ِ"))

    # Dodatkowe zbitki graniczne
    for noun in ARTICLE_NOUNS:
        cases.append(TestCase("boundary_min_al", f"مِنَ {with_definite_article(noun)}ِ"))
        cases.append(TestCase("boundary_fi_al", f"فِي {with_definite_article(noun)}ِ"))
        cases.append(TestCase("boundary_ila_al", f"إِلَى {with_definite_article(noun)}ِ"))

    return cases


def gen_idafa_phrases() -> List[TestCase]:
    cases = []
    for head in SAFE_NOUNS:
        for dep in ARTICLE_NOUNS:
            cases.append(TestCase("idafa", f"{head}ُ {with_definite_article(dep)}ِ"))
    return cases


def gen_nominal_phrases() -> List[TestCase]:
    cases = []

    # Indefinite noun + adjective
    for noun in SAFE_NOUNS:
        for adj in ADJECTIVES:
            cases.append(TestCase("nominal_indefinite", f"{noun}ٌ {adj}ٌ"))

    # Definite noun + adjective
    for noun in SAFE_NOUNS:
        for adj in ADJECTIVES:
            cases.append(TestCase("nominal_definite", f"{with_definite_article(noun)}ُ {with_definite_article(adj)}ُ"))

    # Przyimkowe + przymiotnik
    for noun in SAFE_NOUNS:
        for adj in ADJECTIVES[:10]:
            cases.append(TestCase("prepositional_nominal_phrase", f"فِي {with_definite_article(noun)}ِ {with_definite_article(adj)}ِ"))

    return cases


def gen_verbal_sentences() -> List[TestCase]:
    cases = []

    # Zdania z imperfect
    for subj in SUBJECTS:
        subj_def = with_definite_article(subj) + "ُ"
        for verb in SAFE_VERBS_IMPF:
            for obj in OBJECTS:
                obj_def = with_definite_article(obj) + "َ"
                cases.append(TestCase("verbal_sentence_imperfect", f"{subj_def} {verb} {obj_def}"))

    # Zdania z perfect
    for subj in SUBJECTS:
        subj_def = with_definite_article(subj) + "ُ"
        for verb in SAFE_VERBS_PERF:
            for obj in OBJECTS:
                obj_def = with_definite_article(obj) + "َ"
                cases.append(TestCase("verbal_sentence_perfect", f"{subj_def} {verb} {obj_def}"))

    # Krótsze rozkazy
    for verb in SAFE_VERBS_IMPV:
        for obj in OBJECTS:
            obj_def = with_definite_article(obj) + "َ"
            cases.append(TestCase("imperative_phrase", f"{verb} {obj_def}"))

    return cases


def gen_misc_phrase_patterns() -> List[TestCase]:
    cases = []

    # Spójniki + rzeczowniki z AL-
    for noun in ARTICLE_NOUNS:
        cases.append(TestCase("conjunction_patterns", f"وَ{with_definite_article(noun)}ُ"))
        cases.append(TestCase("conjunction_patterns", f"فَ{with_definite_article(noun)}ُ"))

    # Czasownik + fraza przyimkowa
    for verb in SAFE_VERBS_IMPF:
        for noun in ARTICLE_NOUNS[:10]:
            cases.append(TestCase("verb_plus_prep_phrase", f"{verb} فِي {with_definite_article(noun)}ِ"))
            cases.append(TestCase("verb_plus_prep_phrase", f"{verb} مِنَ {with_definite_article(noun)}ِ"))

    return cases


def build_test_suite() -> List[TestCase]:
    all_cases = []
    all_cases.extend(gen_static_cases())
    all_cases.extend(gen_case_endings())
    all_cases.extend(gen_article_forms())
    all_cases.extend(gen_noun_pronoun_forms())
    all_cases.extend(gen_verb_pronoun_forms())
    all_cases.extend(gen_preposition_phrases())
    all_cases.extend(gen_idafa_phrases())
    all_cases.extend(gen_nominal_phrases())
    all_cases.extend(gen_verbal_sentences())
    all_cases.extend(gen_misc_phrase_patterns())

    return ordered_unique(all_cases)


# ============================================================
# 6. URUCHOMIENIE TESTU
# ============================================================

def run_tests(output_dir: str = "arabic_g2p_mega_results", gold_tsv: Optional[str] = None):
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    csv_path = output_path / "results.csv"
    summary_path = output_path / "summary.txt"

    gold = load_gold_tsv(gold_tsv)
    cases = build_test_suite()

    total = len(cases)
    print("=" * 90)
    print("ARABIC G2P MEGA SUITE")
    print(f"Liczba testów: {total}")
    print(f"Gold set załadowany: {'TAK' if gold else 'NIE'}")
    print("=" * 90)

    passed = 0
    failed = 0

    gold_total = 0
    gold_exact = 0
    gold_normalized = 0

    by_category_total = Counter()
    by_category_pass = Counter()
    by_category_fail = Counter()

    pairs_path = output_path / "arabic_ipa_pairs.txt"

    with csv_path.open("w", encoding="utf-8", newline="") as f_csv, \
         pairs_path.open("w", encoding="utf-8") as f_pairs:
        writer = csv.writer(f_csv)
        writer.writerow([
            "id", "category", "text",
            "buckwalter", "phonemes", "ipa",
            "gold_ipa", "exact_match", "normalized_match",
            "status", "error"
        ])

        for i, case in enumerate(cases, 1):
            by_category_total[case.category] += 1
            text = normalize_arabic_text(case.text)

            try:
                buckw_raw = arabic_to_buckwalter(text)
                mantoq_phonemes = process_utterance(buckw_raw)
                ipa_pred = arabic_to_ipa(text, space_separated=False)

                if not buckw_raw:
                    raise ValueError("arabic_to_buckwalter zwrócił pusty wynik")
                if not mantoq_phonemes:
                    raise ValueError("process_utterance zwrócił pusty wynik")
                if not ipa_pred:
                    raise ValueError("arabic_to_ipa zwrócił pusty wynik")

                gold_ipa = gold.get(text, "")
                exact_match = ""
                normalized_match = ""

                if gold_ipa:
                    gold_total += 1
                    exact_match = int(ipa_pred == gold_ipa)
                    normalized_match = int(normalize_ipa(ipa_pred) == normalize_ipa(gold_ipa))
                    gold_exact += exact_match
                    gold_normalized += normalized_match

                writer.writerow([
                    i, case.category, text,
                    buckw_raw, mantoq_phonemes, ipa_pred,
                    gold_ipa, exact_match, normalized_match,
                    "PASS", ""
                ])

                # JUST PRINT IPA AS REQUESTED
                # print(ipa_pred)
                f_pairs.write(f"{text} : {ipa_pred}\n")

                passed += 1
                by_category_pass[case.category] += 1

            except Exception as e:
                failed += 1
                by_category_fail[case.category] += 1

                writer.writerow([
                    i, case.category, text,
                    "", "", "",
                    "", "", "",
                    "FAIL", str(e)
                ])

                print(f"BŁĄD [{i:05d}/{total}] {case.category} | {text} | {e}")

            if i % 500 == 0:
                pass # print(f"Postęp: {i}/{total}")

    with summary_path.open("w", encoding="utf-8") as f_sum:
        f_sum.write("=== ARABIC G2P MEGA SUITE SUMMARY ===\n")
        f_sum.write(f"Łączna liczba testów: {total}\n")
        f_sum.write(f"PASS: {passed}\n")
        f_sum.write(f"FAIL: {failed}\n")
        f_sum.write(f"Smoke pass rate: {(passed / total * 100):.2f}%\n\n")

        if gold_total > 0:
            f_sum.write("=== GOLD EVALUATION ===\n")
            f_sum.write(f"Liczba przypadków z referencją: {gold_total}\n")
            f_sum.write(f"Exact IPA match: {gold_exact}/{gold_total} = {(gold_exact / gold_total * 100):.2f}%\n")
            f_sum.write(
                f"Normalized IPA match: {gold_normalized}/{gold_total} = {(gold_normalized / gold_total * 100):.2f}%\n\n"
            )
        else:
            f_sum.write("=== GOLD EVALUATION ===\n")
            f_sum.write("Brak gold setu. Ten bieg mierzy coverage / crash-rate, a nie realną accuracy.\n\n")

        f_sum.write("=== CATEGORY BREAKDOWN ===\n")
        for cat in sorted(by_category_total.keys()):
            cat_total = by_category_total[cat]
            cat_pass = by_category_pass[cat]
            cat_fail = by_category_fail[cat]
            rate = (cat_pass / cat_total * 100) if cat_total else 0.0
            f_sum.write(f"{cat}: total={cat_total}, pass={cat_pass}, fail={cat_fail}, pass_rate={rate:.2f}%\n")

    print("=" * 90)
    print("ZAKOŃCZONO")
    print(f"Wyniki CSV: {csv_path}")
    print(f"Podsumowanie: {summary_path}")
    print(f"PASS: {passed}/{total}")
    print(f"FAIL: {failed}/{total}")
    if gold_total > 0:
        print(f"Exact IPA match: {gold_exact}/{gold_total} = {(gold_exact / gold_total * 100):.2f}%")
        print(f"Normalized IPA match: {gold_normalized}/{gold_total} = {(gold_normalized / gold_total * 100):.2f}%")
    else:
        print("Brak gold setu -> to był test coverage/stability, nie accuracy.")
    print("=" * 90)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Arabic G2P Mega Suite")
    parser.add_argument("--output-dir", default="arabic_g2p_mega_results", help="Folder wynikowy")
    parser.add_argument("--gold-tsv", default=None, help="TSV: <arabic_text>\\t<gold_ipa>")
    args = parser.parse_args()

    run_tests(output_dir=args.output_dir, gold_tsv=args.gold_tsv)