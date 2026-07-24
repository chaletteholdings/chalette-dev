---
name: skill-generator
description: "Generates a project-scoped skill for a specific client or workstream, so the CEO can say 'go [project]' and Claude loads the exact right context without hard-coding it in the plugin. Reads the project folder (PROJECT_BRAIN, PROJECT_CONTEXT, SESSION_NOTES), sweeps connectors for last-30-day signal, pre-fills a confirmation dialog, then renders a spec-compliant SKILL.md plus a shadow file for diff-based regeneration. Use when the CEO says 'generate a skill for [project]', 'make a skill for [client]', 'scaffold a skill for [workstream]', 'create the go-[name] skill', 'I need a skill for [project]', or drops a new project folder and wants it wired up. DOES NOT fire on 'create a skill' with no project scope — that's HQ-level skill-creator. DOES NOT fire on 'regenerate [project] skill' — that's `regenerate-skill`. Writes only to `[WORKSPACE_ROOT]/_hq/skills/[project]/`, never to plugin source or other projects' folders."
---

## Skill Boundary (v2.1)

- **Use `skill-generator` for:** producing a new project-scoped SKILL.md from workspace context, with a shadow file for future regeneration.
- **Use `regenerate-skill` for:** updating an existing generated skill when the template or project context changes.
- **Use `workspace-manager` for:** creating a new client folder scaffold (PROJECT_BRAIN, PROJECT_CONTEXT, SESSION_NOTES, SUBPROJECTS). `skill-generator` runs AFTER that scaffold exists.
- **Use HQ `skill-creator` for:** new plugin-level skills that ship with Command Room (not project-specific).
- **Pair pattern:** `workspace-manager` scaffolds the folder → `skill-generator` generates the skill → `regenerate-skill` keeps it fresh.

## Writer Contract

Before writing to any workspace file, read `shared/WORKSPACE_API.md`.

**Primary writer for:**
- `[WORKSPACE_ROOT]/_hq/skills/[project-kebab-name]/SKILL.md`
- `[WORKSPACE_ROOT]/_hq/skills/[project-kebab-name]/.generated/SKILL.md.current` (shadow file)
- `[WORKSPACE_ROOT]/_hq/skills/[project-kebab-name]/.generated/GENERATION_LOG.md` (provenance audit trail)

**Appends to:**
- `[WORKSPACE_ROOT]/_hq/events.jsonl` (one event per generation with type `skill.generated` and full provenance)

**Never writes to:**
- Any path outside `_hq/skills/[project-kebab-name]/`
- Plugin source at `plugin-source-v2/`
- The generated skill's project folder at `Claude/[Project]/` (that's owned by the project workflow)

**Reads only (no writes):**
- `[WORKSPACE_ROOT]/Claude/[Project]/PROJECT_BRAIN.md`
- `[WORKSPACE_ROOT]/Claude/[Project]/PROJECT_CONTEXT.md`
- `[WORKSPACE_ROOT]/Claude/[Project]/SESSION_NOTES_*.md`
- `[WORKSPACE_ROOT]/Claude/[Project]/SUBPROJECTS.md`
- `references/generated-skill-template.md`
- `references/SKILL_SHAPE_V2.md`
- Connectors per `shared/PASSIVE_CAPTURE.md`

---

# Skill Generator

**For:** CEOs whose projects have accumulated enough context (PROJECT_BRAIN + session history) that a pre-loaded "go [project]" skill would save 30 seconds per session, but who don't want to hand-craft each skill and don't want the plugin to ship with their project names baked in.

## What It Does

Takes a project folder path and produces a SKILL.md that, when triggered by "go [project]" or equivalent, loads the right context in 1 read instead of 5. The generated skill is workspace-local (lives under `_hq/skills/`, not in plugin source) so it's portable and private. A shadow file preserves the last generated state for diff-based regeneration.

## How It Works

### Phase 1 — Input Detection

Accept input as one of:

1. **Explicit project path:** `[WORKSPACE_ROOT]/Claude/Acme Property/` — user-provided, full path.
2. **Project name alone:** "Acme Property" — resolve via `list-active` skill output or workspace-manager's project registry.
3. **Folder-drop trigger:** a new folder appeared under `Claude/` and `workspace-manager` called us with the path.

If resolution fails, stop and ask: "I couldn't find a project folder matching that name. Should I look in `Claude/` or a different location?"

### Phase 2 — Context Harvest

Read in this order, stopping if any source is missing rather than assuming defaults:

