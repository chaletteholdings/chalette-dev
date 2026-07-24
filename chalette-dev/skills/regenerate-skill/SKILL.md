---
name: regenerate-skill
description: "Regenerates an existing project-scoped skill when the template or project context changes, preserving the CEO's User Customizations zone verbatim and flagging any edits made outside the preserved zone for merge review. Reads the current SKILL.md and its shadow file, diffs them to detect non-zone edits, then re-runs skill-generator behind a preview-before-commit gate with 30-day rollback history. Use when the CEO says 'regenerate [project] skill', 'update the [project] skill', 'refresh the Acme Property skill', 'rebuild my NorthStar skill', 'my skill is stale', or when `weekly-audit` flags a skill as drifted. DOES NOT fire on 'generate a skill for [project]' — that's `skill-generator`. DOES NOT fire on 'delete the [project] skill' — that's a manual file operation the user should do themselves. Writes only to `[WORKSPACE_ROOT]/_hq/skills/[project]/` and keeps 30-day version history for rollback."
---

## Skill Boundary (v2.1)

- **Use `regenerate-skill` for:** updating an existing generated skill safely — preserving user customizations, flagging non-zone edits, keeping rollback history.
- **Use `skill-generator` for:** first-time generation when no SKILL.md exists for the project yet.
- **Use `weekly-audit` for:** detecting which skills need regeneration (it lists skills whose template_version is behind current or whose source files have changed significantly since last generation).
- **Pair pattern:** `weekly-audit` flags staleness → `regenerate-skill` updates → history preserved in `.generated/history/`.

## Writer Contract

Before writing to any workspace file, read `shared/WORKSPACE_API.md`.

**Primary writer for:**
- `[WORKSPACE_ROOT]/_hq/skills/[project-kebab-name]/SKILL.md` (rewrites)
- `[WORKSPACE_ROOT]/_hq/skills/[project-kebab-name]/.generated/SKILL.md.current` (updates shadow)
- `[WORKSPACE_ROOT]/_hq/skills/[project-kebab-name]/.generated/history/SKILL.md.YYYY-MM-DD-HHMMSS.md` (rollback snapshots)
- `[WORKSPACE_ROOT]/_hq/skills/[project-kebab-name]/.generated/GENERATION_LOG.md` (append regen entry)

**Appends to:**
- `[WORKSPACE_ROOT]/_hq/events.jsonl` (event type `skill.regenerated` with diff summary)

**Never writes to:**
- Any path outside `_hq/skills/[project-kebab-name]/`
- Plugin source
- The project's content folder at `Claude/[Project]/`

---

# Regenerate Skill

**For:** CEOs whose generated skills need to stay in sync with an evolving template and evolving project reality — without losing their personal customizations and without regenerating over edits they made on purpose.

## What It Does

Takes an existing generated skill and refreshes it, intelligently.

Three things stay safe:
1. **User Customizations zone** — carried forward verbatim.
2. **Prior versions** — last 30 days of SKILL.md snapshots kept for rollback.
3. **Non-zone edits** — detected and surfaced for merge, never silently overwritten.

Three things get updated:
1. **Template shape** — if the generator's template_version is ahead, sections reshape accordingly.
2. **Project context** — refreshed from current PROJECT_BRAIN, SESSION_NOTES, connectors.
3. **Provenance frontmatter** — new generated_at, new source_files list, new connector signals.

## How It Works

### Phase 1 — Detect Target

Accept project name or path. Resolve to `[WORKSPACE_ROOT]/_hq/skills/[project-kebab-name]/`. Verify:
- `SKILL.md` exists (if not, route to `skill-generator`)
- `.generated/SKILL.md.current` exists (if not, the skill was hand-crafted — ask user if they want to convert it to generated format; if yes, proceed but flag every section as "non-zone edit" since we have no baseline)

### Phase 2 — Read Three States

1. **Current SKILL.md** — what the user is actually using right now.
2. **Shadow (`.generated/SKILL.md.current`)** — what the generator produced last time.
3. **Fresh draft** — what the generator WOULD produce now with current template + current context (ask user to re-confirm Q1–Q6, pre-filled with answers from last GENERATION_LOG entry).

### Phase 3 — Diff Analysis

Compute three diffs:

**Diff A: Current vs Shadow**
- Any difference OUTSIDE the `<!-- USER_CUSTOMIZATIONS_START -->` / `<!-- USER_CUSTOMIZATIONS_END -->` markers is a **non-zone edit**. List these line-by-line.
- Any difference INSIDE the zone is a **customization** — expected, preserved.

**Diff B: Shadow vs Fresh Draft**
- This is the "template/context update" diff. Shows what would change if user had never edited.

**Diff C: Current vs Fresh Draft**
- What the user would actually see if we regenerated blindly. Highlights any conflicts where a non-zone edit would be lost.

### Phase 4 — Merge Preview

Render a preview showing:

```
Regeneration preview for {{project}}

Template version: {{old}} → {{new}}
Generator version: {{old}} → {{new}}
Source files changed: {{list}}
Connector signal delta: {{summary}}

CHANGES THAT WILL BE APPLIED (from template/context update):
{{Diff B summarized}}

USER CUSTOMIZATIONS PRESERVED:
{{content of User Customizations zone}}

⚠ NON-ZONE EDITS DETECTED (will be LOST unless you merge them):
{{Diff A non-zone portion}}

Options:
1. Apply update, preserve customizations zone, DISCARD non-zone edits
2. Apply update, preserve customizations zone, AUTO-MOVE non-zone edits into customizations zone
3. Show me each non-zone edit and let me decide per-change
4. Cancel regeneration — I need to fix the non-zone edits manually first
```

