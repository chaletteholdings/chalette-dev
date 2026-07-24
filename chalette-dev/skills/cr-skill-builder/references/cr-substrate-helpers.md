---
title: Canonical Substrate Helpers — when to use which + quality-gate delegated tooling
cr_plugin_version_min: 5.2.0
last_updated: 2026-07-23
---

# Canonical Substrate Helpers

The ONLY blessed paths into the CR substrate. Bypassing them is the Bug #81 architectural-failure class — defensive helpers don't help callers who don't use them.

cr-skill-builder Gate 3 verifies every skill uses these helpers — not raw `open()` or `path.write_text()`. CI validator (Gate 3) re-verifies at PR time.

---

## events.jsonl writes

```python
from atomic_io import atomic_append_jsonl
atomic_append_jsonl(events_path, event)
```

**Helper:** `command-room/shared/scripts/atomic_io.py::atomic_append_jsonl`
**Why:** append-only + atomic write + post-write parse check. Bypass = Bug #81.

## entities.json writes (people, orgs, projects)

```python
import sys; sys.path.insert(0, 'shared/scripts')
from people_writer import create_person, update_person, find_existing_person, merge_person_into

# always dedup first
existing = find_existing_person(workspace_root, name=..., email=...)
if existing:
    update_person(existing["id"], ...)
else:
    create_person(...)
```

**Helper:** `command-room/shared/scripts/people_writer.py`
**Why:** schema validation + dedup + atomic write + writes person lifecycle events. Direct `entities.json` edits are FORBIDDEN per v3.2+ contract.

## Any JSON substrate file (aliases, okrs, one_on_ones, skill_config, etc.)

```python
from atomic_io import atomic_write_json
atomic_write_json(path, data)
```

**Helper:** `command-room/shared/scripts/atomic_io.py::atomic_write_json`
**Why:** atomic temp-file-then-rename + parse-back verification. Prevents truncated-file incidents.

## Reading commitment events (5 shape variants)

```python
from cru_match import _commitment_field, load_open_commitments

# canonical field access (handles all 5 shape variants)
owner_id = _commitment_field(event, "owner_id")
title = _commitment_field(event, "title")

# bulk load of open commitments
commitments = load_open_commitments(workspace_root, filter_by_person_id=None)
```

**Helper:** `command-room/shared/scripts/cru_match.py`
**Why:** 5 commitment shape variants exist in the wild. Hand-rolling reads = bugs.

## Entity resolution (name-bearing triggers)

```python
from entity_resolve import resolve_all
result = resolve_all(workspace_root, query)
# result.people, result.orgs, result.projects, result.confidence
```

**Helper:** `command-room/shared/scripts/entity_resolve.py`
**Why:** handles aliases, partial matches, multi-word names. v3.13.7 enforcement-gate canonical path.

## Live contact check (recency overlay)

```python
from live_contact_check import live_contact_check
last_contact_iso = live_contact_check(person_id, workspace_root)
```

**Helper:** `command-room/shared/scripts/live_contact_check.py`
**Why:** substrate cadence math gets stale; live Gmail/Calendar overlay prevents false-dormant flags. Required before any dormant/risk flag per v3.13.7+.

## File path output

```python
from brief_path import get_brief_path, get_brief_artifact_url

path = get_brief_path(workspace_root, filename)
url = get_brief_artifact_url(path)
```

**Helper:** `command-room/shared/scripts/brief_path.py`
**Why:** H2 link surface (Gate 8) + runtime-resolved `$WORKSPACE` (Gate 5) + native Windows path format (v3.13.0+).

## Chat output rendering

```python
from chat_output_renderer import render_chat_output_widget, doc_headline_link, doc_headline_link_h3

widget_html = render_chat_output_widget(items=..., actions=...)
link_md = doc_headline_link(label, url)        # H2 single-doc
link_md = doc_headline_link_h3(label, url)     # H3 multi-doc
```

**Helper:** `command-room/shared/scripts/chat_output_renderer.py`
**Why:** leak scanner (Gate 9) + canonical action set + voice-tone enforcement.

## Skill config (first-run questionnaire)

```python
from skill_config_writer import load_skill_config, save_skill_config, wipe_skill_config

config = load_skill_config(workspace_root, skill_name)
if config is None:
    # run questionnaire, gather answers
    save_skill_config(workspace_root, skill_name, config_dict, schema_version=1)
```

**Helper:** `command-room/shared/scripts/skill_config_writer.py` (shipped — no longer "to be added"; exposes `load_skill_config` / `save_skill_config` / `wipe_skill_config`)
**Why:** 5-question cap + schema validation + atomic write + emits `skill_first_run_configured` event.

---

## Forbidden patterns (Gate 3 + CI validator catch)

| Forbidden | Replacement |
|---|---|
| `with open(events_path, "a") as f: f.write(...)` | `atomic_append_jsonl(events_path, event)` |
| `path.write_text(json.dumps(...))` | `atomic_write_json(path, data)` |
| `json.load(open(entities_path))` + manual edit + write | `people_writer.update_person(...)` |
| Hand-rolled commitment field access (`ev["data"]["owner_id"]`) | `_commitment_field(ev, "owner_id")` |
| Literal `C:\Users\<name>\Desktop\...` in chat output | `get_brief_artifact_url(path)` |
| Markdown numbered actions (`▸ send 1 ▸ draft 1`) | `render_chat_output_widget(...)` |

