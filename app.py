#!/usr/bin/env python3
"""
vocab — one-step active recall (Streamlit).

Open the page → auto: next-day → weekly fails → bank words → same-day.
Plain Streamlit UI (works on phone and PC). No custom visual design.
"""

from __future__ import annotations

import calendar as cal_mod
import json
from datetime import date, timedelta

import streamlit as st
import streamlit.components.v1 as components

from bank import BANKS, bank_stats, draw_words
from storage import (
    export_json,
    file_data_path,
    import_json,
    load_progress,
    persist_progress,
)
from vocab import (
    failed_queue,
    mark_result,
    next_day_queue,
    parse_batch,
    parse_date,
    stats,
    today,
    weekly_due,
)

# ---------------------------------------------------------------------------
# Page — plain Streamlit, larger controls only
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="vocab",
    page_icon="📘",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# Fluid spacing: scales with viewport (phone → tablet → PC)
st.markdown(
    """
<style>
  /* ---- Spacing tokens (fluid) ---- */
  :root {
    /* vertical rhythm between UI blocks */
    --space-1: clamp(0.35rem, 0.8vw + 0.2rem, 0.6rem);
    --space-2: clamp(0.55rem, 1.2vw + 0.3rem, 0.95rem);
    --space-3: clamp(0.75rem, 1.8vw + 0.35rem, 1.35rem);
    --space-4: clamp(1rem, 2.4vw + 0.4rem, 1.85rem);
    --space-5: clamp(1.25rem, 3vw + 0.5rem, 2.5rem);

    /* page chrome */
    --page-x: clamp(0.9rem, 4vw, 2.25rem);
    --page-y: clamp(1.35rem, 3.5vw, 2.75rem);
    --content-max: min(42rem, 100%);

    /* controls */
    --btn-h: clamp(3.1rem, 2vw + 2.6rem, 3.75rem);
    --btn-font: clamp(1.05rem, 0.35vw + 1rem, 1.25rem);
    --col-gap: clamp(0.55rem, 1.6vw + 0.25rem, 1.25rem);
    --stack-gap: var(--space-3);
  }

  /* Phone: more vertical room between tappable rows, tighter side padding */
  @media (max-width: 640px) {
    :root {
      --stack-gap: clamp(0.85rem, 3.2vw, 1.2rem);
      --col-gap: clamp(0.65rem, 3vw, 1rem);
      --btn-h: clamp(3.5rem, 10vw, 4rem);
      --btn-font: 1.2rem;
      --page-x: clamp(0.85rem, 4vw, 1.15rem);
      --page-y: clamp(0.75rem, 3vw, 1.1rem);
    }
  }

  /* Tablet */
  @media (min-width: 641px) and (max-width: 1024px) {
    :root {
      --stack-gap: clamp(0.8rem, 1.6vw, 1.25rem);
      --col-gap: 1rem;
      --btn-h: 3.4rem;
      --content-max: min(40rem, 100%);
    }
  }

  /* Desktop / large PC */
  @media (min-width: 1025px) {
    :root {
      --stack-gap: clamp(0.9rem, 1.1vw, 1.4rem);
      --col-gap: 1.15rem;
      --btn-h: 3.5rem;
      --btn-font: 1.2rem;
      --page-x: 2rem;
      --page-y: 2rem;
      --content-max: 42rem;
    }
  }

  /* Very short viewports (phone landscape): compress vertical rhythm */
  @media (max-height: 500px) {
    :root {
      --stack-gap: 0.55rem;
      --space-3: 0.55rem;
      --space-4: 0.7rem;
      --btn-h: 2.85rem;
      --page-y: 0.55rem;
    }
  }

  /* ---- Apply tokens to Streamlit layout ---- */
  .block-container {
    max-width: var(--content-max) !important;
    padding-top: var(--page-y) !important;
    padding-bottom: calc(var(--page-y) * 1.4) !important;
    padding-left: var(--page-x) !important;
    padding-right: var(--page-x) !important;
  }

  /* Main vertical stack: fluid gap between every element */
  div[data-testid="stVerticalBlock"] {
    gap: var(--stack-gap) !important;
  }

  /* Nested stacks slightly tighter so groups stay related */
  div[data-testid="stVerticalBlock"] div[data-testid="stVerticalBlock"] {
    gap: var(--space-2) !important;
  }

  /* Side-by-side columns (Got it / Missed) */
  div[data-testid="stHorizontalBlock"] {
    gap: var(--col-gap) !important;
    row-gap: var(--stack-gap) !important;
  }

  /* Buttons */
  .stButton {
    margin: 0 !important;
  }
  .stButton > button {
    width: 100%;
    min-height: var(--btn-h);
    font-size: var(--btn-font) !important;
    padding: 0.65rem 1rem !important;
    line-height: 1.2;
  }

  /* Headings: keep title readable; extra top space for "vocab" */
  h1, h2, h3,
  [data-testid="stMarkdownContainer"] h1,
  [data-testid="stMarkdownContainer"] h2,
  [data-testid="stMarkdownContainer"] h3 {
    padding-top: 0 !important;
    margin-bottom: var(--space-1) !important;
  }
  h1 {
    font-size: clamp(1.6rem, 1.2vw + 1.35rem, 2.1rem) !important;
    margin-top: 0.35rem !important;
    color: var(--text-color, inherit) !important;
  }
  h2, h3 {
    margin-top: 0 !important;
  }
  h2 { font-size: clamp(1.45rem, 1.5vw + 1.15rem, 2rem) !important; }
  h3 { font-size: clamp(1.2rem, 1vw + 1rem, 1.45rem) !important; }

  /* Caption / helper text closer to related controls */
  [data-testid="stCaptionContainer"] {
    margin-bottom: calc(var(--space-1) * -0.25) !important;
  }

  hr, [data-testid="stDivider"] {
    margin: var(--space-2) 0 !important;
  }

  /* Word cue block: fluid breathing room */
  .vocab-cue {
    margin: var(--space-3) 0 var(--space-2) 0;
    padding: var(--space-4) var(--space-2);
  }
  .vocab-cue h2 {
    text-align: center;
    margin: 0 !important;
    line-height: 1.25 !important;
    font-size: clamp(1.75rem, 4vw + 1rem, 2.6rem) !important;
    word-break: break-word;
  }
  .vocab-answer {
    text-align: center;
    margin: 0 0 var(--space-3) 0;
    font-size: clamp(1.2rem, 2vw + 0.9rem, 1.55rem);
    line-height: 1.4;
  }
  .vocab-cue h2,
  .vocab-answer {
    color: var(--text-color, inherit);
  }
  /* Study focus mode */
  .study-progress {
    text-align: center;
    font-size: 0.9rem;
    color: color-mix(in srgb, var(--text-color, currentColor) 55%, transparent);
    margin: 0.75rem 0 0;
  }

  /* Action row wrapper */
  .vocab-actions {
    margin-top: var(--space-3);
  }

  /* Expander / form controls spacing */
  .streamlit-expanderContent {
    padding-top: var(--space-2) !important;
  }
  .stTextArea textarea {
    min-height: clamp(6rem, 18vh, 10rem) !important;
  }

  /* ---- Calendar: theme-aware (light + dark) via Streamlit CSS vars ---- */
  .cal-shell {
    background: var(--secondary-background-color, transparent);
    border: 1px solid color-mix(in srgb, var(--text-color, currentColor) 16%, transparent);
    border-radius: 12px;
    padding: 0.55rem 0.45rem 0.65rem;
    margin: 0.15rem 0 0.35rem;
  }
  .cal-grid {
    display: grid !important;
    grid-template-columns: repeat(7, minmax(0, 1fr)) !important;
    gap: 0.28rem;
    width: 100%;
  }
  .cal-wd {
    text-align: center;
    font-size: 0.68rem;
    font-weight: 600;
    color: color-mix(in srgb, var(--text-color, currentColor) 55%, transparent);
    padding: 0.15rem 0;
  }
  .cal-cell {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-height: clamp(2.4rem, 10vw, 3.1rem);
    border-radius: 8px;
    border: 1px solid color-mix(in srgb, var(--text-color, currentColor) 18%, transparent);
    background: var(--background-color, transparent);
    color: var(--text-color, inherit);
    font-size: clamp(0.68rem, 2.6vw, 0.82rem);
    line-height: 1.15;
    box-sizing: border-box;
  }
  .cal-cell .n { font-weight: 650; font-size: 0.95em; }
  .cal-cell .m {
    font-size: 0.85em;
    color: color-mix(in srgb, var(--text-color, currentColor) 62%, transparent);
    margin-top: 0.12rem;
  }
  .cal-cell.pad {
    border: none;
    background: transparent;
  }
  .cal-cell.st-empty .m {
    color: color-mix(in srgb, var(--text-color, currentColor) 35%, transparent);
  }
  .cal-cell.st-todo {
    background: var(--background-color, transparent);
    border-color: color-mix(in srgb, var(--text-color, currentColor) 28%, transparent);
  }
  /* Status tints: mix accent into theme surface so both themes stay readable */
  .cal-cell.st-partial {
    background: color-mix(in srgb, #f59e0b 22%, var(--secondary-background-color, transparent));
    border-color: color-mix(in srgb, #f59e0b 55%, transparent);
  }
  .cal-cell.st-partial .m {
    color: color-mix(in srgb, #f59e0b 55%, var(--text-color, currentColor));
  }
  .cal-cell.st-done {
    background: color-mix(in srgb, #22c55e 20%, var(--secondary-background-color, transparent));
    border-color: color-mix(in srgb, #22c55e 50%, transparent);
  }
  .cal-cell.st-done .m {
    color: color-mix(in srgb, #22c55e 50%, var(--text-color, currentColor));
  }
  .cal-cell.st-fail {
    background: color-mix(in srgb, #ef4444 20%, var(--secondary-background-color, transparent));
    border-color: color-mix(in srgb, #ef4444 50%, transparent);
  }
  .cal-cell.st-fail .m {
    color: color-mix(in srgb, #ef4444 50%, var(--text-color, currentColor));
  }
  .cal-cell.selected {
    outline: 2px solid var(--primary-color, #3b82f6);
    outline-offset: 1px;
    border-color: var(--primary-color, #3b82f6) !important;
  }
  .cal-cell.today:not(.selected) {
    border-color: color-mix(in srgb, var(--primary-color, #3b82f6) 55%, transparent);
  }
  .cal-month-title {
    text-align: center;
    font-weight: 650;
    font-size: 1.05rem;
    padding: 0.55rem 0;
    color: var(--text-color, inherit);
  }
  .cal-legend {
    display: flex;
    flex-wrap: wrap;
    gap: 0.45rem 0.85rem;
    font-size: 0.75rem;
    color: color-mix(in srgb, var(--text-color, currentColor) 65%, transparent);
    margin: 0.45rem 0 0.1rem;
  }
  .cal-legend span::before {
    content: "";
    display: inline-block;
    width: 0.5rem;
    height: 0.5rem;
    border-radius: 50%;
    margin-right: 0.28rem;
    vertical-align: middle;
  }
  .cal-legend .lg-done::before { background: #22c55e; }
  .cal-legend .lg-partial::before { background: #f59e0b; }
  .cal-legend .lg-fail::before { background: #ef4444; }
  .cal-legend .lg-empty::before {
    background: color-mix(in srgb, var(--text-color, currentColor) 30%, transparent);
  }
  .cal-day-summary {
    font-size: 0.92rem;
    color: var(--text-color, inherit);
    margin: 0.35rem 0 0.1rem;
    line-height: 1.35;
  }
  /* Fallback when color-mix unsupported: still use theme text color */
  @supports not (color: color-mix(in srgb, red 50%, blue)) {
    .cal-month-title,
    .cal-day-summary,
    .cal-cell { color: var(--text-color, inherit); }
    .cal-wd,
    .cal-legend,
    .cal-cell .m { opacity: 0.75; }
  }
</style>
""",
    unsafe_allow_html=True,
)