If Diff A shows zero non-zone edits, skip the warning block and just preview Diff B with "Apply / Cancel" options.

### Phase 5 — User Confirmation

Wait for user choice. Default is option 4 if non-zone edits exist (safe default — never lose data).

If user picks option 2, rewrite the generated template's User Customizations zone to include the non-zone edits wrapped in a `<!-- migrated from non-zone edit YYYY-MM-DD -->` comment block, positioned by their location in the original file (preserving reading order where possible).

### Phase 6 — Snapshot & Write

Before overwriting:

1. Copy current SKILL.md to `.generated/history/SKILL.md.{{iso-timestamp}}.md`
2. Prune history older than 30 days (keep most recent 10 regardless of age, for safety)

Then write:
- New SKILL.md (with merged customizations)
- New shadow `.generated/SKILL.md.current`
- Updated GENERATION_LOG.md entry

### Phase 7 — Log & Announce

Append to GENERATION_LOG.md:

```markdown
## Regeneration {{timestamp}}

- **Template version:** {{old}} → {{new}}
- **Generator version:** {{old}} → {{new}}
- **Diff A (non-zone edits detected):** {{count}} — action: {{user-choice}}
- **Diff B (template/context updates applied):** {{count}} changes across {{list-of-sections}}
- **User Customizations zone:** {{byte-count}} bytes, preserved
- **Snapshot saved:** .generated/history/SKILL.md.{{timestamp}}.md
- **History pruned:** {{n}} snapshots removed (older than 30 days)
```

Emit event:

```json
{
  "type": "skill.regenerated",
  "project": "{{project-kebab-name}}",
  "template_version_from": "{{old}}",
  "template_version_to": "{{new}}",
  "non_zone_edits_detected": {{n}},
  "merge_choice": "{{option}}",
  "timestamp": "{{iso8601}}"
}
```

Announce:

```
Regenerated {{project}} skill.

- Template: {{old}} → {{new}}
- Your customizations: preserved ({{n}} lines)
- Non-zone edits: {{handled_how}}
- Snapshot: .generated/history/SKILL.md.{{timestamp}}.md (rollback if needed)

Rollback command: `rollback [project] skill to {{timestamp}}`
```

### Rollback Path

If user says "rollback [project] skill" or "undo the last regen":
1. List last 10 snapshots from `.generated/history/`
2. Let user pick which to restore
3. Copy chosen snapshot back to `SKILL.md`
4. Regenerate shadow from that snapshot (shadow = current minus User Customizations zone)
5. Log event type `skill.rolled_back`

## How to Use

Trigger phrases:

- "Regenerate the Acme Property skill"
- "Refresh my NorthStar skill"
- "Update the go-daniel skill"
- "Rebuild the Command Room project skill"
- "My Acme skill is stale — fix it"
- "Rollback the NorthStar skill to last week's version"

The skill always shows preview before writing. Default option when non-zone edits exist is "Cancel" so nothing is lost by accident.

## What You Get

- Updated SKILL.md reflecting current template + context
- Preserved User Customizations zone (zero data loss there)
- Explicit prompts for any non-zone edits (merge, migrate, or discard — never silent)
- 30-day rollback window
- Provenance audit trail in GENERATION_LOG.md

## Gotchas

- **Option 4 (cancel) is the default if non-zone edits exist.** Do not auto-apply. Users who edited outside the zone did it for a reason — force them to make the merge decision consciously.
- **History directory can grow.** 30-day retention PLUS minimum-10-snapshots means worst case is 30 + 10 = 40 files per project. At ~5KB per snapshot that's 200KB per project — acceptable.
- **Rollback restores the SKILL.md but not the connector state.** If you rollback, the events.jsonl still has the regen event. This is correct behavior — events are append-only audit trail, not current state.
- **Shadow corruption kills the diff.** If `.generated/SKILL.md.current` is missing or malformed, Diff A can't run. In that case, treat entire current SKILL.md as if every section were a non-zone edit (safe — forces merge review).
- **Template version downgrades are rejected.** If generator's template_version < current SKILL.md's template_version, fail loud. Downgrade path is unsupported.
- **Regeneration does NOT auto-run on schedule.** Weekly-audit flags stale skills but does not regenerate without user confirmation. This is a safety rule — no silent rewrites.

## Connected Tools

- Reads from: same set as skill-generator (PROJECT_BRAIN, PROJECT_CONTEXT, SESSION_NOTES, connectors via MCP)
- Pair with: `skill-generator` (initial generation), `weekly-audit` (staleness flagging), `insight-generator` (accrues Workflow Routing + Gotchas content)

## Scheduled Mode

Not scheduled by default. Can be invoked by `weekly-audit` as part of its report ("these skills are stale — run regenerate-skill?"), but weekly-audit never regenerates directly.

## What It Doesn't Do

- Does not regenerate skills that don't exist (routes to skill-generator).
- Does not auto-merge non-zone edits without user confirmation.
- Does not modify plugin-level skills or cross-project skills.
- Does not delete history snapshots newer than 30 days.
- Does not rollback silently — always shows snapshot list and waits for user pick.
- Does not fix skill shape violations — those are logged by weekly-audit, surfaced to user, and the user decides whether to regenerate.
