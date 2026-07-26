# vocab — minimal active-recall English vocab

Local-first. One JSON file. No SRS, no accounts, no streaks.

**Daily goal:** under ~90 seconds after Duolingo; under ~60 seconds for next-day only.

## Deploy on Streamlit Community Cloud

1. Repo main file: **`app.py`**
2. Python dependencies: **`requirements.txt`**
3. [share.streamlit.io](https://share.streamlit.io) → **New app** → pick this repo → Main file path: `app.py` → Deploy

On Cloud, progress is **per browser session** (isolated users). For lasting personal data, run locally (`streamlit run app.py`) so files go to `~/.vocab/data.json`.

## Complete stack

| Piece | Role |
|-------|------|
| `app.py` | Streamlit UI (mobile-friendly cards, daily chain, banks) |
| `vocab.py` | Shared core + CLI |
| `bank.py` | Excel-derived word banks |
| `import_xlsx.py` | Rebuild banks from `.xlsx` |
| `data/banks/*.json` | Absolute Beginner (~1213) + High school (~51) |
| `~/.vocab/data.json` | Your active items + progress |

Two front-ends, **same data file** and same rules:

| Front-end | Start |
|-----------|--------|
| **Streamlit (browser)** | `run_app.cmd` or `py -3 -m streamlit run app.py` |
| **CLI** | `vocab.cmd` / `py -3 vocab.py` |

---

## Streamlit app (recommended daily path)

### Install once

```powershell
cd C:\Users\seong\.grok\bin\vocab-recall
py -3 -m pip install -r requirements.txt
```

### Start (one command)

```powershell
cd C:\Users\seong\.grok\bin\vocab-recall
py -3 -m streamlit run app.py
```

or double-click / run:

```text
C:\Users\seong\.grok\bin\vocab-recall\run_app.cmd
```

### One-step UX

**Open the page. That is the only step.**

No mode menu. No “Daily / Review / Add” choice. Auto path:

1. Next-day review (if any)
2. Weekly fails only (if due)
3. Auto-draw 3–5 words from your default bank → same-day recall
4. **Done**

Per card: English → think → **Reveal** → **Got it** / **Missed**.

Settings / Duolingo paste live under a collapsed panel on the Done screen only.

### Word banks (from Excel)

Imported lists live under `data/banks/` (not dumped into the daily queue):

| Bank | Source file | Words |
|------|-------------|------:|
| Absolute Beginner | `data/Absolute Beginner words.xlsx` | ~1213 |
| High school | `data/High school words.xlsx` | ~51 |

In the app, choose a bank and take **3–5 words/day** → same-day recall. Already-studied English words are skipped.

Re-import after editing Excel:

```powershell
cd C:\Users\seong\.grok\bin\vocab-recall
py -3 import_xlsx.py
```

---

## CLI (optional)

```powershell
function vocab { py -3 "C:\Users\seong\.grok\bin\vocab-recall\vocab.py" @args }
```

Put that in your PowerShell profile (`notepad $PROFILE`) if you want the terminal version.

### After every Duolingo lesson (CLI)

```text
vocab
```

or:

```powershell
py -3 C:\Users\seong\.grok\bin\vocab-recall\vocab.py
# or
C:\Users\seong\.grok\bin\vocab-recall\vocab.cmd
```

---

## Data file

Shared by Streamlit and CLI (auto-created):

```
%USERPROFILE%\.vocab\data.json
```

Override: `setx VOCAB_DATA "D:\backup\vocab.json"`

What happens automatically (no mode choice):

1. **Next-day review** — yesterday’s words (or older if you skipped a day)
2. **Weekly fails** — only if ≥7 days since last weekly fail-pass *and* there are failed items
3. **Add 3–5 new words** — paste lines, blank line to finish → **immediate same-day recall**

Paste formats (one pair per line):

```text
ubiquitous - 어디에나 있는
ephemeral: 덧없는
resilient	회복력 있는
serendipity 우연한 발견
```

For each card:

1. You see the **English word only** (answer hidden)
2. Mentally produce the Korean meaning
3. Press **Enter** to reveal
4. Type **`s`** (got it) or **`f`** (missed)

Skip adding: at the add prompt, press Enter on an empty first line.

### Before a lesson only (reviews, no add)

```text
vocab review
```

### Other commands

| Command        | Purpose                          |
|----------------|----------------------------------|
| `vocab`        | Full daily loop (default)        |
| `vocab review` | Next-day + weekly if due         |
| `vocab add`    | Add words + same-day only        |
| `vocab stats`  | Counts (week adds, fails, queue) |
| `vocab list`   | Recent items                     |
| `vocab path`   | Print data file location         |

---

## The three-pass system (only)

| When        | What                         |
|-------------|------------------------------|
| Same day    | Right after you add words    |
| Next day    | Before / as you start the next session |
| Once / week | **Failed items only**        |

No other reviews. No Anki intervals.

**Skipped a day?** Next-day items stay in the queue until you run the tool. They do not vanish.

**Failed flag:** any `f` sets `failed: true`. Weekly session is the only place that clears a fail when you mark `s`.

---

## Data file format

Human-readable JSON. Copy the file anywhere to back up.

```json
{
  "version": 1,
  "last_weekly": "2026-07-20",
  "next_id": 12,
  "items": [
    {
      "id": 1,
      "en": "ubiquitous",
      "ko": "어디에나 있는",
      "added": "2026-07-25",
      "same_day": "pass",
      "next_day": "fail",
      "failed": true,
      "last_reviewed": "2026-07-26"
    }
  ]
}
```

| Field           | Meaning                                      |
|-----------------|----------------------------------------------|
| `en` / `ko`     | Cue and meaning                              |
| `added`         | ISO date added                               |
| `same_day`      | `pass` / `fail` / `null`                     |
| `next_day`      | `pass` / `fail` / `null` (null = not done)   |
| `failed`        | In weekly fail queue                         |
| `last_weekly`   | Last weekly fail session date (meta)         |

---

## Reminder (optional)

Windows Task Scheduler or phone alarm:

- **After Duolingo** → run `vocab`
- That’s the only habit to attach

No in-app notifications by design.

---

## Design rules (why it stays small)

- Active recall only — meaning never shown first
- Zero “what should I study?” decisions
- One local file, easy backup
- No gamification, points, or streaks
- No full SRS — same-day + next-day + weekly fails only