DEFAULT_SETTINGS = {
    "bank": "absolute_beginner",
    "batch_size": 5,
}


def load_data() -> dict:
    data = load_progress(DEFAULT_SETTINGS)
    if data["settings"].get("bank") not in BANKS:
        data["settings"]["bank"] = "absolute_beginner"
    return data


def persist(data: dict) -> None:
    persist_progress(data)


def find_item(data: dict, item_id: int) -> dict | None:
    for it in data["items"]:
        if it["id"] == item_id:
            return it
    return None


def added_today(data: dict) -> bool:
    d = today().isoformat()
    return any(it.get("added") == d for it in data["items"])


def add_pairs(data: dict, pairs: list[tuple[str, str]], source: str | None = None) -> list[int]:
    d = today().isoformat()
    new_ids: list[int] = []
    known = {str(it.get("en", "")).lower() for it in data.get("items", [])}
    for en, ko in pairs:
        if not en or en.lower() in known:
            continue
        item = {
            "id": data["next_id"],
            "en": en,
            "ko": ko,
            "added": d,
            "same_day": None,
            "next_day": None,
            "failed": False,
            "last_reviewed": None,
        }
        if source:
            item["source"] = source
        data["next_id"] += 1
        data["items"].append(item)
        known.add(en.lower())
        new_ids.append(item["id"])
    if new_ids:
        persist(data)
    return new_ids


