# Kidaw'ida–Kiswahili Parallel Corpus (Cleaned)

A single, cleaned, deduplicated `dav → swa` (Kidaw'ida–Kiswahili) parallel
corpus, built for our own machine translation work from a public dataset we
downloaded.

**This is not our data.** We did not collect or translate any of these
sentences. It originates from the Lacuna Fund–supported Kenyan low-resource
language project described below.We downloaded one of that project's public
releases and cleaned it up for our own use. Full credit for the underlying
work belongs to its original authors and contributors.

## Contents

- `corpus/kidawida_kiswahili_corpus.csv` — the corpus: two columns, `dav`, `swa`. One sentence pair per row.
- `build_corpus.ipynb` — the notebook that produced it from the raw download. Runs in Google Colab or Jupyter.
- `LICENSE` — Apache License 2.0 (verbatim, from the source repo).


## Original source

- **waleghwa/low-resource-language-data** (Zenodo, DOI:
  [10.5281/zenodo.13355021](https://doi.org/10.5281/zenodo.13355021)) — *Parallel
  Corpora for Kiswahili and Kidaw'ida, Kalenjin and Dholuo*

**Authors / data curators:** Audrey Mbogho (Project Manager, USIU Africa),
Andrew Kipkebut (Kabarak University), Lilian Wanzare (Maseno University),
Quin Awuor (USIU Africa), Vivian Oloo (Maseno University), Rose Lugano
(University of Florida), with data collection by Esther Mkawanyika Nkrumah,
Shalet Doreen Mkamzungu, Patience Chao Mwangola and David Mbela Mwakaba.
Funded by the [Lacuna Fund](https://lacunafund.org/).

**License:** **Apache License 2.0**, per the `LICENSE` file in the source
GitHub repo ([waleghwa/low-resource-language-data](https://github.com/waleghwa/low-resource-language-data)),
which is the project's actively maintained home (Zenodo hosts periodic
snapshot uploads of it). 

**How to cite the original data:**

```
Mbogho, A., Kipkebut, A., Wanzare, L., Awuor, Q., Oloo, V., & Lugano, R. (2024).
waleghwa/low-resource-language-data Parallel Corpora for Kiswahili and
Kidaw'ida, Kalenjin and Dholuo (v1.0.0) [Data set]. Zenodo.
https://doi.org/10.5281/zenodo.13355021
```

**Modifications from the original:** cleaned encoding, dropped empty
and exact-duplicate rows. 

## What the notebook does (`build_corpus.ipynb`)

1. **Decodes correctly.** The raw CSV is otherwise-ASCII but has a handful of
   stray Windows-1252 bytes (smart quotes, non-breaking spaces) baked in, so
   it's read as `cp1252` rather than `utf-8`, which would raise a decode error.
2. **Normalizes text**: Unicode NFC normalization, curly quotes/NBSP/ellipsis
   collapsed to plain ASCII equivalents, whitespace collapsed without
   touching the `'` used meaningfully in Kidaw'ida orthography (`w'`, `ng'`,
   `m'`, etc.).
3. **Drops** rows left empty on either side after cleaning.
4. **Deduplicates** on exact `(dav, swa)` pairs (the raw file has 4,448
   internal exact duplicates), keeping the first occurrence.
5. **Writes** `corpus/kidawida_kiswahili_corpus.{csv,jsonl}` — just `dav` and
   `swa`.

Result: 26,608 raw rows → **22,151 unique, cleaned pairs**.

Re-run it by opening `build_corpus.ipynb` in Google Colab (or Jupyter) and
running all cells top to bottom. If the raw CSV isn't already next to the
notebook, it'll prompt you to upload it.

