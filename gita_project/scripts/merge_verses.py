"""
Merges the per-chapter translations/explanations in chapter_content/ with the
Sanskrit in data/authoritative.json, and writes the combined result to
data/verses.json.

All 18 chapters are rebuilt from chapter_content/ch1.py ... ch18.py on every
run, so the script is idempotent and verses.json is fully derived output.

Usage:
    python scripts/merge_verses.py
"""

import importlib
import json
import os
import re
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
AUTHORITATIVE_PATH = os.path.join(DATA_DIR, "authoritative.json")
VERSES_PATH = os.path.join(DATA_DIR, "verses.json")

# chapter_content/ lives next to scripts/, under the project root.
sys.path.insert(0, BASE_DIR)

GENERATED_CHAPTERS = range(1, 19)

DEVANAGARI_DIGITS = str.maketrans("0123456789", "०१२३४५६७८९")

# Trailing "।।2.47।।" style verse marker in the source data.
VERSE_MARKER_RE = re.compile(r"।{1,2}\s*\d+\s*\.\s*\d+\s*।{1,2}\s*$")


def to_devanagari(number):
    return str(number).translate(DEVANAGARI_DIGITS)


def normalize_sanskrit(raw_text, verse_number):
    """Tidy a source `text` field into the shape used by verses.json.

    The source separates padas with blank lines and ends each verse with a
    "।।chapter.verse।।" marker. We keep the source's own line breaks — several
    verses in the longer metres split mid-word, so inserting our own dandas
    would corrupt them — and only replace the trailing marker with the
    "॥<verse>॥" form already used by Chapter 1.
    """
    text = raw_text.replace(" ", " ").strip()
    text = VERSE_MARKER_RE.sub("", text).strip()

    lines = [line.strip() for line in text.split("\n")]
    lines = [line for line in lines if line]

    # A few verses arrive as one long line with an internal danda doing the
    # work of a line break; split those so the card renderer can breathe.
    if len(lines) == 1 and "।" in lines[0][:-1]:
        parts = [p.strip() for p in lines[0].split("।")]
        parts = [p for p in parts if p]
        if len(parts) > 1:
            lines = [p + "।" for p in parts[:-1]] + [parts[-1]]

    if not lines:
        raise ValueError("empty sanskrit text")

    lines[-1] = "{} ॥{}॥".format(lines[-1].rstrip("।").rstrip(), to_devanagari(verse_number))
    return "\n".join(lines)


def load_authoritative():
    with open(AUTHORITATIVE_PATH, encoding="utf-8") as f:
        records = json.load(f)
    index = {}
    for record in records:
        key = (record["chapter_number"], record["verse_number"])
        index[key] = record
    return index


def load_chapter_content(chapter):
    module = importlib.import_module("chapter_content.ch{}".format(chapter))
    return module.CONTENT


def build_generated_verses(authoritative):
    verses = []
    problems = []

    for chapter in GENERATED_CHAPTERS:
        content = load_chapter_content(chapter)
        expected = sorted(
            v for (c, v) in authoritative if c == chapter
        )
        written = sorted(content)

        missing = [v for v in expected if v not in content]
        extra = [v for v in written if v not in expected]
        if missing:
            problems.append("chapter {}: no content for verses {}".format(chapter, missing))
        if extra:
            problems.append("chapter {}: content for non-existent verses {}".format(chapter, extra))

        for verse_number in expected:
            entry = content.get(verse_number)
            if entry is None:
                continue
            translation = entry["t"].strip()
            explanation = entry["e"].strip()
            if not translation or not explanation:
                problems.append("chapter {} verse {}: blank text".format(chapter, verse_number))
                continue
            record = authoritative[(chapter, verse_number)]
            verses.append(
                {
                    "chapter": chapter,
                    "verse": verse_number,
                    "sanskrit": normalize_sanskrit(record["text"], verse_number),
                    "translation": translation,
                    "explanation": explanation,
                }
            )

    return verses, problems


def main():
    authoritative = load_authoritative()

    merged, problems = build_generated_verses(authoritative)
    if problems:
        for problem in problems:
            print("ERROR: {}".format(problem))
        raise SystemExit("refusing to write verses.json with {} problem(s)".format(len(problems)))

    with open(VERSES_PATH, "w", encoding="utf-8") as f:
        json.dump(merged, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print("Wrote {} verses to {}".format(len(merged), VERSES_PATH))
    for chapter in GENERATED_CHAPTERS:
        count = sum(1 for v in merged if v["chapter"] == chapter)
        print("    ch{:>2}: {:>3} verses".format(chapter, count))


if __name__ == "__main__":
    main()