def init_session() -> None:
    ss = st.session_state
    if "booted" not in ss:
        ss.booted = False
    if "phase" not in ss:
        ss.phase = "boot"
    if "queue_ids" not in ss:
        ss.queue_ids = []
    if "idx" not in ss:
        ss.idx = 0
    if "revealed" not in ss:
        ss.revealed = False
    if "field" not in ss:
        ss.field = "next_day"
    if "label" not in ss:
        ss.label = ""
    if "weekly_ids" not in ss:
        ss.weekly_ids = []
    if "path" not in ss:
        ss.path = file_data_path()
    if "chain" not in ss:
        ss.chain = []
    if "selected_day" not in ss:
        ss.selected_day = today().isoformat()
    if "cal_month" not in ss:
        t = today()
        ss.cal_month = t.month
        ss.cal_year = t.year


def start_recall(ids: list[int], field: str, label: str, chain: list[str]) -> None:
    st.session_state.phase = "recall"
    st.session_state.queue_ids = list(ids)
    st.session_state.field = field
    st.session_state.label = label
    st.session_state.idx = 0
    st.session_state.revealed = False
    st.session_state.chain = list(chain)
    if field == "weekly":
        st.session_state.weekly_ids = list(ids)


def auto_start_new(data: dict, chain: list[str]) -> bool:
    settings = data["settings"]
    key = settings["bank"]
    n = int(settings["batch_size"])
    pairs = draw_words(key, data, n)
    if not pairs:
        for alt in BANKS:
            if alt == key:
                continue
            pairs = draw_words(alt, data, n)
            if pairs:
                key = alt
                break
    if not pairs:
        return False
    new_ids = add_pairs(data, pairs, source=key)
    if not new_ids:
        return False
    start_recall(new_ids, "same_day", "New words", chain)
    return True


