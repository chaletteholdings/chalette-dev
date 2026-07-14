---
title: Event Type Registry — writers + consumers + last-touched
cr_plugin_version_min: 3.13.8.3
last_updated: 2026-05-26
auto_regenerated: true
---

# Event Type Registry

This file is REGENERATED at every cr-skill-builder run by reading `command-room/shared/data-schemas/events.schema.json` (the canonical enum) and grepping `command-room/skills/**/SKILL.md` for `"type": "<value>"` in writer + reader contexts.

## What cr-skill-builder uses it for

1. **Phase 2 — substrate contract design:** surface existing event types when M says "this skill reads commitments" so M doesn't reinvent.
2. **Gate 2 — consumer check:** for each new event type the skill writes, validate the declared consumer exists.
3. **Gate 20 — collision check:** new event type names don't shadow existing ones.

## Regeneration

At Phase 2 start, cr-skill-builder runs the regeneration helper:

```bash
SESSION_DIR=$(echo "$CLAUDE_CODE_TMPDIR" | sed "s|/tmp$||")
PLUGIN_ROOT=$(ls -d "$SESSION_DIR"/mnt/.remote-plugins/plugin_* 2>/dev/null | head -1)
cd "$PLUGIN_ROOT"
python3 shared/scripts/regenerate_event_registry.py
```

(Helper to be added at skill build time. Until then, registry is manually maintained against `events.schema.json`.)

## Registry shape

```json
{
  "schema_version": 1,
  "regenerated_at": "<ISO datetime>",
  "cr_plugin_version": "<X.Y.Z>",
  "event_types": [
    {
      "type": "<event_type_name>",
      "writers": ["<skill-name>", ...],
      "consumers": ["<skill-name>", ...],
      "shape_variants": <integer>,
      "canonical_reader": "<helper path or 'direct'>",
      "first_seen_version": "<X.Y.Z>",
      "notes": "<optional>"
    }
  ]
}
```

## Current event types (as of cr_plugin_version_min)

The full enum is in `command-room/shared/data-schemas/events.schema.json`. Highlights for quick reference:

### Commitment family (5 shape variants — read via `cru_match._commitment_field`)

| Type | Writers | Canonical reader |
|---|---|---|
| `commitment` | scan-for-commitments, cr-past-meetings, meeting-notes, follow-up-ritual | `cru_match._commitment_field` |
| `commitment_resolved` | commitments-orchestrator, log-resolution, cr-past-meetings | `cru_match._commitment_field` |
| `commitment_updated` | commitments-orchestrator, follow-up-ritual | `cru_match._commitment_field` |
| `commitment_review_proposed` | scan-for-commitments (pending-review variant) | `cru_match._commitment_field` |
| `commitment_review_dismissed` | commitments-orchestrator | `cru_match._commitment_field` |
| `commitment_to_discuss` | meeting-notes | `cru_match._commitment_field` |

### Decision family

| Type | Writers | Canonical reader |
|---|---|---|
| `decision` | decision-log, decision-memo-composer, meeting-notes | direct |
| `decision_resolved` | decision-log, log-resolution | direct |
| `decision_superseded` | decision-log | direct |
| `decision_reaffirmed` | decision-revisit | direct |
| `decision_memo_drafted` | decision-memo-composer | direct |

### People + Org lifecycle

| Type | Writers |
|---|---|
| `person_created`, `person_updated`, `person_merged`, `person_repaired`, `person_proposal`, `person_update_proposal`, `person_added`, `person_pending_review` | people-crm + via `people_writer.py` |
| `org_proposed`, `org_created`, `org_updated`, `org_repaired` | people-crm, automation, workspace-manager |
| `tier_change` | people-crm |

### Meeting + interaction

| Type | Writers |
|---|---|
| `meeting`, `meeting_scheduled`, `meeting_processed` | cr-past-meetings, cr-upcoming-meetings, meeting-notes |
| `interaction` | passive-capture (any connector read) |
| `outreach_sent` | email-writer, follow-up-ritual |
| `thread_resolved`, `thread_resurrected` | thread-resurrection, log-resolution |
| `email_drafted`, `email_sent` | email-writer, commitments-orchestrator, inbox-triage |