---

## Quality-gate delegated tooling (the chalette skills cr-skill-builder invokes for Tier B)

cr-skill-builder delegates Tier B runtime/eval gates to these existing chalette skills. They are NOT substrate helpers — they are canonical quality-gate tooling that cr-skill-builder MUST invoke for the relevant gates.

### Voice Calibration (Gate 14 — composer skills)

```
Invoke: chalette-dev:voice-test
Input:  sample drafts from the new composer skill (≥3 representative outputs)
Output: score 0-100 per draft + weighted average + per-AI-tell breakdown
Threshold: ≥85 average for ship
           70-85 needs explicit M-acceptance with reason logged
           <70 AUTO-BLOCK (gap too wide to ship to paying customer)
```

**Why:** composer skills carry the operator's voice. Voice drift is the most visible failure mode customers notice.

### Eval Executor + Grader (Gate 15)

```
Invoke: chalette-dev:skill-creator (Executor + Grader sub-agents)
Input:  drafted SKILL.md + test prompts file (tests/eval_prompts_<skill>.json)
Output: per-prompt verdict (PASS/FAIL) + aggregate pass rate
Threshold: ≥90% pass rate
```

**Why:** catches skills that technically work but produce inferior outputs vs intent. Per Anthropic skill-creator 2026 update.

### Description-improver (Gate 16)

```
Invoke: chalette-dev:skill-creator description-improver tool
Input:  drafted SKILL.md frontmatter description
Output: triggering accuracy score 0-1 + reword suggestions
Threshold: ≥0.85
```

**Why:** a vague description steals triggers from existing skills (cannibalization). Negative-trigger quoting trap (single-quoted phrases in "DOES NOT fire on" become negative triggers — clarifying mentions must be unquoted).

### Synthetic-workspace runtime exercise (Gate 13)

```
Invoke: chalette-dev:synthetic-workspace-runtime-test
Input:  --target=synthetic --skill=<new-skill-name>
Output: PASS / WARN / BLOCK verdict + runtime exception trace if any
Threshold: PASS only
```

**Why:** runtime catches bugs static can't. Per V3.13.8 §6 Principle 1.

### Bug-regression suite (Gate 18)

```
Invoke: chalette-dev:bug-regression-suite
Input:  --target=workspace (or --target=synthetic if fixtures available)
Output: baseline diff (PRE-drop vs POST-drop) + any newly-failing tests
Threshold: zero newly-failing tests
```

**Why:** adding skills sometimes breaks neighbors via trigger cannibalization or substrate-path collisions. Catches at verification time, not in production.

---

## Composer-skill detection logic (Gate 14 trigger)

cr-skill-builder auto-detects composer status from SKILL.md description. Any of these markers triggers composer-classification:

- "draft an email", "draft emails", "drafts email"
- "compose", "composes", "composer"
- "write a memo", "writes a memo", "memo composition"
- "draft a reply", "drafts a reply"
- "write in [name]'s voice", "draft in [name]'s voice"
- "follow-up draft", "outreach draft"
- "decision memo", "one-pager", "board pack"

When triggered, the SKILL.md MUST include the Voice Calibration block from `command-room/shared/VOICE_CALIBRATION.md` "Composer Contract Header" section, per `SKILL_SHAPE_V2.md` Section 2 requirement for composer skills.

---

## Path resolution patterns

For substrate file paths used in skill code:

```python
import os
# Resolve from the environment / operator config — never hardcode a machine path (Gate 9).
workspace_root = os.environ.get("WORKSPACE")
if not workspace_root:
    raise RuntimeError("WORKSPACE not set — resolve workspace_root from the runtime/operator config, never a literal path")
events_path = os.path.join(workspace_root, "_hq", "data", "events.jsonl")
entities_path = os.path.join(workspace_root, "_hq", "data", "entities.json")
```

NEVER hardcode an absolute path. NEVER copy a path from a docstring or example. Per Gate 5 + CONTRACT.md Rule 25.

For user-facing chat output:
- Use `get_brief_artifact_url(path)` to produce the H2 clickable link
- NEVER narrate the path as plain text ("saved to {path}")

---

## When a new helper should be added

If cr-skill-builder Phase 2 reveals a skill needs to write to a substrate file that has no canonical helper:

1. Flag in Phase 4 as WARN: "New substrate file `<path>` proposed; consider creating helper at `shared/scripts/<name>_writer.py`."
2. Phase 5 generates the helper stub using `atomic_write_json` internally + schema validation.
3. CI validator (Gate 3) enforces that all subsequent writes to that file go through the helper.

The principle from `feedback_defensive_helper_only_helps_users`: defensive helpers only protect callers who USE them. Once a helper exists, the contract is that bypassing it is an architectural violation, not just a stylistic choice.