def build_and_start(data: dict) -> None:
    d = today()
    nd = next_day_queue(data["items"], d)
    wk = failed_queue(data["items"]) if weekly_due(data, d) else []
    need_new = not added_today(data)

    if nd:
        after = []
        if wk:
            after.append("weekly")
        if need_new:
            after.append("new")
        after.append("done")
        start_recall([it["id"] for it in nd], "next_day", "Next-day review", after)
        return

    if wk:
        after = []
        if need_new:
            after.append("new")
        after.append("done")
        start_recall([it["id"] for it in wk], "weekly", "Weekly fails", after)
        return

    if need_new:
        if auto_start_new(data, ["done"]):
            return
        st.session_state.phase = "done"
        return

    st.session_state.phase = "done"


def advance_chain(data: dict) -> None:
    chain = list(st.session_state.chain)
    while chain:
        step = chain.pop(0)
        st.session_state.chain = chain
        if step == "weekly":
            fq = failed_queue(data["items"])
            if fq and weekly_due(data, today()):
                start_recall([it["id"] for it in fq], "weekly", "Weekly fails", chain)
                st.rerun()
                return
            continue
        if step == "new":
            if not added_today(data):
                if auto_start_new(data, chain if chain else ["done"]):
                    st.rerun()
                    return
            continue
        if step == "done":
            st.session_state.phase = "done"
            st.rerun()
            return
    st.session_state.phase = "done"
    st.rerun()