### Briefing + report family

| Type | Writers |
|---|---|
| `briefing` | morning-briefing |
| `memo_drafted` | memo-writer |
| `one_pager_drafted` | one-pager-composer |
| `board_pack_assembled` | board-pack-assembler |
| `followup_pack_drafted` | follow-up-ritual |
| `pack_run` | operator-report, weekly-recap |
| `contract_reviewed` | contract-review |

### Workspace lifecycle

| Type | Writers |
|---|---|
| `status_change`, `scope_change` | workspace-manager |
| `intel_logged` | intel-intake, insight-generator |
| `audit_run`, `weekly_audit_run` | weekly-audit |
| `pattern_break_detected` | insight-generator |
| `classification_review`, `reclassification` | inbox-triage, follow-up-ritual |
| `onboarding_step`, `onboarding_checkpoint` | command-room-onboarding |
| `chat_dismissal`, `chat_suppressed` | apply-choices |
| `choices_applied` | apply-choices |
| `dont_forget_feedback` | pulse |
| `connector_read` | all connector-touching skills via passive-capture |
| `schedule_created`, `backfill_chunk_scheduled` | enable-command-room-schedules |
| `plugin_install`, `plugin_update`, `plugin_update_deferred`, `plugin_update_remediation` | command-room-update-bridge |
| `workspace_migration_applied`, `workspace_migration_skipped`, `workspace_setting_changed` | workspace-manager |
| `brain_name_captured`, `brain_name_declined` | workspace-manager |
| `artifact_installed`, `artifact_install_failed` | enable-quick-commands, enable-workspace-map |
| `file_filed` | file-documents |
| `bug_received` | process-bug-report (chalette), report-bug |
| `automation_opportunity_surfaced`, `automation_scaffolded`, `automation_deployed` | automation-scanner, scaffold-automation |
| `search_performed` | transcript-search |
| `intro_made`, `intro_followup_check`, `intro_landed`, `intro_didnt_land` | intro-broker |

### Reserved for v3.14+ (cr-skill-builder Mode 2 will add these)

These are the new event types for the locked v3.14 batch — they MUST be added to the enum before any v3.14 skill ships:

| Type | Writer (planned) | Consumers (planned) |
|---|---|---|
| `customer_health_scored` | customer-health-scorer | morning-briefing, friday-wrap, weekly-review-coach |
| `okr_logged`, `okr_progress_logged`, `okr_kr_attributed` | okr-tracker | friday-wrap, morning-briefing, weekly-review-coach |
| `project_stalled_flagged` | pulse / weekly-audit (enhancement) | morning-briefing, friday-wrap |
| `one_on_one_held`, `one_on_one_overdue`, `one_on_one_skipped` | 1on1-tracker | morning-briefing, weekly-audit |
| `weekly_intention_set` | weekly-review-coach | friday-wrap, morning-briefing |
| `skill_first_run_configured`, `skill_reconfigured` | (any skill with first-run questionnaire via skill_config_writer.py) | usage-report, weekly-audit |

When cr-skill-builder scaffolds a v3.14 skill, it generates the enum diff for `events.schema.json` AND updates this registry as part of Phase 5 output.

## Collision-detection rules (Gate 20)

When Phase 2 declares a new event type, cr-skill-builder checks:
1. Exact name match against existing enum → BLOCK (rename required)
2. ≥90% semantic similarity (e.g., `customer_scored` vs existing `customer_health_scored`) → WARN with rename suggestion
3. Same prefix family but different shape (e.g., new `commitment_X` event type that doesn't match the 5-shape canonical reader) → BLOCK (use existing shape OR introduce explicit reader)

## Consumer-check rules (Gate 2)

When Phase 2 declares a consumer for a new event type:
1. Named consumer must exist in `skills/` OR be a new skill being created in the same ship
2. If consumer is an existing skill being modified to read the new event, generate a consumer-update note in Phase 5 output
3. Zero consumers → BLOCK
