# Taita (Kidaw'ida) Text Cleaner

A standalone Python library for cleaning and spelling-correcting Kidaw'ida
(Taita) text. No external dictionary dependencies — corrections come from
frequency-based mining of the corpus itself, **verified by a native
speaker**, not applied automatically by frequency alone.

That last point matters more here than it does for some other languages:
on this corpus, the more-frequent spelling of a word was wrong almost as
often as it was right (`mndu` outnumbers `mundu` 301 to 234, but `mundu` is
correct; `uja` outnumbers `ujha` 124 to 41, but `ujha` is correct). So this
tool does not auto-apply "whichever spelling wins by frequency" the way a
purely statistical cleaner might — every entry in `corrections.py` was a
human call on real example sentences.

## Why this isn't a copy of the Kikuyu cleaner

The overall shape (mine candidate pairs → get them confirmed → apply with a
changelog) is the same as the Kikuyu Text Cleaner this was modeled on. The
actual *rules* aren't ported, because Taita's confusable patterns aren't the
same as Kikuyu's:

- Kikuyu's variation is mostly diacritics (`ĩ`/`i`, `ũ`/`u`), and the marked
  form is reliably the standard one.
- Taita has no diacritics at all — its noise is almost entirely apostrophe
  placement and "extra h" spellings (`gha`/`ghwa`, `ja`/`jha`, `ata`/`hata`),
  and neither direction is reliable from frequency alone.
- A large share of Taita's short, high-frequency "candidate typos" turned
  out to be genuinely different words — Bantu-style noun-class agreement
  particles (`cha`/`gha`/`aha`/`agha`/`ghwa`/`wa`, all meaning roughly "of"
  for different noun classes), not misspellings of one shared word. Treating
  those as typos would have quietly damaged the corpus.

So: **mine your own corpus, don't assume another language's pattern set.**
See the top-level repo README for the fuller writeup of this process.

## Installation

Just the `taita_cleaner` folder, stdlib only. Python 3.8+.

## Quick Start

```python
from taita_cleaner import TaitaCleaner, TaitaAnalyzer

# === Basic Cleaning ===
texts = [
    "Kila mndu wawehitaji rafiki wa loli",
    "W'andu w'iboilwagha ni kubonya maw'iw'i.",
    "Mchezo gwa moira ghwa mindi ghwmanyikie",
]

cleaner = TaitaCleaner()
corrected_texts, changes, stats = cleaner.process_texts(texts)
print(f"Modified {stats['rows_modified']} rows")
print(f"Applied {stats['total_corrections']} corrections")

# === Analysis Only (find NEW candidate pairs nobody's reviewed yet) ===
analyzer = TaitaAnalyzer(texts)
results = analyzer.run_full_analysis()
print(f"Found {len(results['candidate_pairs'])} unsettled candidate pairs")
```

### Command Line

```bash
# Clean a CSV column, with a changelog of every change made
python -m taita_cleaner.cli clean input.csv --column dav --output cleaned.csv --changelog changelog.csv

# Mine a CSV column for new candidate pairs (excludes anything already confirmed)
python -m taita_cleaner.cli analyze input.csv --column dav --output review_sheet.csv

# Clean a single string
python -m taita_cleaner.cli text "Kila mndu wawehitaji rafiki wa loli"
```

## Modules

### `TaitaCleaner`

| Method | Description |
|---|---|
| `__init__(corrections=None)` | Optional dict to extend/override the confirmed correction map |
| `add_custom_corrections(dict)` | Add more corrections |
| `correct_word(word)` | Correct a single word -> `(corrected, source)` |
| `correct_text(text, track_changes=True, clean_first=False)` | Correct a string -> `(corrected, changes)` |
| `process_texts(texts, clean_first=False)` | Correct a list -> `(corrected_texts, changes, stats)` |
| `get_correction_summary()` | Stats on everything corrected so far |
| `export_correction_map()` | The active correction map as a list of dicts |

Every correction is tagged with its `source`: `apostrophe_rule` (the ng'
rule) or `confirmed_correction` (a specific word-level fix from
`corrections.py`). Nothing is ever silently applied — `correct_text` and
`process_texts` always return the changelog alongside the result.

### `TaitaAnalyzer`

Mines a set of texts for new candidate spelling-variant pairs (one
character-edit apart), the same technique used to build the very first
review sheet. Automatically **excludes** anything already settled in
`corrections.py` (`CONFIRMED_CORRECTIONS` and `CONFIRMED_DISTINCT`), so
re-running it after each review round only surfaces pairs nobody has
judged yet.

| Method | Description |
|---|---|
| `__init__(texts=None)` / `add_texts(texts)` | Load texts |
| `word_frequencies()` | Counter of word -> count |
| `find_edit_distance_candidates(...)` | Unsettled candidate pairs, ranked by combined frequency |
| `example_sentence(word)` | First sentence containing that word |
| `run_full_analysis(...)` | Stats + candidate pairs in one call |

## The Confirmed Rules (`corrections.py`)

**The apostrophe rule** (`normalize_apostrophes` in `utils.py`) — confirmed
to be a real, general fact about the orthography, not a per-word judgment:

> The apostrophe is only meaningful in `ng'` (the same nasal marker Swahili
> uses in `ng'ombe`). Every other apostrophe — word-initial (`w'andu`),
> root-internal (`nguw'o`, `daw'ida`, `mariw'a`), after `m` (`m'baa`), or
> just stray (`wu'ghoma`) — gets dropped.

This single rule resolved 428 of 451 candidate apostrophe pairs at once,
affecting 13,330 of the corpus's 100,324 tokens (~13%).

**Word-level corrections** — each one an individual native-speaker call,
*not* derivable from a rule (see `CONFIRMED_CORRECTIONS` in
`corrections.py` for the full list and notes on each).

**Confirmed-distinct pairs** (`CONFIRMED_DISTINCT`) — pairs that look like
typo candidates but are real, different words. The analyzer will never
propose these again.

**Ambiguous words** (`AMBIGUOUS_WORDS`) — words that are sometimes correct
and sometimes a typo for something else, depending on context (e.g. `mana`,
which has its own meaning but is never a correct spelling of `mwana`).
These are left untouched rather than guessed at; fixing them properly would
need sentence-by-sentence review, not a word-level rule.

**Flagged sentences** (`FLAGGED_SENTENCES`) — a different category of
problem: the right word exists, but the wrong one was used for the
grammatical slot (e.g. `gha` used where `ghwa` belongs). This is a
grammar/agreement issue, not a spelling one, and isn't something a
frequency-based word-level tool can fix in general — logged per-sentence
instead of folded into the correction map.

## Testing

```bash
python -m unittest taita_cleaner.tests -v
```

28 tests covering the apostrophe rule, the cleaner, the analyzer's
exclusion logic, and the utility functions.

## Extending

To add a new confirmed correction once it's been reviewed, add it to
`CONFIRMED_CORRECTIONS` in `corrections.py`. To record a pair that looked
like a typo but isn't, add it to `CONFIRMED_DISTINCT`. Re-run the analyzer
afterward — it'll stop suggesting anything you've already settled.