def day_activity(data: dict, d: date) -> dict:
    """Per-day word count and progress for items added on d."""
    key = d.isoformat()
    items = [it for it in data.get("items", []) if it.get("added") == key]
    n = len(items)
    same_done = sum(1 for it in items if it.get("same_day") is not None)
    same_pass = sum(1 for it in items if it.get("same_day") == "pass")
    next_done = sum(1 for it in items if it.get("next_day") is not None)
    next_pass = sum(1 for it in items if it.get("next_day") == "pass")
    fails = sum(1 for it in items if it.get("failed"))
    # Progress: weight same-day 50% + next-day 50% when words exist
    if n == 0:
        progress = 0.0
        status = "empty"
    else:
        progress = (same_done + next_done) / (2 * n)
        if fails:
            status = "fail"
        elif same_done >= n and next_done >= n:
            status = "done"
        elif same_done > 0 or next_done > 0:
            status = "partial"
        else:
            status = "todo"
    return {
        "count": n,
        "same_done": same_done,
        "same_pass": same_pass,
        "next_done": next_done,
        "next_pass": next_pass,
        "fails": fails,
        "progress": progress,
        "status": status,
        "items": items,
    }


def _status_marker(status: str) -> str:
    return {
        "done": "●",
        "partial": "◐",
        "fail": "!",
        "todo": "○",
        "empty": "·",
    }.get(status, "·")


def _calendar_grid_html(data: dict, year: int, month: int, selected: str) -> str:
    """Display-only 7-column CSS grid (no links — selection is via date_input)."""
    t = today()
    parts: list[str] = ['<div class="cal-shell"><div class="cal-grid">']
    for name in ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"):
        parts.append(f'<div class="cal-wd">{name}</div>')

    weeks = cal_mod.Calendar(firstweekday=0).monthdayscalendar(year, month)
    for week in weeks:
        for day_num in week:
            if day_num == 0:
                parts.append('<div class="cal-cell pad"></div>')
                continue
            d = date(year, month, day_num)
            iso = d.isoformat()
            act = day_activity(data, d)
            st_cls = f"st-{act['status']}"
            if iso == selected:
                st_cls += " selected"
            if d == t:
                st_cls += " today"
            marker = _status_marker(act["status"])
            meta = f"{marker} {act['count']}" if act["count"] else marker
            parts.append(
                f'<div class="cal-cell {st_cls}" title="{iso}: {act["count"]} words">'
                f'<span class="n">{day_num}</span>'
                f'<span class="m">{meta}</span></div>'
            )
    parts.append("</div></div>")
    return "".join(parts)


