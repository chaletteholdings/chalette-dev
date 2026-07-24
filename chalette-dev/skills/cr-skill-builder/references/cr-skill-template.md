---
title: CR SKILL.md Template (boilerplate cr-skill-builder Phase 5 renders from)
cr_plugin_version_min: 5.2.0
last_updated: 2026-07-23
---

# CR SKILL.md Template

Canonical skeleton for a new Command Room plugin skill. cr-skill-builder Phase 5 renders this with the captured values from Phases 1-3 substituted into `{{placeholders}}`.

Conforms to `command-room/references/SKILL_SHAPE_V2.md` — every CR skill that ships to a paying client MUST match this shape.

---

## Description doctrine (WI-3 / D2 — the single highest-leverage field)

The `description` is the ONLY field Cowork's router reads (body trigger tables are documentation, not routing — the description-only-routing gotcha). It is also under a hard budget (Gate 26). So it carries **triggers + boundaries and nothing else** — no workflow summary, no substrate-I/O recital, no gate inventory. Two measured reasons:
- A **directive** description ("ALWAYS use when…") outperforms a passive one by a wide, significant margin. Front-load the trigger stem into the first 250 chars (the listing-truncation window).
- Agents will **execute the description instead of reading the body** — a description that summarizes the workflow gets the workflow half-done from the description alone. So the description states WHEN to fire, never HOW the skill works.

**The formula:**

```
[capability, one clause]. ALWAYS use when the CEO says [trigger stems — front-loaded,
inside the first 250 chars]. Do not [handle the intent directly / route to a neighbor]
— use this skill. DOES NOT fire on [near-miss] — that's [neighbor, UNQUOTED].
```

Rules: third person; no `keywords` field (measured no-op); ≤980 chars (Gate 26); no angle brackets / version tags. The substrate-I/O summary that used to live in the description MOVES to the body's **Writer Contract** (it is workflow-summary risk + wasted trigger budget). Neighbor mentions inside `DOES NOT fire on` stay UNQUOTED (the quoting trap — a single-quoted neighbor phrase becomes a live negative trigger).

---

## Template body

```yaml
---
name: {{skill-name}}
description: "{{capability_one_clause}}. ALWAYS use when the CEO says {{front_loaded_trigger_stems}}. Do not {{direct_handling_or_neighbor_route}} — use this skill. {{does_not_fire_clauses_unquoted_neighbors}}."
metadata:
  version: {{skill_version}}
---

## Recommended Model

**Default: {{opus_or_sonnet}}.** {{model_reasoning}}

---

{{entity_resolve_section_if_name_bearing_triggers}}

## Skill Boundary (v2.1)

- **Use {{skill-name}} for:** {{single_sentence_scope}}.
- **Use `{{close_neighbor_1}}` for:** {{what_neighbor_1_does}}.
- **Use `{{close_neighbor_2}}` for:** {{what_neighbor_2_does}}.
{{additional_routing_guidance}}

{{voice_calibration_section_if_composer_skill}}

## Writer Contract

{{writes_to_section}}

{{passive_capture_reference_if_connector_touching}}

{{atomic_helper_enforcement_block}}

{{bash_preflight_gate_if_writer_helper_used}}

## What It Doesn't Do

- {{negative_1}}
- {{negative_2}}
- {{negative_3}}

{{rationalization_table_slot_if_discipline_skill}}

## How to Use

\`\`\`
{{trigger_phrase_examples}}
\`\`\`

{{optional_scope_modifiers}}

## How It Works

{{step0_todowrite_block_if_5plus_steps}}

{{phase_or_step_breakdown}}

{{first_run_questionnaire_block_if_applicable}}

## Output

{{output_surfaces}}

{{reliability_reference_if_scheduled}}
```

---

## Conditional block — Step 0 TodoWrite (skills with 5+ steps, WI-5 / D4)

Insert this as the FIRST step of any generated skill whose flow has 5 or more steps or hard gates. A Step-0 checklist eliminates silent step-skipping (measured: an 18-step flow went from silent skips to zero) — strong "BLOCKING" language alone does not; agents rationalize past MUSTs, but a visible checklist item they have to mark done resists that.

```markdown
### Step 0 — Build the checklist (do this first, before any other step)

Create a TodoWrite checklist of all {{N}} steps of this skill before starting. Mark a
step complete ONLY after its output actually exists (the file is written / the event is
appended / the gate returned a verdict) — never on intent. A step that is not in the
list cannot be silently skipped; a step marked done without its artifact is the failure
this checklist exists to catch.
```

---

