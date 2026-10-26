# Generated Skill Template — v2.6

**Purpose:** Canonical template that `skill-generator` renders for every project-scoped skill. Every generated SKILL.md in `[WORKSPACE_ROOT]/_hq/skills/[project]/` is produced from this template.

**Read by:** `skill-generator` (during render), `regenerate-skill` (during diff/rebase), `weekly-audit` (validator).

**Do not edit generated SKILL.md files directly outside the User Customizations zone.** Edits outside the zone are detected by `regenerate-skill` and will trigger a merge prompt on next regen.

---

## Template Version

`template_version: 2.6.0` — bump when the template shape changes in a way that requires regeneration of all generated skills.

---

## Required Output Shape

Every generated SKILL.md MUST include:

1. Frontmatter with provenance
2. Skill Boundary (v2.1) section
3. Writer Contract section (paths only — skill only writes to project folder)
4. Generated Sections (Activation, Path Resolution, Workflow Routing, Key Contacts, Tool Stack, Context Sources, Preferences)
5. **Gotchas (starts empty — only accrued from real failures)**
6. User Customizations zone (delimited by HTML comment markers)
7. What It Doesn't Do section
8. Shadow file at `[WORKSPACE_ROOT]/_hq/skills/[project]/.generated/SKILL.md.current` (exact copy of generated body minus User Customizations zone)

---

## Template Skeleton

Below is the literal template that `skill-generator` fills in. Variables are in `{{double_braces}}`. Any section marked `OPTIONAL` is omitted if the corresponding input is empty.