def render_calendar(data: dict) -> None:
    """Month calendar: visual grid + safe date picker (no iframe links)."""
    t = today()
    if "selected_day" not in st.session_state:
        st.session_state.selected_day = t.isoformat()
    try:
        sel = parse_date(st.session_state.selected_day)
    except Exception:
        sel = t
        st.session_state.selected_day = t.isoformat()

    # Month view follows the selected day (via date picker below)
    year = sel.year
    month = sel.month
    st.session_state.cal_year = year
    st.session_state.cal_month = month

    st.markdown(
        f"<div class='cal-month-title'>{cal_mod.month_name[month]} {year}</div>",
        unsafe_allow_html=True,
    )

    # Visual month (display only) — real CSS grid, works on mobile
    st.markdown(
        _calendar_grid_html(data, year, month, sel.isoformat()),
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="cal-legend">'
        '<span class="lg-done">done</span>'
        '<span class="lg-partial">in progress</span>'
        '<span class="lg-fail">has fails</span>'
        '<span class="lg-empty">no words</span>'
        "</div>",
        unsafe_allow_html=True,
    )

    # Safe day selection (native widget — no iframe / query-param crashes)
    if "cal_date_input" not in st.session_state:
        st.session_state.cal_date_input = sel
    picked = st.date_input(
        "Select day",
        min_value=date(2020, 1, 1),
        max_value=t + timedelta(days=365),
        format="YYYY-MM-DD",
        key="cal_date_input",
    )
    if isinstance(picked, date):
        iso = picked.isoformat()
        if iso != st.session_state.selected_day:
            st.session_state.selected_day = iso
            # Sync month title/grid when user picks another month via picker
            st.rerun()

    sel = parse_date(st.session_state.selected_day)
    act = day_activity(data, sel)
    # Day detail only when there are words (keeps top of screen free)
    if act["items"]:
        with st.expander(
            f"{sel.isoformat()} · {act['count']} words · "
            f"{int(round(act['progress'] * 100))}%",
            expanded=False,
        ):
            st.caption(
                f"same-day {act['same_done']}/{act['count']} · "
                f"next-day {act['next_done']}/{act['count']}"
                + (f" · fails {act['fails']}" if act["fails"] else "")
            )
            for it in act["items"]:
                flags = []
                if it.get("same_day"):
                    flags.append(f"same:{it['same_day']}")
                if it.get("next_day"):
                    flags.append(f"next:{it['next_day']}")
                if it.get("failed"):
                    flags.append("FAIL")
                flag = f" — {', '.join(flags)}" if flags else " — pending"
                st.write(f"**{it['en']}** · {it['ko']}{flag}")


def header_stats(data: dict) -> None:
    """Top chrome: calendar only (compact)."""
    render_calendar(data)


