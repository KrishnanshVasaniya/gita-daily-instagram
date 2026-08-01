"""
Picks the next verse (in order) from data/verses.json, generates its 2-slide
carousel, writes data/run_meta.json describing this run (for the posting
script to pick up), and advances data/state.json so tomorrow's run moves on
to the next verse.

This script does NOT talk to Instagram. It only prepares content.
Run post_to_instagram.py afterwards (once the images are pushed to GitHub
and reachable at a public raw.githubusercontent.com URL).
"""

import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
VERSES_PATH = os.path.join(DATA_DIR, "verses.json")
STATE_PATH = os.path.join(DATA_DIR, "state.json")
META_PATH = os.path.join(DATA_DIR, "run_meta.json")

import generate_card  # noqa: E402  (same scripts/ folder)

DEFAULT_HASHTAGS = (
    "#BhagavadGita #Gita #Krishna #Arjuna #Dharma #Karma #HinduWisdom "
    "#SpiritualQuotes #SanatanaDharma #GitaWisdom"
)


def build_caption(verse):
    return (
        f"Bhagavad Gita, Chapter {verse['chapter']}, Verse {verse['verse']}\n\n"
        f"\u201c{verse['translation']}\u201d\n\n"
        f"{verse['explanation']}\n\n"
        f"{DEFAULT_HASHTAGS}"
    )


def main():
    with open(VERSES_PATH, encoding="utf-8") as f:
        verses = json.load(f)

    with open(STATE_PATH, encoding="utf-8") as f:
        state = json.load(f)

    idx = state["next_index"] % len(verses)
    verse = verses[idx]

    slide1_path, slide2_path = generate_card.generate(verse)

    meta = {
        "chapter": verse["chapter"],
        "verse": verse["verse"],
        "caption": build_caption(verse),
        "slide1_file": os.path.relpath(slide1_path, BASE_DIR),
        "slide2_file": os.path.relpath(slide2_path, BASE_DIR),
    }
    with open(META_PATH, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    state["next_index"] = idx + 1
    with open(STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)

    print(f"Prepared Chapter {verse['chapter']}, Verse {verse['verse']}")
    print(f"  {slide1_path}")
    print(f"  {slide2_path}")
    print(f"  meta -> {META_PATH}")


if __name__ == "__main__":
    main()
