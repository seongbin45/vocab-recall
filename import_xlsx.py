#!/usr/bin/env python3
"""Convert Excel word lists into bank JSON files for the vocab app."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parent / "data"
BANK_DIR = DATA_DIR / "banks"
HANGUL = re.compile(r"[\uac00-\ud7a3]")
LATIN = re.compile(r"[A-Za-z]")


def primary_meaning(raw: str) -> str:
    """Use full meaning string; normalize separators for readability."""
    s = re.sub(r"\s*\|\s*", " · ", raw.strip())
    s = re.sub(r"\s+", " ", s)
    return s


def looks_hangul(s: str) -> bool:
    return bool(HANGUL.search(s))


def looks_latin(s: str) -> bool:
    return bool(LATIN.search(s))


def normalize_pair(word: str, meaning: str) -> tuple[str, str] | None:
    word = str(word).strip()
    meaning = str(meaning).strip()
    if not word or word.lower() == "nan":
        return None
    if not meaning or meaning.lower() == "nan":
        return None

    # Korean headword + English glosses → flip for English learning
    if looks_hangul(word) and looks_latin(meaning) and not looks_hangul(meaning):
        # first English gloss as cue
        first = re.split(r"[|·,/]", meaning)[0].strip()
        first = re.sub(r"^a\s+", "", first, flags=re.I)
        if not first:
            return None
        return first, primary_meaning(word)

    en = word
    ko = primary_meaning(meaning)
    if not en or not ko:
        return None
    return en, ko


def read_sheet(path: Path) -> list[dict]:
    df = pd.read_excel(path, sheet_name=0, header=0)
    # expect 단어 + 주요뜻 (발음 optional)
    cols = {str(c).strip(): c for c in df.columns}
    word_col = cols.get("단어") or df.columns[0]
    meaning_col = cols.get("주요뜻")
    if meaning_col is None:
        # last non-pronunciation column
        meaning_col = df.columns[-1]

    out: list[dict] = []
    seen: set[str] = set()
    for _, row in df.iterrows():
        pair = normalize_pair(row[word_col], row[meaning_col])
        if not pair:
            continue
        en, ko = pair
        key = en.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append({"en": en, "ko": ko})
    return out


def write_bank(name: str, source: str, words: list[dict], origin: str) -> Path:
    BANK_DIR.mkdir(parents=True, exist_ok=True)
    path = BANK_DIR / f"{name}.json"
    payload = {
        "name": name,
        "source": source,
        "origin_file": origin,
        "count": len(words),
        "words": words,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def main() -> None:
    jobs = [
        (
            "high_school",
            "High school",
            DATA_DIR / "High school words.xlsx",
        ),
        (
            "absolute_beginner",
            "Absolute Beginner",
            DATA_DIR / "Absolute Beginner words.xlsx",
        ),
    ]
    for name, source, xlsx in jobs:
        if not xlsx.exists():
            print(f"MISSING {xlsx}")
            continue
        words = read_sheet(xlsx)
        path = write_bank(name, source, words, xlsx.name)
        print(f"{source}: {len(words)} words → {path}")


if __name__ == "__main__":
    main()