def play_pronunciation(text: str, *, key: str) -> None:
    """
    Hear the English word via the browser (Web Speech API).

    Speaker icon control; colors/fonts inherit from the host (no hardcoding).
    Speech starts on a direct tap inside this component (required on mobile).
    """
    word = (text or "").strip()
    if not word:
        return
    # key keeps each card’s widget identity stable across Streamlit reruns
    _ = key
    # SVG uses currentColor so it follows theme text color (light/dark)
    components.html(
        f"""
        <!DOCTYPE html>
        <html>
        <head>
          <meta charset="utf-8"/>
          <meta name="viewport" content="width=device-width, initial-scale=1"/>
          <style>
            /* No hardcoded theme colors/fonts — system + currentColor only */
            html, body {{
              margin: 0;
              padding: 0;
              background: transparent;
              color: CanvasText;
            }}
            .wrap {{
              display: flex;
              flex-direction: column;
              align-items: center;
              gap: 0.25rem;
            }}
            button#listen {{
              display: inline-flex;
              align-items: center;
              justify-content: center;
              min-width: 2.75rem;
              min-height: 2.75rem;
              padding: 0.5rem;
              margin: 0;
              border: none;
              border-radius: 999px;
              background: transparent;
              color: CanvasText;
              cursor: pointer;
              -webkit-tap-highlight-color: transparent;
              line-height: 0;
            }}
            button#listen:active {{ opacity: 0.65; }}
            button#listen svg {{
              width: 1.75rem;
              height: 1.75rem;
              display: block;
              fill: currentColor;
            }}
            #msg {{
              display: none;
              text-align: center;
              color: CanvasText;
              opacity: 0.8;
              margin: 0;
              font: inherit;
            }}
            #msg.show {{ display: block; }}
          </style>
        </head>
        <body>
          <div class="wrap">
            <button id="listen" type="button" aria-label="Listen to pronunciation" title="Listen">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" aria-hidden="true">
                <path d="M3 9v6h4l5 5V4L7 9H3zm13.5 3c0-1.77-1.02-3.29-2.5-4.03v8.05c1.48-.73 2.5-2.25 2.5-4.02zM14 3.23v2.06c2.89.86 5 3.54 5 6.71s-2.11 5.85-5 6.71v2.06c4.01-.91 7-4.49 7-8.77s-2.99-7.86-7-8.77z"/>
              </svg>
            </button>
            <p id="msg" hidden></p>
          </div>
          <script>
          (function () {{
            const text = {json.dumps(word)};
            const btn = document.getElementById("listen");
            const msg = document.getElementById("msg");

            function showErr(t) {{
              msg.hidden = false;
              msg.classList.add("show");
              msg.textContent = t;
            }}

            function pickVoice(synth) {{
              const voices = synth.getVoices() || [];
              return (
                voices.find(v => v.lang === "en-US") ||
                voices.find(v => v.lang === "en-GB") ||
                voices.find(v => (v.lang || "").toLowerCase().startsWith("en")) ||
                null
              );
            }}

            function speak() {{
              const synth = window.speechSynthesis;
              if (!synth) {{
                showErr("Speech not supported");
                return;
              }}
              try {{ synth.cancel(); }} catch (e) {{}}

              const u = new SpeechSynthesisUtterance(text);
              u.lang = "en-US";
              u.rate = 0.9;
              u.pitch = 1;
              const voice = pickVoice(synth);
              if (voice) {{
                u.voice = voice;
                u.lang = voice.lang || "en-US";
              }}
              setTimeout(function () {{
                try {{ synth.speak(u); }}
                catch (e) {{ showErr("Could not play"); }}
              }}, 60);
            }}

            if (window.speechSynthesis) {{
              window.speechSynthesis.getVoices();
              window.speechSynthesis.onvoiceschanged = function () {{
                window.speechSynthesis.getVoices();
              }};
            }}

            btn.addEventListener("click", function (e) {{
              e.preventDefault();
              e.stopPropagation();
              msg.hidden = true;
              msg.classList.remove("show");
              speak();
            }}, {{ passive: false }});
          }})();
          </script>
        </body>
        </html>
        """,
        height=56,
    )


def show_recall(data: dict) -> None:
    """Focus mode: word card only — no calendar, title, or stats."""
    ids: list[int] = st.session_state.queue_ids
    idx: int = st.session_state.idx
    field: str = st.session_state.field
    n = len(ids)

    if n == 0 or idx >= n:
        if field == "weekly":
            for iid in st.session_state.weekly_ids:
                it = find_item(data, iid)
                if it and it.get("weekly") == "pass":
                    it["failed"] = False
            data["last_weekly"] = today().isoformat()
            persist(data)
            st.session_state.weekly_ids = []
        st.session_state.queue_ids = []
        st.session_state.idx = 0
        st.session_state.revealed = False
        advance_chain(data)
        return

    item = find_item(data, ids[idx])
    if not item:
        st.session_state.idx += 1
        st.session_state.revealed = False
        st.rerun()
        return

    st.markdown(
        f'<p class="study-progress">{idx + 1} / {n}</p>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<div class="vocab-cue"><h2>{item["en"]}</h2></div>',
        unsafe_allow_html=True,
    )
    # Pronunciation first step: always available on the study card
    play_pronunciation(item["en"], key=f"listen_{field}_{idx}_{item['id']}")

    if not st.session_state.revealed:
        if st.button(
            "Reveal",
            type="primary",
            use_container_width=True,
            key=f"r_{field}_{idx}",
        ):
            st.session_state.revealed = True
            st.rerun()
        return

    st.markdown(
        f'<p class="vocab-answer">{item["ko"]}</p>',
        unsafe_allow_html=True,
    )
    c1, c2 = st.columns(2, gap="medium")
    with c1:
        if st.button(
            "Got it",
            type="primary",
            use_container_width=True,
            key=f"s_{field}_{idx}",
        ):
            mark_result(item, field, True)
            if field == "weekly":
                item["failed"] = False
            persist(data)
            st.session_state.idx += 1
            st.session_state.revealed = False
            st.rerun()
    with c2:
        if st.button(
            "Missed",
            use_container_width=True,
            key=f"f_{field}_{idx}",
        ):
            mark_result(item, field, False)
            persist(data)
            st.session_state.idx += 1
            st.session_state.revealed = False
            st.rerun()


