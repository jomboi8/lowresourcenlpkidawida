"""
Core utility functions: tokenizing, frequency counting, Unicode/marker
cleanup, and the apostrophe rule.

No external dependencies -- everything here is stdlib.
"""
import re
import unicodedata
from collections import Counter

# words are letters plus the apostrophe (meaningful in Kidaw'ida spelling,
# e.g. ng'ombe) -- extracted lowercase for frequency counting / matching.
TOKEN_RE = re.compile(r"[a-zA-Z']+")

# transcript markers like Kikuyu's [Pause]/[cs] -- kept for parity with that
# tool's API and in case future data has them. None have shown up in the
# Kidaw'ida-Kiswahili corpus so far, so this is currently a light passthrough.
MARKER_RE = re.compile(r"\[[^\]]*\]")

# mojibake / typographic characters that sometimes leak in from copy-pasted
# text, normalized to their plain-ASCII equivalents.
CHAR_FIXUPS = {
    "’": "'",   # ' -> '
    "‘": "'",   # ' -> '
    "“": '"',   # " -> "
    "”": '"',   # " -> "
    "\xa0": " ",     # non-breaking space
    "…": "...", # ellipsis
    "–": "-",   # en dash
    "—": "-",   # em dash
}
WHITESPACE_RE = re.compile(r"\s+")


def extract_words(text):
    """Extract lowercase word tokens (letters + apostrophe) from text."""
    return TOKEN_RE.findall(text.lower())


def get_word_frequencies(words):
    """Return a Counter of word -> occurrence count."""
    return Counter(words)


def clean_markers(text):
    """Remove transcript markers like [Pause], [cs]. No-op if none present."""
    return MARKER_RE.sub("", text)


def normalize_unicode(text, form="NFC", fix_typographic=True):
    """Unicode-normalize text and optionally fix mojibake characters."""
    text = unicodedata.normalize(form, text)
    if fix_typographic:
        for bad, good in CHAR_FIXUPS.items():
            text = text.replace(bad, good)
    return WHITESPACE_RE.sub(" ", text).strip()


def normalize_apostrophes(word):
    """
    Apply the confirmed Kidaw'ida apostrophe rule: the apostrophe is only
    phonemic in `ng'` (the same nasal marker Swahili uses, e.g. ng'ombe).
    Every other apostrophe in the corpus (w'andu, m'baa, mari'wa, ...) turned
    out to be inconsistent transcription, not a real distinction -- confirmed
    by a native speaker, not inferred from frequency. So: keep it in ng',
    strip it everywhere else.
    """
    protected = word.replace("ng'", "ng\0")
    stripped = protected.replace("'", "")
    return stripped.replace("\0", "'")


def is_valid_taita_word(word):
    """Check if a word uses only letters and the apostrophe."""
    return bool(word) and bool(re.fullmatch(r"[a-zA-Z']+", word))


def match_case(source, replacement):
    """Apply the casing of `source` to `replacement` (Title/UPPER/lower)."""
    if source.isupper():
        return replacement.upper()
    if source[:1].isupper():
        return replacement[:1].upper() + replacement[1:]
    return replacement
