"""Word-bank helpers: load Excel-derived banks and draw unused words."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

BANK_DIR = Path(__file__).resolve().parent / "data" / "banks"

BANKS = {
    "absolute_beginner": {
        "label": "Absolute Beginner",
        "file": "absolute_beginner.json",
    },
    "high_school": {
        "label": "High school",
        "file": "high_school.json",
    },
}


def bank_path(key: str) -> Path:
    return BANK_DIR / BANKS[key]["file"]


def load_bank(key: str) -> dict[str, Any]:
    path = bank_path(key)
    if not path.exists():
        return {"name": key, "source": key, "count": 0, "words": []}
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def known_english(data: dict) -> set[str]:
    return {str(it.get("en", "")).lower() for it in data.get("items", [])}


def unused_words(bank: dict, data: dict) -> list[dict]:
    known = known_english(data)
    out = []
    for w in bank.get("words", []):
        en = str(w.get("en", "")).strip()
        if not en or en.lower() in known:
            continue
        out.append(w)
    return out


def bank_stats(data: dict) -> list[dict]:
    rows = []
    for key, meta in BANKS.items():
        bank = load_bank(key)
        total = len(bank.get("words", []))
        left = len(unused_words(bank, data))
        rows.append(
            {
                "key": key,
                "label": meta["label"],
                "total": total,
                "left": left,
                "done": total - left,
            }
        )
    return rows


def draw_words(key: str, data: dict, n: int = 5) -> list[tuple[str, str]]:
    bank = load_bank(key)
    unused = unused_words(bank, data)
    picked = unused[: max(0, n)]
    return [(w["en"], w["ko"]) for w in picked]