```markdown
---
name: {{project_kebab_name}}
description: "{{generated_description}}"
template_version: 2.6.0
generated_at: {{timestamp}}
generator_version: {{skill_generator_version}}
source_files:
{{#each source_files}}
  - {{this}}
{{/each}}
connector_signals:
  calendar_last_30d: {{calendar_events_count}}
  gmail_last_30d: {{gmail_threads_count}}
  slack_last_30d: {{slack_messages_count}}
  granola_last_30d: {{granola_transcripts_count}}
  drive_folder_mtime: {{drive_folder_mtime}}
confirmed_by_user: {{confirmed_timestamp}}
domain_extension: {{domain_extension_name_or_none}}
---

## Skill Boundary (v2.1)

- **Use `{{project_kebab_name}}` for:** {{scope_statement_from_q2}}
- **Use `workspace-manager` for:** cross-project orchestration, new client creation, session lifecycle.
- **Pair pattern:** `{{project_kebab_name}}` loads project context. `workspace-manager` routes between projects. `meeting-notes` processes transcripts into this project's session notes.

## Writer Contract

Before writing to any workspace file, read `shared/WORKSPACE_API.md`.

**Primary writer for:**
- `[WORKSPACE_ROOT]/Claude/{{project_folder_name}}/SESSION_NOTES_{{project_upper_name}}.md` (append-only at end)
- `[WORKSPACE_ROOT]/Claude/{{project_folder_name}}/PROJECT_BRAIN.md` (update-in-place, sections 3–6)

**Appends to:**
- `[WORKSPACE_ROOT]/_hq/events.jsonl` (per PASSIVE_CAPTURE.md)

**Never writes to:**
- Any other project's folder
- `_hq/entities.json` (owned by `workspace-ingest` and `people-crm`)
- Plugin source

---

# {{project_display_name}}

**For:** {{audience_statement_from_q2}}

## Activation

This skill loads when:

- User says: {{#each trigger_phrases}}"{{this}}"{{#unless @last}}, {{/unless}}{{/each}}
- User drops a file into `[WORKSPACE_ROOT]/Claude/{{project_folder_name}}/`
- `workspace-manager` routes a message mentioning {{project_display_name}} or any of its counterparts: {{counterparts_list}}

**Two activation modes:**

**Full session** ("{{primary_trigger}}"):
1. Read `PROJECT_BRAIN.md` (compressed memory — always current)
2. Read tail of `SESSION_NOTES_{{project_upper_name}}.md` (last 2 sessions)
3. Read `PROJECT_CONTEXT.md` only if PROJECT_BRAIN points to it
4. Announce: "Loaded {{project_display_name}}. Last session: [date]. [1-sentence open item summary]. What are we doing?"

**Cold start** (task mention without "go" trigger):
1. Read PROJECT_BRAIN only
2. Load other files on-demand based on task

## Path Resolution

| Context | Path |
|---|---|
| Drive (this machine) | `{{drive_absolute_path}}` |
| Drive (other machines) | `[WORKSPACE_ROOT]/Claude/{{project_folder_name}}/` |
| Cowork / Claude Code session | `[WORKSPACE_ROOT]/Claude/{{project_folder_name}}/` |
| Generated skill source | `[WORKSPACE_ROOT]/_hq/skills/{{project_kebab_name}}/` |
| Synced skill runtime | `[WORKSPACE_ROOT]/.claude/skills/{{project_kebab_name}}/` |

All writes resolve under `[WORKSPACE_ROOT]`. Never hard-code the Drive absolute path at runtime.

## Workflow Routing

When the user says... | Read this file first | Then...
---|---|---
{{#each workflow_routes}}
"{{trigger}}" | `{{file}}` | {{action}}
{{/each}}

{{#if workflow_routes_empty}}
_No workflow routes learned yet. Insight-generator will populate this table over time as patterns emerge from session notes and connector events._
{{/if}}

## Key Contacts

| Name | Role | Relationship / Notes |
|---|---|---|
{{#each contacts}}
| {{name}} | {{role}} | {{notes}} |
{{/each}}

{{#if contacts_empty}}
_No contacts extracted from PROJECT_BRAIN. Update via next session or `people-crm` run._
{{/if}}

## Tool Stack

**Explicit tools for this project** (user-confirmed in Q5):

{{#each tool_stack}}
- **{{tool_name}}**: {{tool_purpose}}
{{/each}}

**Do not assume any tool not listed here.** If a workflow needs a tool that isn't in this stack, stop and ask.

## Context Sources

External sources that may contain signal for this project:

{{#each context_sources}}
- **{{source_type}}** ({{source_name}}): {{source_notes}}
{{/each}}

{{#if context_sources_empty}}
_No external sources declared. Add via next session or `context-ingestion` run._
{{/if}}

## Preferences

{{#each preferences}}
- {{this}}
{{/each}}

{{#if preferences_empty}}
_Preferences accrue from session notes. Default: follow `[WORKSPACE_ROOT]/CLAUDE.md` workspace-level rules._
{{/if}}

{{#if domain_extension}}
## Domain Extension: {{domain_extension_name}}

{{domain_extension_body}}

{{/if}}

## Gotchas

<!-- GOTCHAS_ZONE_START -->
<!-- This section is empty by default. Gotchas are appended ONLY when a real failure occurs and is logged. Do not synthesize or pre-fill based on domain. -->
<!-- Format for each gotcha:
- **[One-line symptom]**: [what to check/do]. Seen: [YYYY-MM-DD]. Root cause: [one line].
-->
<!-- GOTCHAS_ZONE_END -->

---

<!-- USER_CUSTOMIZATIONS_START -->
<!--
  Anything between these markers is preserved across regenerations.
  Add your own notes, overrides, or preferences here. `regenerate-skill`
  will carry this block forward verbatim when the template is updated.
-->

<!-- USER_CUSTOMIZATIONS_END -->

---

## What It Doesn't Do

- Does not route between projects — that's `workspace-manager`.
- Does not process meeting transcripts — that's `meeting-notes` (which appends to this project's session notes).
- Does not manage contacts or org tree — that's `people-crm`.
- Does not fire on ambiguous mentions of {{project_display_name}} without context — defers to `workspace-manager` for disambiguation.

```

---

## Variable Inputs (what skill-generator must supply)

