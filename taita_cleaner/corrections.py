"""
Native-speaker-confirmed correction data for Kidaw'ida.

Everything in this file was confirmed by a native speaker reviewing real
example sentences from the corpus -- NOT picked automatically by frequency
ratio. That distinction matters here: on this corpus, the more-frequent
spelling was wrong about as often as it was right (e.g. `mndu` outnumbers
`mundu` 301 to 234, but `mundu` is correct; `uja` outnumbers `ujha` 124 to
41, but `ujha` is correct). So nothing below is a guess -- but also nothing
here was derived from a general rule except the apostrophe one, which is a
real orthographic fact about the language, not a statistical pattern.
"""

# Word -> correct spelling. Applied after the apostrophe rule (see utils.py),
# so these keys are already apostrophe-normalized.
CONFIRMED_CORRECTIONS = {
    "mndu": "mundu",           # missing vowel
    "izanga": "isanga",        # z/s
    "ghwmanyikie": "ghwamanyikie",  # missing vowel
    "gwa": "ghwa",             # missing h
    "kihi": "kii",             # h/no-h -- confirmed by matching "shekeria ni kihi?"
                                # / "shekeria ni kii?" used interchangeably
    "ja": "jha",               # h/no-h -- confirmed by matching "ilagho ja
                                # thamani" / "ilagho jha samani" phrase pairs.
                                # NOTE: `ja`/`jha` review was based on a sample
                                # of examples, not every occurrence -- worth a
                                # spot-check if it ever looks wrong in context.
    "ata": "hata",             # missing h
    "uja": "ujha",             # missing h
}

# Pairs explicitly confirmed to be DIFFERENT words, one edit apart by
# coincidence -- an analyzer/miner must never propose merging these, even
# at a high frequency ratio. Most of these are Bantu-style noun-class
# concord/agreement particles (like Swahili cha/vya/la/ya/wa), not
# misspellings of one shared word.
CONFIRMED_DISTINCT = {
    frozenset(("kwa", "lwa")),
    frozenset(("gha", "ghwa")),
    frozenset(("agha", "gha")),
    frozenset(("cha", "gha")),
    frozenset(("aha", "gha")),
    frozenset(("cha", "chia")),
    frozenset(("mana", "mwana")),
    frozenset(("andu", "wandu")),
    frozenset(("andu", "mundu")),
    frozenset(("koshi", "kosi")),
    frozenset(("saa", "shaa")),
}

# Words that are real on their own but are NEVER a correct spelling of
# another word -- and also can't be blanket-corrected, because which
# meaning applies depends on the sentence. The cleaner leaves these alone
# rather than guess.
AMBIGUOUS_WORDS = {
    "mana": "Real word with its own meaning; never a correct spelling of "
            "'mwana', but not every occurrence is wrong either -- needs "
            "per-sentence judgment, not a blanket rule. Left untouched.",
}

# Specific sentence-level usage errors -- the right word exists, but the
# wrong one was used for this grammatical slot (grammar/agreement, not
# spelling). Not something a word-level correction map can fix generally;
# logged here so they aren't lost, applied only to the exact sentence.
FLAGGED_SENTENCES = [
    {
        "sentence": "Wusalama gha barabarenyi ni muhimu saana",
        "issue": "'gha' used where 'ghwa' (of) belongs for this noun",
        "suggested": "Wusalama ghwa barabarenyi ni muhimu saana",
    },
]