1. `PROJECT_BRAIN.md` — primary source for contacts, facts, decisions, open questions, commitments, risks, lessons, glossary, context pointers.
2. `PROJECT_CONTEXT.md` — overview, architecture, margins, pricing, technical context.
3. `SUBPROJECTS.md` — property/workstream index.
4. Tail of `SESSION_NOTES_*.md` (last 3 sessions or last 2000 lines, whichever is smaller).
5. Any file named `HANDOFF_*.md` in the folder.

Extract into structured draft:
- `contacts[]` from PROJECT_BRAIN § People
- `tool_stack_hints[]` from PROJECT_CONTEXT § Technical Architecture
- `context_sources[]` from PROJECT_BRAIN § Context Pointers
- `preferences_hints[]` from PROJECT_BRAIN § Lessons + Decisions Log
- `counterparts[]` from PROJECT_BRAIN § People where role ≠ self

### Phase 3 — Connector Sweep

Query each connected MCP over the last 30 days, scoped to this project. Count and sample:

- **Calendar:** events where title or attendees match project aliases → `calendar_events_count`, top 5 event titles
- **Gmail:** threads where subject or participants match aliases → `gmail_threads_count`, top 5 subjects
- **Slack:** messages in channels matching project or from counterparts → `slack_messages_count`, top 5 channels
- **Granola:** meeting transcripts tagged or mentioning project → `granola_transcripts_count`, top 5 titles
- **Drive:** files modified in project folder → `drive_folder_mtime`, top 5 recently-modified files

