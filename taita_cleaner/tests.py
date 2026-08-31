"""
Test suite for taita_cleaner. Run with:

    python -m unittest taita_cleaner.tests -v
"""
import unittest

from .analyzer import TaitaAnalyzer
from .cleaner import TaitaCleaner
from .utils import (
    clean_markers,
    extract_words,
    get_word_frequencies,
    is_valid_taita_word,
    match_case,
    normalize_apostrophes,
    normalize_unicode,
)


class TestApostropheRule(unittest.TestCase):
    def test_ngprime_is_kept(self):
        self.assertEqual(normalize_apostrophes("ng'ombe"), "ng'ombe")
        self.assertEqual(normalize_apostrophes("ng'ondi"), "ng'ondi")
        self.assertEqual(normalize_apostrophes("kaung'a"), "kaung'a")

    def test_word_initial_w_is_dropped(self):
        self.assertEqual(normalize_apostrophes("w'andu"), "wandu")
        self.assertEqual(normalize_apostrophes("w'a"), "wa")
        self.assertEqual(normalize_apostrophes("w'ana"), "wana")

    def test_root_internal_w_is_dropped(self):
        self.assertEqual(normalize_apostrophes("nguw'o"), "nguwo")
        self.assertEqual(normalize_apostrophes("daw'ida"), "dawida")
        self.assertEqual(normalize_apostrophes("mariw'a"), "mariwa")

    def test_m_apostrophe_is_dropped(self):
        self.assertEqual(normalize_apostrophes("m'ndu"), "mndu")
        self.assertEqual(normalize_apostrophes("m'baa"), "mbaa")

    def test_scattered_typo_apostrophes_are_dropped(self):
        self.assertEqual(normalize_apostrophes("wu'ghoma"), "wughoma")
        self.assertEqual(normalize_apostrophes("kidawi'da"), "kidawida")

    def test_ngprime_survives_alongside_other_apostrophes(self):
        # w' dropped, ng' kept, in the same word
        self.assertEqual(normalize_apostrophes("w'ung'ara"), "wung'ara")

    def test_word_with_no_apostrophe_is_unchanged(self):
        self.assertEqual(normalize_apostrophes("mundu"), "mundu")


class TestCleaner(unittest.TestCase):
    def setUp(self):
        self.cleaner = TaitaCleaner()

    def test_confirmed_correction_applied(self):
        corrected, source = self.cleaner.correct_word("mndu")
        self.assertEqual(corrected, "mundu")
        self.assertEqual(source, "confirmed_correction")

    def test_apostrophe_rule_applied_when_no_further_correction(self):
        corrected, source = self.cleaner.correct_word("w'andu")
        self.assertEqual(corrected, "wandu")
        self.assertEqual(source, "apostrophe_rule")

    def test_ngprime_word_untouched(self):
        corrected, source = self.cleaner.correct_word("ng'ombe")
        self.assertEqual(corrected, "ng'ombe")
        self.assertIsNone(source)

    def test_ambiguous_word_untouched(self):
        corrected, source = self.cleaner.correct_word("mana")
        self.assertEqual(corrected, "mana")
        self.assertIsNone(source)

    def test_distinct_words_untouched(self):
        for w in ("kwa", "lwa", "gha", "ghwa", "koshi", "kosi"):
            corrected, source = self.cleaner.correct_word(w)
            self.assertEqual(corrected, w)
            self.assertIsNone(source)

    def test_case_preserved_title(self):
        corrected, _ = self.cleaner.correct_word("Mndu")
        self.assertEqual(corrected, "Mundu")

    def test_case_preserved_upper(self):
        corrected, _ = self.cleaner.correct_word("MNDU")
        self.assertEqual(corrected, "MUNDU")

    def test_correct_text_and_changelog(self):
        text = "Kila mndu wawehitaji rafiki wa loli"
        corrected, changes = self.cleaner.correct_text(text)
        self.assertIn("mundu", corrected)
        self.assertEqual(len(changes), 1)
        self.assertEqual(changes[0]["original"], "mndu")
        self.assertEqual(changes[0]["corrected"], "mundu")

    def test_process_texts_stats(self):
        texts = ["Kila mndu wawehitaji", "W'andu w'iboilwagha", "Nothing to fix here"]
        corrected, changes, stats = self.cleaner.process_texts(texts)
        self.assertEqual(stats["rows_processed"], 3)
        self.assertEqual(stats["rows_modified"], 2)
        self.assertGreaterEqual(stats["total_corrections"], 2)

    def test_custom_corrections(self):
        cleaner = TaitaCleaner()
        cleaner.add_custom_corrections({"foo": "bar"})
        corrected, _ = cleaner.correct_word("foo")
        self.assertEqual(corrected, "bar")

    def test_export_correction_map(self):
        exported = self.cleaner.export_correction_map()
        self.assertIn({"wrong": "mndu", "right": "mundu"}, exported)


