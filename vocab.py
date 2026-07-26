#!/usr/bin/env python3
"""
Minimal English vocabulary active-recall tool.

One command does the right thing:
  1) next-day review (if any)
  2) weekly fail-only review (if due)
  3) add 3–5 new words + immediate same-day recall

Data: single JSON file (default ~/.vocab/data.json). No cloud, no SRS.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import date, timedelta
from pathlib import Path
from typing import Any

VERSION = 1
WEEKLY_INTERVAL_DAYS = 7
DEFAULT_DATA = Path.home() / ".vocab" / "data.json"


# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------

def today() -> date:
    return date.today()


def parse_date(s: str) -> date:
    return date.fromisoformat(s)


def ensure_data(path: Path) -> dict[str, Any]:
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        data = {"version": VERSION, "last_weekly": None, "next_id": 1, "items": []}
        save_data(path, data)
        return data
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    data.setdefault("version", VERSION)
    data.setdefault("last_weekly", None)
    data.setdefault("next_id", 1)
    data.setdefault("items", [])
    return data


def save_data(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")
    tmp.replace(path)


# ---------------------------------------------------------------------------
# Queues
# ---------------------------------------------------------------------------

def next_day_queue(items: list[dict], d: date) -> list[dict]:
    """Items added before today whose next-day recall is not done yet.
    Skipped days: still due (next_day is null and added < today).
    """
    out = []
    for it in items:
        if it.get("next_day") is not None:
            continue
        if it.get("same_day") is None:
            # never finished same-day; treat as due for next-day once past add day
            pass
        added = parse_date(it["added"])
        if added < d:
            out.append(it)
    return out


def weekly_due(data: dict, d: date) -> bool:
    failed = [it for it in data["items"] if it.get("failed")]
    if not failed:
        return False
    last = data.get("last_weekly")
    if last is None:
        # first weekly: due once any item is older than a week, or immediately if fails exist
        oldest_fail = min(parse_date(it["added"]) for it in failed)
        return (d - oldest_fail).days >= WEEKLY_INTERVAL_DAYS
    return (d - parse_date(last)).days >= WEEKLY_INTERVAL_DAYS


def failed_queue(items: list[dict]) -> list[dict]:
    return [it for it in items if it.get("failed")]


def week_bounds(d: date) -> tuple[date, date]:
    # Monday-start week
    start = d - timedelta(days=d.weekday())
    end = start + timedelta(days=6)
    return start, end


def stats(data: dict, d: date) -> dict[str, int]:
    start, end = week_bounds(d)
    added_week = sum(
        1 for it in data["items"] if start <= parse_date(it["added"]) <= end
    )
    failed = sum(1 for it in data["items"] if it.get("failed"))
    pending_next = len(next_day_queue(data["items"], d))
    return {
        "total": len(data["items"]),
        "added_this_week": added_week,
        "failed": failed,
        "pending_next_day": pending_next,
    }


# ---------------------------------------------------------------------------
# Parse batch input
# ---------------------------------------------------------------------------

def parse_word_line(line: str) -> tuple[str, str] | None:
    line = line.strip()
    if not line or line.startswith("#"):
        return None

    for sep in (" - ", " — ", " – ", "\t", " | ", ":", "｜"):
        if sep in line:
            left, right = line.split(sep, 1)
            en, ko = left.strip(), right.strip()
            if en and ko:
                return en, ko

    # "word, meaning" — only if single comma and both sides non-empty
    if "," in line:
        left, right = line.split(",", 1)
        en, ko = left.strip(), right.strip()
        if en and ko and " " not in en:
            return en, ko

    # last space split: "ubiquitous 어디에나 있는"
    parts = line.split(None, 1)
    if len(parts) == 2:
        return parts[0], parts[1]

    return None


def parse_batch(text: str) -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []
    for line in text.splitlines():
        p = parse_word_line(line)
        if p:
            pairs.append(p)
    return pairs


# ---------------------------------------------------------------------------
# I/O helpers
# ---------------------------------------------------------------------------

def out(msg: str = "") -> None:
    print(msg, flush=True)


def ask(prompt: str) -> str:
    try:
        return input(prompt).strip()
    except EOFError:
        return ""
    except KeyboardInterrupt:
        out("\n")
        sys.exit(0)


def clear_hint() -> None:
    # Do not clear screen (breaks some terminals / history). Just separate.
    out()


def mark_result(item: dict, field: str, ok: bool) -> None:
    item[field] = "pass" if ok else "fail"
    if not ok:
        item["failed"] = True
    item["last_reviewed"] = today().isoformat()


# ---------------------------------------------------------------------------
# Active recall (meaning from English; never show answer first)
# ---------------------------------------------------------------------------

def recall_session(
    items: list[dict],
    *,
    label: str,
    field: str,
    data: dict,
    path: Path,
    reverse: bool = False,
) -> None:
    """Active recall: show cue, user tries to produce answer, then mark s/f."""
    if not items:
        return

    n = len(items)
    out(f"--- {label} ({n}) ---")
    out("Think of the meaning, then Enter to reveal.  s = got it  f = missed")
    out()

    for i, it in enumerate(items, 1):
        cue = it["ko"] if reverse else it["en"]
        answer = it["en"] if reverse else it["ko"]
        out(f"[{i}/{n}]  {cue}")
        ask("  (Enter to reveal) ")
        out(f"  → {answer}")
        while True:
            m = ask("  [s]uccess / [f]ail: ").lower()
            if m in ("s", "y", "1", "ok", "p"):
                mark_result(it, field, True)
                if field == "weekly":
                    it["failed"] = False
                break
            if m in ("f", "n", "0", "x"):
                mark_result(it, field, False)
                break
            out("  type s or f")
        out()
        save_data(path, data)  # save after each item so quit mid-session is safe

    out(f"Done: {label}.")


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def cmd_run(data: dict, path: Path) -> None:
    """Zero-choice daily entry: next-day → weekly (if due) → add + same-day."""
    d = today()
    s = stats(data, d)
    out(f"vocab  |  week+{s['added_this_week']}  fail={s['failed']}  next={s['pending_next_day']}")
    out()

    # 1) Next-day
    nd = next_day_queue(data["items"], d)
    if nd:
        recall_session(nd, label="Next-day review", field="next_day", data=data, path=path)
        out()
    else:
        out("No next-day items.")
        out()

    # 2) Weekly fails
    if weekly_due(data, d):
        fq = failed_queue(data["items"])
        if fq:
            recall_session(fq, label="Weekly fails only", field="weekly", data=data, path=path)
            # clear failed on weekly pass (already handled in loop); stamp week
            for it in fq:
                if it.get("weekly") == "pass":
                    it["failed"] = False
            data["last_weekly"] = d.isoformat()
            save_data(path, data)
            out()
    else:
        last = data.get("last_weekly") or "never"
        out(f"Weekly fails: not due (last={last}).")
        out()

    # 3) Add new words
    out("Add new words from today's lesson (blank line to finish, or just Enter to skip).")
    out("Formats:  word - 뜻   |   word: 뜻   |   word<TAB>뜻")
    out()

    lines: list[str] = []
    while True:
        line = ask("> ")
        if line == "" and not lines:
            break
        if line == "":
            # blank after some lines ends batch
            break
        if line.lower() in ("done", "q", "."):
            break
        lines.append(line)

    if not lines:
        out("No new words. Done.")
        _print_stats(data, d)
        return

    pairs = parse_batch("\n".join(lines))
    if not pairs:
        out("Could not parse any lines. Try:  apple - 사과")
        return

    new_items: list[dict] = []
    for en, ko in pairs:
        item = {
            "id": data["next_id"],
            "en": en,
            "ko": ko,
            "added": d.isoformat(),
            "same_day": None,
            "next_day": None,
            "failed": False,
            "last_reviewed": None,
        }
        data["next_id"] += 1
        data["items"].append(item)
        new_items.append(item)
    save_data(path, data)
    out(f"Stored {len(new_items)} word(s). Same-day recall now.")
    out()
    recall_session(new_items, label="Same-day recall", field="same_day", data=data, path=path)
    _print_stats(data, d)


def cmd_add(data: dict, path: Path) -> None:
    """Only add + same-day (skip auto reviews)."""
    d = today()
    out("Paste words (blank line to finish).")
    lines: list[str] = []
    while True:
        line = ask("> ")
        if line == "":
            break
        if line.lower() in ("done", "q", "."):
            break
        lines.append(line)
    pairs = parse_batch("\n".join(lines))
    if not pairs:
        out("Nothing added.")
        return
    new_items = []
    for en, ko in pairs:
        item = {
            "id": data["next_id"],
            "en": en,
            "ko": ko,
            "added": d.isoformat(),
            "same_day": None,
            "next_day": None,
            "failed": False,
            "last_reviewed": None,
        }
        data["next_id"] += 1
        data["items"].append(item)
        new_items.append(item)
    save_data(path, data)
    out(f"Stored {len(new_items)}. Same-day recall:")
    out()
    recall_session(new_items, label="Same-day recall", field="same_day", data=data, path=path)


def cmd_review(data: dict, path: Path) -> None:
    """Only due reviews (next-day + weekly if due). No add."""
    d = today()
    nd = next_day_queue(data["items"], d)
    if nd:
        recall_session(nd, label="Next-day review", field="next_day", data=data, path=path)
    else:
        out("No next-day items.")

    if weekly_due(data, d):
        fq = failed_queue(data["items"])
        if fq:
            out()
            recall_session(fq, label="Weekly fails only", field="weekly", data=data, path=path)
            for it in fq:
                if it.get("weekly") == "pass":
                    it["failed"] = False
            data["last_weekly"] = d.isoformat()
            save_data(path, data)
    else:
        out("Weekly fails: not due.")
    _print_stats(data, d)


def _print_stats(data: dict, d: date) -> None:
    s = stats(data, d)
    out()
    out(
        f"stats  total={s['total']}  "
        f"added_this_week={s['added_this_week']}  "
        f"failed={s['failed']}  "
        f"pending_next_day={s['pending_next_day']}"
    )


def cmd_stats(data: dict, path: Path) -> None:
    _print_stats(data, today())
    out(f"data   {path}")


def cmd_list(data: dict, path: Path) -> None:
    d = today()
    items = data["items"]
    if not items:
        out("(empty)")
        return
    for it in items[-30:]:
        flags = []
        if it.get("failed"):
            flags.append("FAIL")
        if it.get("next_day") is None and parse_date(it["added"]) < d:
            flags.append("NEXT")
        flag = f" [{' '.join(flags)}]" if flags else ""
        out(f"  {it['id']:>3}  {it['added']}  {it['en']} — {it['ko']}{flag}")
    if len(items) > 30:
        out(f"  ... {len(items) - 30} older not shown")
    _print_stats(data, d)


def cmd_path(data: dict, path: Path) -> None:
    out(str(path.resolve()))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    # Force UTF-8 on Windows consoles when possible
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
            sys.stdin.reconfigure(encoding="utf-8")
        except Exception:
            pass

    p = argparse.ArgumentParser(
        prog="vocab",
        description="Minimal active-recall vocab (same-day + next-day + weekly fails).",
    )
    p.add_argument(
        "command",
        nargs="?",
        default="run",
        choices=["run", "add", "review", "stats", "list", "path", "help"],
        help="run (default) | add | review | stats | list | path",
    )
    p.add_argument(
        "--data",
        type=Path,
        default=Path(os.environ.get("VOCAB_DATA", DEFAULT_DATA)),
        help=f"JSON data file (default: {DEFAULT_DATA})",
    )
    args = p.parse_args(argv)

    if args.command == "help":
        p.print_help()
        out()
        out("Daily:  python vocab.py")
        out("  → next-day (if any) → weekly fails (if due) → add words + same-day")
        return 0

    path: Path = args.data
    data = ensure_data(path)

    cmds = {
        "run": cmd_run,
        "add": cmd_add,
        "review": cmd_review,
        "stats": cmd_stats,
        "list": cmd_list,
        "path": cmd_path,
    }
    cmds[args.command](data, path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