These feed the provenance frontmatter and also inform the `trigger_phrases` heuristic (if Calendar has "Acme Property weekly" recurring, that's a strong trigger signal).

If a connector is unavailable, record `connector_name: unavailable` in provenance and continue. Never block on connector availability.

### Phase 4 — Pre-Fill The Five Questions

Draft answers using Phase 2 + Phase 3 signal. Do NOT skip the confirmation — the user reviews every answer before render.

**Q1 — Aliases & Trigger Phrases**
> "What do you actually say when you want to work on this? I've pulled these from your folder name, PROJECT_BRAIN, and last 30 days of activity. Confirm or edit:"
>
> Pre-filled with: folder name + any nicknames found in SESSION_NOTES + Calendar event title keywords. Always include "go [kebab-name]" and "end [kebab-name]" as defaults.

**Q2 — Scope & Audience**
> "In one sentence: what is this project, and who is it for?"
>
> Pre-filled from PROJECT_CONTEXT § Overview first sentence.

**Q3 — Activation Detail**
> "When you say the trigger, do you want a full session load (read everything, announce state, wait) or a lightweight task load (only pull context as needed)?"
>
> Pre-filled: "full session" if SESSION_NOTES exist and are recent; "task load" if folder is new.

**Q4 — Counterparts**
> "Confirm the people I should always load context on for this project. Edit if wrong:"
>
> Pre-filled from PROJECT_BRAIN § People (excluding self).

**Q5 — Tool Stack (CRITICAL — do not skip)**
> "What tools are you actually using on this project? List them. I won't assume any tool not listed here."
>
> Pre-filled from PROJECT_CONTEXT § Technical Architecture hints, but presented as a draft only. Force explicit user confirmation — this is the Gate 1 safety rule that prevents synthesis of plausible-but-wrong workflows.

**Q6 — Domain Extension (optional)**
> "Is this project in a regulated, creative, or international domain that needs extra rules? Choose one or skip:"
>
> Options: `regulated-healthcare`, `regulated-financial`, `regulated-legal`, `creative-agency`, `international`, `none`.
>
> Pre-filled based on keyword match against PROJECT_BRAIN content. If no strong match, default to `none` and do not prompt the user to reconsider — regulated defaults are dangerous.

### Phase 5 — Render

Read `references/generated-skill-template.md`. Substitute variables per the variable table in the template. Enforce:

- Frontmatter complete with all provenance fields.
- Gotchas section EMPTY (only the empty-markers comment block).
- Preferences section EMPTY if no strong signal from PROJECT_BRAIN § Lessons.
- Workflow Routing table EMPTY with the explanatory note if not enough SESSION_NOTES history to detect patterns.
- Tool Stack populated ONLY with user-confirmed tools from Q5.
- User Customizations zone present with empty markers.

Render to:
- Primary: `[WORKSPACE_ROOT]/_hq/skills/[project-kebab-name]/SKILL.md`
- Shadow: `[WORKSPACE_ROOT]/_hq/skills/[project-kebab-name]/.generated/SKILL.md.current` (same content minus User Customizations zone)

### Phase 6 — Log & Announce

Append to `[WORKSPACE_ROOT]/_hq/skills/[project-kebab-name]/.generated/GENERATION_LOG.md`:

```markdown
## Generation {{timestamp}}

- **Template version:** 2.6.0
- **Generator version:** 2.6.0
- **Source files read:** {{list}}
- **Connector signals:** Calendar={{n}}, Gmail={{n}}, Slack={{n}}, Granola={{n}}
- **Q1–Q6 answers:** {{summary}}
- **User-edited pre-fill answers:** {{list-of-changes}}
- **Domain extension:** {{name_or_none}}
- **Shadow written:** yes
```

Emit event to `events.jsonl`:

```json
{
  "type": "skill.generated",
  "project": "{{project-kebab-name}}",
  "template_version": "2.6.0",
  "generator_version": "2.6.0",
  "timestamp": "{{iso8601}}",
  "source_file_count": {{n}},
  "connector_signals": { ... },
  "user_edits_count": {{n}}
}
```

Announce to user in this exact shape:

```
Generated skill for {{project_display_name}}.

Location: [WORKSPACE_ROOT]/_hq/skills/{{kebab-name}}/SKILL.md
Shadow: .generated/SKILL.md.current (for future regeneration)

Syncs to runtime via sync-skills.ps1 — run that if you want this live now.

Next steps (optional):
- `regenerate-skill {{kebab-name}}` — if project context changes significantly
- Edit the User Customizations zone in the SKILL.md to add notes that survive regeneration
- Delete `.generated/SKILL.md.current` and re-run generator to force a clean regen
```

## How to Use

Trigger phrases:

- "Generate a skill for Acme Property"
- "Make a skill for NorthStar"
- "Scaffold a skill for the new Daniel project"
- "Create the go-uplift skill"
- "I need a skill for Command Room"

The skill always confirms the 5 (or 6) questions before rendering. It never silently writes.

## What You Get

- A workspace-local SKILL.md under `_hq/skills/[project]/`
- A shadow file for future diff-based regeneration
- A generation log entry for provenance
- An events.jsonl row for audit
- (After you run sync-skills) A live skill that fires on "go [project]"

The generated skill is on average 60–70% complete on first render. The remaining 30–40% accrues from:
- Real session notes (workflow routing patterns)
- Real failures (gotchas)
- Explicit preferences (user edits to User Customizations zone)

Do not try to make the first render 100%. It won't be and shouldn't be.

## Gotchas

- **Empty sections are correct, not a bug.** If workflow routing is empty on first render, that's because no patterns have been detected yet. Do not synthesize plausible routes from domain inference.
- **Tool Stack MUST be user-confirmed.** The Gate 1 Case 3 finding (HIPAA hallucination in healthcare) originated from inferring tools from folder name. Force Q5.
- **Generator versions must be monotonic.** If you try to regenerate with an older generator version, fail loud — downgrade paths are not supported.
- **Do not regenerate over user edits without going through `regenerate-skill`.** Direct re-run of skill-generator with no shadow check will blow away User Customizations zone. This skill detects an existing SKILL.md and routes to regenerate-skill automatically if found.
- **One project folder = one generated skill.** If a subproject grows large (per `subproject-graduation` skill), graduate it first, then run skill-generator against the new top-level folder.

## Connected Tools

- Reads from: Gmail, Calendar, Slack, Granola, Drive (all optional — degrades gracefully)
- Pair with: `workspace-manager` (creates folder), `regenerate-skill` (updates output), `insight-generator` (fills Gotchas + Workflow Routing over time), `weekly-audit` (validates output conforms to v2.6 shape)

## Scheduled Mode

Not scheduled. Generator runs only on explicit user request. Automated drift detection is `regenerate-skill`'s job (via weekly-audit integration).

## What It Doesn't Do

- Does not generate plugin-level skills (those go through HQ skill-creator).
- Does not modify the project folder itself — only writes to `_hq/skills/`.
- Does not activate or install the generated skill — user must run sync-skills.ps1 or restart Claude Code.
- Does not handle subproject-to-project promotion — that's `subproject-graduation`.
- Does not synthesize content from domain inference alone — empty beats wrong.
- Does not skip confirmation — the user reviews Q1–Q5 (and optionally Q6) before render, every time.