| Variable | Source | Fallback if missing |
|---|---|---|
| `project_kebab_name` | folder name lowercased + hyphenated | prompt user |
| `project_display_name` | Q1 answer | folder name titlecased |
| `project_folder_name` | exact folder name on disk | required |
| `project_upper_name` | Q1 uppercased with underscores | derived |
| `generated_description` | Q2 + Q3 + Q4 composed into spec-compliant paragraph | LLM synth |
| `source_files` | glob of project folder .md files | [] |
| `connector_signals` | 30-day window query per connector | all 0s |
| `trigger_phrases` | Q1 answer (aliases list) | [project_display_name] |
| `primary_trigger` | first aliases entry prefixed with "go " | "go {{project_kebab_name}}" |
| `counterparts_list` | extracted from PROJECT_BRAIN § People table | "none" |
| `scope_statement_from_q2` | Q2 one-sentence answer | required |
| `audience_statement_from_q2` | Q2 one-sentence answer | required |
| `drive_absolute_path` | `[WORKSPACE_ROOT]` + `/Claude/` + folder_name | derived |
| `workflow_routes` | grep SESSION_NOTES for "Workflow Routing" patterns OR empty | empty with note |
| `contacts` | PROJECT_BRAIN § People table | empty with note |
| `tool_stack` | Q5 answer (tool_name + purpose per line) | ask |
| `context_sources` | PROJECT_BRAIN § Context Pointers | empty with note |
| `preferences` | PROJECT_BRAIN § Lessons + Decisions Log tags | empty with note |
| `domain_extension` | Q6 (optional, skip if not applicable) | none |
| `timestamp` | UTC ISO8601 | required |
| `skill_generator_version` | read from skill-generator SKILL.md frontmatter | required |

---

## Empty-Default Rule (CRITICAL)

**Gotchas default EMPTY. Tool Stack default EMPTY (ask user). Preferences default EMPTY.**

Rationale: Gate 1 synthetic test Case 3 (regulated healthcare) showed that template auto-fill of these sections based on folder-name inference produced hallucinated HIPAA-compliance claims that would have been dangerous in production. Empty defaults force the accrual path (real failures, real user confirmation) rather than synthesized plausibility.

Skill-generator MUST resist the urge to fill these from domain inference alone. If it has no source citation for a gotcha, it omits the gotcha.

---

## User Customizations Zone

Delimited by:

```
<!-- USER_CUSTOMIZATIONS_START -->
...
<!-- USER_CUSTOMIZATIONS_END -->
```

This zone is:
- Preserved verbatim by `regenerate-skill`
- The ONLY zone a user is expected to edit directly
- Copied forward even if the surrounding template changes shape

Any edit outside this zone is flagged by `regenerate-skill` as "non-zone edit" and prompted for merge review.

---

## Shadow File Convention

After generation, skill-generator writes:

- Primary: `[WORKSPACE_ROOT]/_hq/skills/[project]/SKILL.md`
- Shadow: `[WORKSPACE_ROOT]/_hq/skills/[project]/.generated/SKILL.md.current`

The shadow is an exact copy of the generated body MINUS the User Customizations zone (empty markers preserved).

`regenerate-skill` uses the shadow as the "what we last generated" reference point. Diffing `SKILL.md` against `SKILL.md.current` identifies:
- Non-zone edits (user edited outside the zone) — flagged
- Zone content (user edited inside the zone) — preserved
- Clean state (no user edits) — safe to overwrite

---

## Domain Extensions (Q6 — Optional)

If the project is in a regulated, creative, or international domain, Q6 activates a domain extension block that injects after Preferences. Extensions are keyed by one of:

- `regulated-healthcare` — HIPAA references, PHI handling, audit trail requirement
- `regulated-financial` — SEC/FINRA references, retention periods, MNPI handling
- `regulated-legal` — privilege considerations, work-product doctrine, retention
- `creative-agency` — client approvals, IP ownership, portfolio rights
- `international` — timezone normalization, locale, currency

Extensions are stored in `references/domain-extensions/[name].md` and loaded only when the user explicitly chooses one in Q6. Default = none.

If no extension matches the project's needs, the user can write their own block inside the User Customizations zone.

---

## Validation (run by weekly-audit)

For each generated SKILL.md in `_hq/skills/`:

1. Frontmatter includes `template_version`, `generated_at`, `source_files`, `confirmed_by_user`.
2. `<!-- USER_CUSTOMIZATIONS_START -->` and `<!-- USER_CUSTOMIZATIONS_END -->` markers present and balanced.
3. Shadow file exists at `.generated/SKILL.md.current`.
4. Gotchas section present but may be empty (this is allowed, unlike v2.1 handcrafted skills where empty gotchas was a warning).
5. All standard v2.1 validation rules still apply (Skill Boundary, Writer Contract, What It Doesn't Do, no customer-string literals in wrong places — generated skills ARE allowed to reference their own project name since they are project-scoped, not plugin-wide).

---

**End of generated skill template spec.**
