---
title: CR SKILL.md Template (boilerplate cr-skill-builder Phase 5 renders from)
cr_plugin_version_min: 3.13.8.3
last_updated: 2026-05-26
---

# CR SKILL.md Template

Canonical skeleton for a new Command Room plugin skill. cr-skill-builder Phase 5 renders this with the captured values from Phases 1-3 substituted into `{{placeholders}}`.

Conforms to `command-room/references/SKILL_SHAPE_V2.md` — every CR skill that ships to a paying client MUST match this shape.

---

## Template body

```yaml
---
name: {{skill-name}}
description: "{{outcome_sentence}}. {{what_it_reads_and_writes}}. {{connectors_used_if_any}}. Use when the CEO says {{trigger_phrases_quoted_list}}. {{does_not_fire_clauses}}."
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

## How to Use

\`\`\`
{{trigger_phrase_examples}}
\`\`\`

{{optional_scope_modifiers}}

## How It Works

{{phase_or_step_breakdown}}

{{first_run_questionnaire_block_if_applicable}}

## Output

{{output_surfaces}}

{{reliability_reference_if_scheduled}}
```

---

## Placeholder fill rules

Each `{{placeholder}}` is filled from a Phase-1-to-3 answer OR computed from substrate:

### Frontmatter

| Placeholder | Source |
|---|---|
| `{{skill-name}}` | Phase 1 — kebab-case, unique, matches folder name |
| `{{outcome_sentence}}` | Phase 1 — outcome the CEO gets, lead with the win |
| `{{what_it_reads_and_writes}}` | Phase 2 — substrate I/O summary |
| `{{connectors_used_if_any}}` | Phase 2 — Gmail / Calendar / Slack / Granola / QuickBooks / DocuSign / Canva, or omit if none |
| `{{trigger_phrases_quoted_list}}` | Phase 1 — natural-language phrases, single-quoted, comma-separated |
| `{{does_not_fire_clauses}}` | Phase 1 — negative triggers with UNQUOTED close-neighbor mentions to avoid the quoting trap |

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
| `{{trigger_phrase_examples}}` | Phase 1 trigger phrases, rendered as code block |
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
| How to Use | Always | Standard |
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
description: "Render action-set widgets for any chat surface that needs send/edit/draft/skip choices, using the canonical widget renderer. Reads pending commitments from events.jsonl to pre-populate action items. Writes a widget_rendered event per fire. Use when an orchestrator says 'render widget for these items', 'show widget', 'wrap these in a widget'. DOES NOT fire on user-facing intent triggers (those go to the skill that produces the items first). DOES NOT fire on 'show me my list' — that's show-my-list, which itself calls widget-helper internally."
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
- Gate 7 — widget format declared if action surface
- Gate 8 — H2 deliverable link declared if file output
- Gate 9 — no leak tokens in user-facing strings
- Gate 14 — Voice Calibration block present for composers
- Gate 20 — collision check via folder-name + trigger-phrase fields

Gates 1-5, 10, 11-13, 15-19 require Phase 2-5 actions beyond just the template.