class TestUtils(unittest.TestCase):
    def test_extract_words(self):
        self.assertEqual(extract_words("Mundu ni ng'ombe!"), ["mundu", "ni", "ng'ombe"])

    def test_get_word_frequencies(self):
        freq = get_word_frequencies(["a", "b", "a", "c", "a"])
        self.assertEqual(freq["a"], 3)
        self.assertEqual(freq["b"], 1)

    def test_clean_markers(self):
        self.assertEqual(clean_markers("Hello [Pause] world [cs]"), "Hello  world ")

    def test_normalize_unicode_fixes_typographic_chars(self):
        self.assertEqual(normalize_unicode("kubung’a"), "kubung'a")
        self.assertEqual(normalize_unicode("a\xa0b"), "a b")

    def test_is_valid_taita_word(self):
        self.assertTrue(is_valid_taita_word("ng'ombe"))
        self.assertFalse(is_valid_taita_word("hello123"))
        self.assertFalse(is_valid_taita_word(""))

    def test_match_case(self):
        self.assertEqual(match_case("Mndu", "mundu"), "Mundu")
        self.assertEqual(match_case("MNDU", "mundu"), "MUNDU")
        self.assertEqual(match_case("mndu", "mundu"), "mundu")


class TestAnalyzer(unittest.TestCase):
    def test_excludes_confirmed_distinct_pairs(self):
        texts = ["kwa mundu", "lwa mundu"] * 5  # kwa/lwa both frequent
        analyzer = TaitaAnalyzer(texts)
        candidates = analyzer.find_edit_distance_candidates(min_freq=2, min_pair_freq=2, min_word_len=3)
        pairs = [frozenset((c["word_a"], c["word_b"])) for c in candidates]
        self.assertNotIn(frozenset(("kwa", "lwa")), pairs)

    def test_excludes_already_corrected_pairs(self):
        texts = ["mndu ni mundu"] * 5
        analyzer = TaitaAnalyzer(texts)
        candidates = analyzer.find_edit_distance_candidates(min_freq=2, min_pair_freq=2, min_word_len=3)
        pairs = [frozenset((c["word_a"], c["word_b"])) for c in candidates]
        self.assertNotIn(frozenset(("mndu", "mundu")), pairs)

    def test_finds_new_unsettled_pair(self):
        texts = ["fooba text here", "fooby text here"] * 5
        analyzer = TaitaAnalyzer(texts)
        candidates = analyzer.find_edit_distance_candidates(min_freq=2, min_pair_freq=2, min_word_len=3)
        pairs = [frozenset((c["word_a"], c["word_b"])) for c in candidates]
        self.assertIn(frozenset(("fooba", "fooby")), pairs)

    def test_example_sentence(self):
        analyzer = TaitaAnalyzer(["first one", "second mundu here"])
        self.assertEqual(analyzer.example_sentence("mundu"), "second mundu here")
        self.assertEqual(analyzer.example_sentence("missing"), "")


if __name__ == "__main__":
    unittest.main()
