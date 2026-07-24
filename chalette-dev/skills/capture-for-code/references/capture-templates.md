# Capture templates — one per type

Copy the matching template exactly. Frontmatter stays minimal — the folder is the status; never add a status field.

---

## BUG — `BUG_<YYYY-MM-DD>_<slug>.md`

```markdown
---
id: BUG_2026-07-23_confirm-row-dupe
type: bug
captured: 2026-07-23
source: capture
severity: blocks-me | annoying | cosmetic
skill: command-room:show-my-list        # the skill that misbehaved, if known; else (unknown)
---

## What happened (operator's words, near-verbatim)
(...)

## Expected
(...)

## Actual
(...)

## Repro
- Exact trigger phrase fired: "..."
- Once or every time: (...)
- Starting state that matters, if known: (...)

## Offending output (pasted)
(paste the bad output / widget row text here, or "(not capturable)")

## Hypothesis (UNVERIFIED)
(the operator's or the session's root-cause guess — a lead for triage, not a fact. "(none)" if no guess.)
```

---

## IDEA — `IDEA_<YYYY-MM-DD>_<slug>.md`

```markdown
---
id: IDEA_2026-07-23_weekly-digest-tiles
type: idea
captured: 2026-07-23
source: capture
impact: 3        # 1-5, capture-time read
confidence: 2    # 1-5, how sure the operator seems that this is worth it
ease: ?          # Code fills this at triage — capture never scores ease
---

## What I want (operator's words, near-verbatim)
(...)

## Trigger moment
(what was happening when the idea landed — the concrete situation it would have helped)

## Nearest existing skill / surface
(e.g. "this feels like weekly-recap plus charts" — best guess, triage verifies)

## Hypothesis (UNVERIFIED)
(any guess about how it might work — "(none)" is fine)
```

---

## SKILL — `SKILL_<YYYY-MM-DD>_<slug>.md`

```markdown
---
id: SKILL_2026-07-23_travel-prep
type: skill
captured: 2026-07-23
source: capture
impact: 3
confidence: 2
ease: ?
---

## The skill I want (operator's words, near-verbatim)
(...)

## When it should fire
(the trigger moments / example phrases M imagines saying)

## What it should produce
(the output M pictures — doc, widget, draft, action)

## Nearest existing skill
(closest current skill and why it doesn't cover this — triage verifies overlap)

## Hypothesis (UNVERIFIED)
("(none)" is fine)
```

---

## Appending to an existing item (duplicate found)

Add at the bottom of the existing file, never rewrite what's there:

```markdown

---
**Recurrence / addition — 2026-07-23 (capture):** (one paragraph: what happened this time / the new angle)
```
