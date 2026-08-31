"""
TaitaCleaner: applies the confirmed apostrophe rule and word-level
corrections to Kidaw'ida text, tracking every change it makes.

Nothing here is applied silently -- correct_text/process_texts always
return a changelog alongside the corrected text.
"""
from collections import Counter

from .corrections import AMBIGUOUS_WORDS, CONFIRMED_CORRECTIONS
from .utils import (
    TOKEN_RE,
    clean_markers,
    match_case,
    normalize_apostrophes,
    normalize_unicode,
)


class TaitaCleaner:
    def __init__(self, corrections=None):
        """corrections: optional dict overriding/extending CONFIRMED_CORRECTIONS."""
        self.corrections = dict(CONFIRMED_CORRECTIONS)
        if corrections:
            self.corrections.update(corrections)
        self._changes = []  # accumulated across calls, for get_correction_summary()

    def add_custom_corrections(self, corrections):
        self.corrections.update(corrections)

    def correct_word(self, word):
        """
        Apply the apostrophe rule, then the correction map, to a single
        lowercase word. Returns (corrected_word, source) where source is
        one of: 'apostrophe_rule', 'confirmed_correction', or None (no
        change). Ambiguous words (see corrections.py) are never touched.
        """
        lower = word.lower()
        if lower in AMBIGUOUS_WORDS:
            return word, None

        after_apostrophe = normalize_apostrophes(lower)
        if after_apostrophe != lower:
            source = "apostrophe_rule"
        else:
            source = None

        final = self.corrections.get(after_apostrophe, after_apostrophe)
        if final != after_apostrophe:
            source = "confirmed_correction"

        if final == lower:
            return word, None
        return match_case(word, final), source

    def correct_text(self, text, track_changes=True, clean_first=False):
        """
        Correct a single text string word by word, preserving everything
        that isn't a word token (spacing, punctuation).
        """
        if clean_first:
            text = clean_markers(normalize_unicode(text))

        changes = []

        def replace(m):
            original = m.group(0)
            corrected, source = self.correct_word(original)
            if corrected != original:
                changes.append({"original": original, "corrected": corrected, "source": source})
            return corrected

        corrected_text = TOKEN_RE.sub(replace, text)
        if track_changes:
            self._changes.extend(changes)
            return corrected_text, changes
        return corrected_text

    def process_texts(self, texts, clean_first=False):
        """
        Correct a list of texts. Returns (corrected_texts, changes,
        stats) where changes is a list (one entry per text) of that
        text's change list, and stats summarizes the run.
        """
        corrected_texts = []
        all_changes = []
        rows_modified = 0
        for text in texts:
            corrected, changes = self.correct_text(text, track_changes=True, clean_first=clean_first)
            corrected_texts.append(corrected)
            all_changes.append(changes)
            if changes:
                rows_modified += 1

        stats = {
            "rows_processed": len(texts),
            "rows_modified": rows_modified,
            "total_corrections": sum(len(c) for c in all_changes),
        }
        return corrected_texts, all_changes, stats

    def get_correction_summary(self):
        """Summary of every correction applied across all correct_text calls so far."""
        by_source = Counter(c["source"] for c in self._changes)
        by_word = Counter((c["original"].lower(), c["corrected"].lower()) for c in self._changes)
        return {
            "total_corrections": len(self._changes),
            "by_source": dict(by_source),
            "most_common_corrections": by_word.most_common(20),
        }

    def export_correction_map(self):
        """Export the active correction map as a list of dicts."""
        return [{"wrong": w, "right": r} for w, r in sorted(self.corrections.items())]
