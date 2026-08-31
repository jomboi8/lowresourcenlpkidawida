"""
Command-line interface for taita_cleaner.

    python -m taita_cleaner.cli clean input.csv --column dav --output cleaned.csv
    python -m taita_cleaner.cli analyze input.csv --column dav --output review_sheet.csv
    python -m taita_cleaner.cli text "Ukaniw'ona wadazamiliwa ni ini."
"""
import argparse
import csv

from .analyzer import TaitaAnalyzer
from .cleaner import TaitaCleaner


def cmd_clean(args):
    with open(args.input, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fieldnames = reader.fieldnames

    cleaner = TaitaCleaner()
    texts = [row[args.column] for row in rows]
    corrected_texts, changes, stats = cleaner.process_texts(texts)

    for row, corrected in zip(rows, corrected_texts):
        row[args.column] = corrected

    with open(args.output, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)

    if args.changelog:
        with open(args.changelog, "w", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            w.writerow(["row", "original_text", "original_word", "corrected_word", "source"])
            for i, row_changes in enumerate(changes):
                for c in row_changes:
                    w.writerow([i, texts[i], c["original"], c["corrected"], c["source"]])

    print(f"Processed {stats['rows_processed']} rows")
    print(f"Modified {stats['rows_modified']} rows")
    print(f"Applied {stats['total_corrections']} corrections")
    print(f"Wrote {args.output}")
    if args.changelog:
        print(f"Wrote {args.changelog}")


def cmd_analyze(args):
    with open(args.input, encoding="utf-8", newline="") as f:
        texts = [row[args.column] for row in csv.DictReader(f)]

    analyzer = TaitaAnalyzer(texts)
    results = analyzer.run_full_analysis()
    candidates = results["candidate_pairs"]

    with open(args.output, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["edit_type", "edit_detail", "ratio", "word_a", "freq_a", "example_a",
                    "word_b", "freq_b", "example_b", "decision", "preferred_form", "notes"])
        for r in candidates[: args.limit]:
            w.writerow([
                r["edit_type"], r["edit_detail"], r["ratio"],
                r["word_a"], r["freq_a"], analyzer.example_sentence(r["word_a"]),
                r["word_b"], r["freq_b"], analyzer.example_sentence(r["word_b"]),
                "", "", "",
            ])

    print(f"texts: {results['statistics']['total_texts']}  "
          f"tokens: {results['statistics']['total_tokens']}  "
          f"unique words: {results['statistics']['unique_words']}")
    print(f"new (unsettled) candidate pairs: {len(candidates)}")
    print(f"Wrote top {min(args.limit, len(candidates))} to {args.output}")


def cmd_text(args):
    cleaner = TaitaCleaner()
    corrected, changes = cleaner.correct_text(args.text)
    print(corrected)
    if changes:
        for c in changes:
            print(f"  {c['original']!r} -> {c['corrected']!r}  ({c['source']})")


def main():
    parser = argparse.ArgumentParser(prog="taita_cleaner")
    sub = parser.add_subparsers(dest="command", required=True)

    p_clean = sub.add_parser("clean", help="Clean a CSV column")
    p_clean.add_argument("input")
    p_clean.add_argument("--column", required=True)
    p_clean.add_argument("--output", required=True)
    p_clean.add_argument("--changelog", default=None)
    p_clean.set_defaults(func=cmd_clean)

    p_analyze = sub.add_parser("analyze", help="Mine a CSV column for new candidate pairs")
    p_analyze.add_argument("input")
    p_analyze.add_argument("--column", required=True)
    p_analyze.add_argument("--output", required=True)
    p_analyze.add_argument("--limit", type=int, default=200)
    p_analyze.set_defaults(func=cmd_analyze)

    p_text = sub.add_parser("text", help="Clean a single string")
    p_text.add_argument("text")
    p_text.set_defaults(func=cmd_text)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
