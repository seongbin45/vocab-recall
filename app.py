#!/usr/bin/env python3
"""
vocab — one-step active recall (Streamlit).

Open the page → auto: next-day → weekly fails → bank words → same-day.
Plain Streamlit UI (works on phone and PC). No custom visual design.
"""

from __future__ import annotations

import streamlit as st

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
    --page-y: clamp(0.9rem, 2.8vw, 2.25rem);
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

  /* Headings: kill Streamlit default huge top padding; use fluid bottom */
  h1, h2, h3,
  [data-testid="stMarkdownContainer"] h1,
  [data-testid="stMarkdownContainer"] h2,
  [data-testid="stMarkdownContainer"] h3 {
    padding-top: 0 !important;
    margin-top: 0 !important;
    margin-bottom: var(--space-1) !important;
  }
  h1 { font-size: clamp(1.6rem, 1.2vw + 1.35rem, 2.1rem) !important; }
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
  .vocab-hint {
    text-align: center;
    color: #6b7280;
    margin: 0 0 var(--space-2) 0;
    font-size: clamp(0.95rem, 1vw + 0.8rem, 1.1rem);
  }

  /* Action row wrapper */
  .vocab-actions {
    margin-top: var(--space-3);
  }

  /* Narrow phone: stack Got it / Missed (full-width rows, fluid vertical gap) */
  @media (max-width: 420px) {
    div[data-testid="stHorizontalBlock"] {
      flex-direction: column !important;
      flex-wrap: nowrap !important;
      gap: var(--stack-gap) !important;
    }
    div[data-testid="stHorizontalBlock"] > div[data-testid="column"],
    div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"],
    div[data-testid="stHorizontalBlock"] > div {
      width: 100% !important;
      flex: 1 1 auto !important;
      min-width: 0 !important;
    }
  }

  /* Expander / form controls spacing */
  .streamlit-expanderContent {
    padding-top: var(--space-2) !important;
  }
  .stTextArea textarea {
    min-height: clamp(6rem, 18vh, 10rem) !important;
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


def header_stats(data: dict) -> None:
    s = stats(data, today())
    st.caption(
        f"week +{s['added_this_week']}  ·  fail {s['failed']}  ·  "
        f"next-day {s['pending_next_day']}  ·  total {s['total']}"
    )


def show_recall(data: dict) -> None:
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

    st.title("vocab")
    header_stats(data)
    st.write(f"**{st.session_state.label}** — {idx + 1} / {n}")
    st.divider()

    # Cue uses fluid padding via CSS class (not fixed rem design chrome)
    st.markdown(
        f'<div class="vocab-cue"><h2>{item["en"]}</h2></div>',
        unsafe_allow_html=True,
    )

    if not st.session_state.revealed:
        st.markdown(
            '<p class="vocab-hint">Think of the Korean meaning, then reveal.</p>',
            unsafe_allow_html=True,
        )
        st.markdown('<div class="vocab-actions"></div>', unsafe_allow_html=True)
        if st.button(
            "Reveal meaning",
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
    st.markdown('<div class="vocab-actions"></div>', unsafe_allow_html=True)
    # gap follows --col-gap; stacks to full width under 420px
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
    st.markdown('<div class="vocab-actions"></div>', unsafe_allow_html=True)
    if st.button(f"Study {n} more words", type="primary", use_container_width=True):
        if auto_start_new(data, ["done"]):
            st.rerun()
        else:
            st.warning("No words left in the banks.")

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

    if not st.session_state.booted:
        st.session_state.booted = True
        build_and_start(data)
        st.rerun()

    phase = st.session_state.phase
    if phase == "boot":
        build_and_start(data)
        st.rerun()
    elif phase == "recall":
        show_recall(data)
    else:
        show_done(data)


if __name__ == "__main__":
    main()
