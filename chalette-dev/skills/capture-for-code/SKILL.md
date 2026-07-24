---
name: capture-for-code
description: "Capture a bug, feature idea, or new-skill idea for the Command Room build pipeline the moment you spot it — a one-minute capture that writes ONE file to the local intake queue and returns to the interrupted task. Capture only: no verification, no diagnosis, no spec-writing (that's triage-intake's job). Use when the operator says: 'capture this for code', 'log this for code', 'capture for code', 'hand this to code', 'bug for code', 'idea for code', 'skill idea for code', 'I want a skill that [X] — capture it', 'add to intake', 'log that in the intake', 'put this in the build queue', 'code handoff', 'that's a bug — log it for the pipeline'. DOES NOT fire on customer-inbound bug reports or the customer-facing report-bug flow. DOES NOT fire on 'bug from [name]' or 'bug intake' — that's process-bug-report. DOES NOT fire on bare 'I think there's a bug in X' with no capture verb — that's an investigation; fire only when the operator asks to log/capture it (including right after such an investigation)."
---

# capture-for-code

The capture half of the intake pair. Sibling of `triage-intake`. Structured capture where the observation happens; verification later, where the codebase is open.

> **Operator-aware.** Read `config/operator.json`, then overlay `config/operator.local.json` per-key if present (gitignored; the operator's local overlay — only M has one). The queue root is the merged `intake_root` (default `~/cr-intake`). Create `new/`, `needs-input/`, `speced/`, `done/`, `killed/`, `specs/` plus a one-line README on first capture if missing.
> ```python
> import json, os
> op = {}
> for _n in ("operator.json", "operator.local.json"):
>     _p = os.path.join(SKILL_PLUGIN_ROOT, "config", _n)
>     if os.path.exists(_p): op.update(json.load(open(_p)))
> ```

## What this is and is not

**Is:** a ≤1-minute interrupt that freezes what you just observed — the exact trigger phrase, the offending output, which skill fired — into one structured file in `<intake_root>/new/`, then hands the conversation straight back to whatever you were doing.

**Is not:** a verifier, triager, or spec-writer. Anything beyond capture without the repo open is fabrication risk. Not the customer bug channel either — this pipe is for the **operator's own** findings while developing or testing Command Room.

## Behavior

### Step 1 — Classify (silently)

Three types, three templates (see `references/capture-templates.md`): **bug** (something misbehaved just now), **idea** (improvement to something that exists), **skill** (a new skill that doesn't exist). Ambiguous between idea and skill → pick `idea`; triage sorts it out. Never ask the operator to classify.

### Step 2 — Auto-collect context (silently, before asking anything)

Grab what is free to see in the current session: the skill that produced the problem (or nearest-related skill), the exact trigger phrase verbatim, the offending output pasted in (widget: describe what rendered + visible row text), the file being worked on. This context evaporates by the next session — capturing it now is the whole point.

### Step 3 — Clarify (bugs only, max 2 questions)

Only if the item is a **bug** AND the repro isn't already clear: ask at most **two** questions in one message — typically *"What did you expect instead?"* and/or *"Once or every time?"*. Infer severity, never ask it. Ideas/skills: ask nothing.

### Step 4 — Duplicate check (cheap, 10 seconds)

List filenames in `<intake_root>/new/`, `needs-input/`, and `speced/`. Obvious match → say so in one line. **Append only to matches in `new/`** — offer a dated note on the existing file instead of a twin. For a match in `needs-input/` or `speced/` (triage owns those folders — the single-writer rule forbids editing them here), do NOT append: write a fresh file in `new/` whose body points at the existing item ID (e.g. "recurrence of BUG_…; see speced/…"). Filename match only, no deep-dive.

### Step 5 — Write the file

Path: `<intake_root>/new/<TYPE>_<YYYY-MM-DD>_<slug>.md` (TYPE ∈ BUG/IDEA/SKILL; slug = 2-4 lowercase hyphenated words). Use the matching template from `references/capture-templates.md` exactly. Non-negotiables:

- The operator's description goes in **near-verbatim** — don't paraphrase away their phrasing.
- Bugs: **expected vs actual as separate fields**, plus repro (the exact trigger phrase counts).
- Any root-cause guess — theirs or yours — goes ONLY under `## Hypothesis (UNVERIFIED)`. Observed behavior and speculated cause never mix.
- Ideas: fill `impact` and `confidence` (1-5); leave `ease` as `?` — only triage (repo open) scores ease.
- **Names discipline (operator-scoped, INTAKE1 F7):** if the merged profile's `allowed_targets` does **not** include `"real"` (contractor/synthetic operator), use **placeholder names only** in every field — never real client/customer names (the org-name leak rule applies to intake files like everything else). An operator whose profile grants `"real"` (M) is capturing findings about their own real workspace and MAY record the real context needed to triage — those files live only on that operator's machine and never ship in the plugin.
- No placeholder text; a section with nothing real gets `(none)`.

### Step 6 — Confirm and return (one line)

> *Captured → `~/cr-intake/new/BUG_2026-07-23_confirm-row-dupe.md`. Triage it next session with "triage intake". — Now, back to [the interrupted task].*

Then actually resume the interrupted task.

## Writer contract

- Writes ONLY into `<intake_root>/new/` (single-writer rule — triage owns all moves out of `new/`).
- Never writes substrate events, never touches any workspace `_hq/data/`.
- Never emails anyone.