## Conditional block — Rationalization table (discipline skills only, WI-5 / WI-6)

A "discipline skill" forbids something under pressure (don't auto-send, don't hand-roll the widget, don't skip the gate). For those, a bare prohibition is not enough — the agent talks itself past it. Pair each prohibition with the excuse it must survive. Seed the rows from the RED-baseline capture (Phase 1.5): the rationalizations the agent ACTUALLY produced when it failed the scenario without the skill.

```markdown
## Do not rationalize past these

| The rule | The excuse that will show up | Why the excuse is wrong |
|---|---|---|
| {{prohibition_1}} | {{observed_rationalization_1}} | {{why_wrong_1}} |
| {{prohibition_2}} | {{observed_rationalization_2}} | {{why_wrong_2}} |
```

Omit this block entirely for non-discipline skills (a pure report or lookup) — an empty rationalization table is noise.

---

## Body budget (WI-7)

The rendered SKILL.md persists in context all session; every line is recurring cost. Target < 500 lines / < ~5k tokens. If a section is rarely needed at fire time, move it to a `references/` file and cite it with a **conditional load trigger** ("Read `references/X.md` when [condition]"), not a generic "see references/". Keep gotchas in the SKILL.md body — the agent won't load a reference for a gotcha it hasn't hit yet.

---

## Placeholder fill rules

Each `{{placeholder}}` is filled from a Phase-1-to-3 answer OR computed from substrate:

### Frontmatter (per the description doctrine above — Gate 26 budget applies)

| Placeholder | Source |
|---|---|
| `{{skill-name}}` | Phase 1 — kebab-case, unique, matches folder name |
| `{{skill_version}}` | Phase 1 — semantic version under `metadata:` (never a top-level key; `quick_validate.py` allows only name/description/license/allowed-tools/metadata/compatibility) |
| `{{capability_one_clause}}` | Phase 1 — the outcome in ONE clause, lead with the win. NOT a workflow summary. |
| `{{front_loaded_trigger_stems}}` | Phase 1 — the trigger stems, front-loaded so at least one lands inside the first 250 chars |
| `{{direct_handling_or_neighbor_route}}` | Phase 1 — the alternative the agent would wrongly take ("handle the intent directly" / "route to `[neighbor]`") |
| `{{does_not_fire_clauses_unquoted_neighbors}}` | Phase 1 — near-miss negatives; neighbor mentions UNQUOTED (quoting trap) |

**Substrate I/O does NOT go in the description.** It moves to the body's Writer Contract. Connectors touched are stated in the body, not the description.

### Body sections

| Placeholder | Source |
|---|---|
| `{{opus_or_sonnet}}` | Default Opus; Sonnet allowed only if skill is mechanical (audit-style or simple lookup) |
| `{{model_reasoning}}` | One sentence why this model |
| `{{entity_resolve_section_if_name_bearing_triggers}}` | Empty if no name-bearing triggers; else insert the Entity-Resolve MUST-language block (see cr-contract-checklist Gate 4) |
| `{{single_sentence_scope}}` | Phase 1 outcome restated as "Use X for: …" |
| `{{close_neighbor_1}}`, `{{close_neighbor_2}}` | Phase 1 — the skills this one disambiguates from |
| `{{voice_calibration_section_if_composer_skill}}` | Empty for non-composers; for composers insert `shared/VOICE_CALIBRATION.md` "Composer Contract Header" block — MANDATORY for ship (Gate 14) |
| `{{writes_to_section}}` | Phase 2 — substrate writes list with new event types + new files |
| `{{passive_capture_reference_if_connector_touching}}` | Empty unless connector-touching; else reference `shared/PASSIVE_CAPTURE.md` |
| `{{atomic_helper_enforcement_block}}` | Standard block declaring atomic-write helper usage (see cr-substrate-helpers.md) |
| `{{bash_preflight_gate_if_writer_helper_used}}` | Standard Bash gate per `people-crm/SKILL.md` v3.2+ pattern |
| `{{negative_1}}`, `{{negative_2}}`, `{{negative_3}}` | Phase 1 — what the skill explicitly does NOT do |
| `{{rationalization_table_slot_if_discipline_skill}}` | Empty unless the skill forbids something under pressure; else the rationalization table seeded from Phase 1.5 RED-baseline (see conditional block above) |
| `{{trigger_phrase_examples}}` | Phase 1 trigger phrases, rendered as code block |
| `{{step0_todowrite_block_if_5plus_steps}}` | Empty for <5-step skills; else the Step-0 TodoWrite block (see conditional block above) |
| `{{phase_or_step_breakdown}}` | Phase 2 + 3 — the core logic, numbered steps |
| `{{first_run_questionnaire_block_if_applicable}}` | Phase 3 — questions, defaults, config storage. Empty if no first-run config |
| `{{output_surfaces}}` | Phase 2 — what the skill emits (markdown / widget / file / event) |
| `{{reliability_reference_if_scheduled}}` | Empty unless scheduled-task skill; else reference `shared/RELIABILITY.md` |

---

## Required sections matrix

| Section | When required | Source spec |
|---|---|---|
| Frontmatter | Always | SKILL_SHAPE_V2 Section "Required Frontmatter" |
| Recommended Model | Always | This template |
| Entity-Resolve enforcement | If name-bearing triggers (Gate 4) | cr-contract-checklist Gate 4 |
| Skill Boundary (v2.1) | Always | SKILL_SHAPE_V2 Section "Required Sections > Skill Boundary" |
| Voice Calibration | Composer skills (Gate 14) | shared/VOICE_CALIBRATION.md + Gate 14 |
| Writer Contract | If skill writes any file | SKILL_SHAPE_V2 Section "Required Sections > Writer Contract" |
| Passive-capture reference | If connector-touching | shared/PASSIVE_CAPTURE.md |
| Atomic-helper enforcement | If skill writes substrate | cr-substrate-helpers.md + Gate 3 |
| Bash preflight gate | If skill uses writer helper | people-crm v3.2+ pattern |
| What It Doesn't Do | Always | SKILL_SHAPE_V2 Section "Required Sections" |
| Rationalization table | Discipline skills (forbid something under pressure) | WI-5 / WI-6 conditional block above |
| How to Use | Always | Standard |
| Step 0 TodoWrite | Skills with 5+ steps/gates (Gate via WI-5) | WI-5 conditional block above |
| How It Works | Always | Standard |
| First-run questionnaire block | If config-aware skill (Gate 10) | cr-first-run-template.md |
| Output | Always | Standard |
| Reliability reference | If scheduled-task skill | shared/RELIABILITY.md |

---

## Example rendered skeleton (annotated)

For a hypothetical `widget-helper` skill that reads commitments and writes a `widget_rendered` event:

```yaml
---
name: widget-helper
description: "Wrap a set of items in the canonical action-set widget. ALWAYS use when an orchestrator says render widget for these items, show widget, or wrap these in a widget. Do not hand-compose widget markup — use this skill. DOES NOT fire on user-facing intent triggers (those go to the skill that produces the items first). DOES NOT fire on show me my list — that's show-my-list, which calls this skill internally."
metadata:
  version: 1.0.0
---

## Recommended Model

**Default: Sonnet.** Mechanical rendering; design is settled.

---

## Skill Boundary (v2.1)

- **Use widget-helper for:** wrapping a set of items in the canonical action widget for chat surfaces.
- **Use `show-my-list` for:** the user-facing "show me my list" intent — show-my-list assembles items and calls widget-helper to render.
- **Use `chat_output_renderer` directly:** for non-action surfaces (briefs, summaries, single docs).

## Writer Contract

- **Writes to events.jsonl:** `widget_rendered` event with widget_id, item_count, action_set.
- **Atomic-write enforcement:** uses `atomic_append_jsonl` per cr-substrate-helpers.md.

## What It Doesn't Do

- Does NOT decide what items to render — that's the caller's job.
- Does NOT modify items — pass-through renderer only.
- Does NOT handle action apply — that's apply-choices.

## How to Use

Called internally by other skills. Not user-facing.

## How It Works

[steps here]
```

(This example is illustrative — not an actual skill in the plugin.)

---

## Quality gates this template ensures

By following the template strictly, the resulting SKILL.md automatically passes:
- Gate 6 — uses canonical placeholders, no real names
- Gate 7 — widget format + canonical verb set declared if action surface
- Gate 8 — H2 deliverable link declared if file output
- Gate 9 — no leak tokens in user-facing strings
- Gate 14 — Voice Calibration block present for composers
- Gate 17 — instruction-layer wiring (helper named in body) if it introduces a shared-code path
- Gate 20 — collision check via folder-name + trigger-phrase fields
- Gate 26 — description budget: the doctrine keeps the field ≤980 chars, angle-bracket-free, stem-front-loaded

The measured trigger eval (Gate 16) still runs against the drafted description; the template gets you a well-shaped description, not a proven one. Gates 1-5, 10, 11-13, 15, 16, 18, 19, 21-25, 27 require Phase 2-5 actions beyond just the template.