def show_done(data: dict) -> None:
    st.title("vocab")
    header_stats(data)
    st.divider()
    st.header("Done for now")

    s = stats(data, today())
    b = bank_stats(data)
    left = sum(r["left"] for r in b)
    st.write(
        f"Added this week: **{s['added_this_week']}**  \n"
        f"Failed items: **{s['failed']}**  \n"
        f"Words left in banks: **{left}**"
    )

    n = int(data["settings"].get("batch_size", 5))
    # Defer study start to next run so this frame never paints calendar + cards together
    if st.button(f"Study {n} more words", type="primary", use_container_width=True):
        st.session_state.go_study_more = True
        st.rerun()

    with st.expander("Settings"):
        settings = data["settings"]
        labels = {k: BANKS[k]["label"] for k in BANKS}
        keys = list(BANKS.keys())
        cur = settings.get("bank", keys[0])
        i = keys.index(cur) if cur in keys else 0
        choice = st.selectbox(
            "Word bank",
            keys,
            index=i,
            format_func=lambda k: f"{labels[k]} ({next((r['left'] for r in b if r['key']==k), 0)} left)",
        )
        batch = st.slider("Words per day", 3, 5, int(settings.get("batch_size", 5)))
        if st.button("Save settings", use_container_width=True):
            data["settings"]["bank"] = choice
            data["settings"]["batch_size"] = batch
            persist(data)
            st.success("Saved.")

        st.write("Paste your own words (optional)")
        text = st.text_area(
            "Words",
            height=120,
            placeholder="word - 뜻\nword: 뜻",
            label_visibility="collapsed",
        )
        if st.button("Add pasted words", use_container_width=True):
            pairs = parse_batch(text or "")
            if not pairs:
                st.warning("Could not read any lines.")
            else:
                ids = add_pairs(data, pairs, source="manual")
                if ids:
                    start_recall(ids, "same_day", "New words", ["done"])
                    st.rerun()
                else:
                    st.warning("Those words are already saved.")

        st.caption(
            "Progress is saved in this browser (localStorage) and, when possible, "
            f"to a file: `{st.session_state.get('path') or file_data_path()}`"
        )
        st.download_button(
            "Download backup JSON",
            data=export_json(data),
            file_name="vocab-data.json",
            mime="application/json",
            use_container_width=True,
        )
        up = st.file_uploader("Restore backup JSON", type=["json"])
        if up is not None and st.button("Import backup", use_container_width=True):
            text = up.getvalue().decode("utf-8")
            restored = import_json(text, DEFAULT_SETTINGS)
            if restored is None:
                st.error("Invalid backup file.")
            else:
                persist(restored)
                st.session_state.booted = False
                st.session_state.phase = "boot"
                st.success("Backup restored.")
                st.rerun()


def main() -> None:
    init_session()
    data = load_data()

    # Start extra bank batch before any Done/calendar UI is drawn
    if st.session_state.pop("go_study_more", False):
        if not auto_start_new(data, ["done"]):
            st.session_state.phase = "done"
            st.warning("No words left in the banks.")

    if not st.session_state.booted:
        st.session_state.booted = True
        build_and_start(data)
        st.rerun()

    phase = st.session_state.phase
    if phase == "boot":
        build_and_start(data)
        st.rerun()
        return

    # Exclusive study path: never render calendar or Done chrome
    if phase == "recall":
        show_recall(data)
        return

    show_done(data)


if __name__ == "__main__":
    main()
