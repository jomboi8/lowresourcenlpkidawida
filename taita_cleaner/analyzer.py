"""
TaitaAnalyzer: mines a set of texts for candidate spelling-variant pairs
(words one character-edit apart), for a native speaker to review. This is
the same technique used to build the very first review sheet, packaged up
so later rounds are cheap to re-run.

It automatically excludes anything already settled in corrections.py, so
each new round only surfaces pairs nobody has judged yet.
"""
from .corrections import CONFIRMED_CORRECTIONS, CONFIRMED_DISTINCT
from .utils import TOKEN_RE, get_word_frequencies


class TaitaAnalyzer:
    def __init__(self, texts=None):
        self.texts = list(texts) if texts else []

    def add_texts(self, texts):
        self.texts.extend(texts)

    def _tokens(self):
        tokens = []
        for t in self.texts:
            tokens.extend(TOKEN_RE.findall(t.lower()))
        return tokens

    def word_frequencies(self):
        return get_word_frequencies(self._tokens())

    def _already_settled(self, a, b):
        pair = frozenset((a, b))
        if pair in CONFIRMED_DISTINCT:
            return True
        # a correction already maps one side to the other (or both to a
        # shared standard form) -- no need to ask about it again
        resolved_a = CONFIRMED_CORRECTIONS.get(a, a)
        resolved_b = CONFIRMED_CORRECTIONS.get(b, b)
        return resolved_a == resolved_b and (a in CONFIRMED_CORRECTIONS or b in CONFIRMED_CORRECTIONS)

    def find_edit_distance_candidates(self, min_freq=2, min_pair_freq=3, min_word_len=3):
        """
        Find word pairs one character-edit apart (insertion/deletion or
        substitution), excluding anything already settled. Returns a list
        of dicts sorted by combined frequency (most impactful first).
        """
        freq = self.word_frequencies()
        vocab = {w for w, c in freq.items() if c >= min_freq and len(w) >= min_word_len}

        pairs = {}

        # indel: one character inserted/deleted
        for w in vocab:
            for i in range(len(w)):
                d = w[:i] + w[i + 1:]
                if d in vocab and d != w:
                    key = tuple(sorted((w, d)))
                    pairs.setdefault(key, ("indel", w[i]))

        # substitution: same length, exactly one position differs
        by_length = {}
        for w in vocab:
            by_length.setdefault(len(w), []).append(w)
        for length, words in by_length.items():
            buckets = {}
            for w in words:
                for i in range(length):
                    buckets.setdefault(w[:i] + "*" + w[i + 1:], []).append(w)
            for group in buckets.values():
                if len(group) < 2:
                    continue
                for i in range(len(group)):
                    for j in range(i + 1, len(group)):
                        a, b = group[i], group[j]
                        if a == b:
                            continue
                        diffs = [k for k in range(length) if a[k] != b[k]]
                        if len(diffs) == 1:
                            key = tuple(sorted((a, b)))
                            pairs.setdefault(key, ("substitution", f"{a[diffs[0]]}/{b[diffs[0]]}"))

        results = []
        for (a, b), (edit_type, detail) in pairs.items():
            if self._already_settled(a, b):
                continue
            fa, fb = freq[a], freq[b]
            if min(fa, fb) < min_pair_freq:
                continue
            ratio = max(fa, fb) / max(min(fa, fb), 1)
            results.append({
                "word_a": a, "freq_a": fa, "word_b": b, "freq_b": fb,
                "ratio": round(ratio, 1), "edit_type": edit_type, "edit_detail": detail,
            })

        results.sort(key=lambda r: -(r["freq_a"] + r["freq_b"]))
        return results

    def example_sentence(self, word):
        """First text containing `word` as a whole token."""
        import re
        pattern = re.compile(r"(?<![a-zA-Z'])" + re.escape(word) + r"(?![a-zA-Z'])", re.IGNORECASE)
        for t in self.texts:
            if pattern.search(t):
                return t
        return ""

    def run_full_analysis(self, min_freq=2, min_pair_freq=3, min_word_len=3):
        freq = self.word_frequencies()
        candidates = self.find_edit_distance_candidates(min_freq, min_pair_freq, min_word_len)
        return {
            "statistics": {
                "total_texts": len(self.texts),
                "total_tokens": sum(freq.values()),
                "unique_words": len(freq),
            },
            "candidate_pairs": candidates,
        }
