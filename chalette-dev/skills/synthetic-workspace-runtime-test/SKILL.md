---
name: synthetic-workspace-runtime-test
description: "INTERNAL — pre-ship gate that spins up a synthetic workspace fixture (clean substrate + 8 deliberately-malformed lines + curated entities/aliases/events) and fires the 7 canonical-scope surfaces against it. Asserts: canonical render path was actually invoked (not freelance), canonical events written with correct shapes, no leak tokens in any output, defensive readers tolerate malformed lines. Triggers: 'run synthetic workspace test', 'pre-ship runtime gate', 'synthetic e2e'. Designed to catch the 'static analysis passes but runtime substitutes inferior path' bug class that v3.13.x verification surfaced repeatedly (Bug #11 / #45 / #52 / #53). Plugin-developer use only. Per V3.13.8_MASTER_PLAN §6 Principle 1: runtime exercise, not static check. Companion to verify-cr-release (which is M-attended Cowork loop)."
---

# synthetic-workspace-runtime-test

Spins up a synthetic Command Room workspace fixture in a temporary directory + fires the 7 canonical-scope scheduled-task surfaces against it. Asserts canonical render path was actually invoked, canonical events written, no leak tokens, defensive readers tolerate malformed substrate.

**Per V3.13.8_MASTER_PLAN §6 Principle 1:** the recurring bug class across v3.13.x testing was "implementation exists, SKILL.md references it, runtime substitutes inferior path under time pressure" (Bugs #11 / #23 / #45 / #52 / #53). Static analysis (read SKILL.md, validate schema) doesn't catch this — only runtime exercise does. This skill is the canonical runtime-exercise gate.

## Why this skill exists

Static structural tests (`tests/run_chat_output_test.py`, `tests/run_helpers_test.py`, etc.) catch:
- ✅ Schema violations
- ✅ Renderer validation gate failures
- ✅ Forbidden tokens in test fixtures

They DO NOT catch:
- ❌ Skill that loads correctly but runtime substitutes freelance path
- ❌ Canonical helper that crashes on real workspace data
- ❌ Process narration leaks during between-tool-call execution
- ❌ Approval gates that hold for canonical path but bypass via sendPrompt indirection

This skill closes that gap by running ACTUAL skill code paths against ACTUAL substrate fixtures + asserting runtime invariants.

## When this fires

| Trigger | Context |
|---|---|
| `run synthetic workspace test` | Standalone runtime gate run |
| `pre-ship runtime gate` | Pre-ship checklist component (per ship-cr-plugin) |
| `synthetic e2e` | Same |
| `synthetic workspace test [skill_name]` | Run gate against a specific skill only |
| `synthetic workspace test --fixtures` | Show available fixtures + their characteristics |

DOES NOT fire on `verify cr release` (that's the M-attended Cowork loop). DOES NOT fire on `run plugin tests` (that's pure-python unit suites, no real substrate).

## Fixtures (in `fixtures/`)

The skill ships canonical fixtures that simulate realistic workspace states:

### `fixtures/clean_workspace/` — pristine baseline

- entities.json: 10 people, 5 orgs, 3 projects
- events.jsonl: 200 events (clean, all canonical shapes)
- aliases.json: 25 entries covering all 10 people
- _hq/views/: regenerated views matching substrate
- CLAUDE.md: workspace instructions

Use for: baseline pass verification

### `fixtures/mature_workspace/` — realistic mature state

Like a real workspace at scale:
- entities.json: 80 people, 20 orgs, 15 projects
- events.jsonl: 1500 events (mix of nano-epoch + human-counter seqs per Bug #41)
- 8 deliberately malformed events.jsonl lines (per Sub-bug #14b — the line-shatter pattern seen in a real workspace)
- aliases.json: 50 entries with both nested + flat shapes (per `feedback_canonical_path_improv_pattern`)
- Mixed event types including some unsanctioned (e.g., `person_added` legacy + `person_created` canonical mixed — per Bug #34)

Use for: defensive-reader tolerance verification, substrate-hygiene migration testing

### `fixtures/degraded_workspace/` — failure-mode fixtures

- entities.json with: 2 Daniels (canonical full-name collision), org with no domains, person with no email (Bug #44 send-class no-email case)
- events.jsonl with: untitled decisions (Bug #22), commitment supersedes mislabeled as resolved (Bug #24), unsanctioned event types (Bug #43)

Use for: edge-case + recovery verification

### `fixtures/fresh_install/` — Day-1 customer

- Empty entities.json (just workspace_settings)
- Empty events.jsonl
- No aliases.json yet
- Default CLAUDE.md

Use for: first-fire / onboarding verification (Bug #36 brain_name prompt, M1 widget)

## Behavior

### Step 1 — Discover plugin + select fixture

```bash
SELF="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"   # chalette-dev plugin root (holds config/)
SESSION_DIR=$(echo "$CLAUDE_CODE_TMPDIR" | sed "s|/tmp$||")
PLUGIN_ROOT=$(ls -d "$SESSION_DIR"/mnt/.remote-plugins/plugin_* 2>/dev/null | head -1)
# Fallback: the cr1 clone from the merged operator profile (operator.json + operator.local.json
# overlaid per-key; gitignored, only M has one). Never a hardcoded machine/marketplace path.
if [ -z "$PLUGIN_ROOT" ]; then
  CR1_CLONE=$(python -c "import json,os
p={}
for f in ('$SELF/config/operator.json','$SELF/config/operator.local.json'):
    if os.path.exists(f): p.update(json.load(open(f)))
print(os.path.expanduser(p.get('cr1_clone') or ''))")
  [ -n "$CR1_CLONE" ] && PLUGIN_ROOT="$CR1_CLONE/command-room"
fi
```

Use chalette plugin's own `skills/synthetic-workspace-runtime-test/fixtures/` directory for fixture source.

### Step 2 — Copy fixture to temp dir + initialize

```bash
TMPDIR=$(mktemp -d -p /tmp synthetic_workspace_XXXXXX)
cp -r "${CHALETTE_PLUGIN}/skills/synthetic-workspace-runtime-test/fixtures/${FIXTURE_NAME}" "$TMPDIR/"
WORKSPACE_ROOT="$TMPDIR/${FIXTURE_NAME}"
```

Each fixture is read-only canonical; the copy is the ephemeral workspace the skill mutates.

### Step 3 — Fire 7 canonical-scope surfaces against the fixture

The 7 surfaces per V3.13.8_MASTER_PLAN canonical scope:

```python
canonical_surfaces = [
    ("morning-briefing", "morning brief"),
    ("orchestrator-inbox", "inbox triage"),
    ("orchestrator-commitments", "commitments"),
    ("orchestrator-dont-forget", "pulse"),
    ("orchestrator-upcoming-meetings", "upcoming meetings"),
    ("orchestrator-past-meetings", "past meetings"),
    ("orchestrator-friday-wrap", "friday wrap"),
]

for surface, trigger in canonical_surfaces:
    result = fire_surface_against_fixture(surface, trigger, WORKSPACE_ROOT)
    verify_invariants(result, surface, fixture_name)
```

`fire_surface_against_fixture()` mocks the Cowork environment minimally:
- Sets workspace_root to fixture's path
- Invokes the orchestrator's bootloader steps
- Captures: tool calls made, events appended, widget HTML emitted, chat narration

### Step 4 — Per-surface invariant assertions

For each fire, the skill verifies these invariants:

```python
def verify_invariants(result: FireResult, surface: str, fixture_name: str) -> list[Failure]:
    failures = []
    
    # Invariant 1: canonical render path
    if not result.called("render_chat_output_widget"):
        failures.append(Failure(
            invariant="canonical_render_invoked",
            surface=surface,
            evidence=f"render_chat_output_widget not called; tool trace: {result.tool_trace[:200]}"
        ))
    
    # Invariant 2: pack_run event written (per Bug #61 fix)
    pack_run_events = [e for e in result.events if e["type"] == "pack_run"]
    if not pack_run_events:
        failures.append(Failure(invariant="pack_run_written", surface=surface))
    elif not pack_run_events[0]["data"].get("kind"):
        failures.append(Failure(invariant="pack_run_kind_populated", surface=surface))
    
    # Invariant 3: no leak tokens in widget HTML or chat narration
    leaks = scan_for_leaks(result.widget_html + result.chat_narration)
    if leaks:
        failures.append(Failure(invariant="no_leaks", surface=surface, evidence=leaks))
    
    # Invariant 4: defensive reader tolerated malformed lines (only for mature/degraded fixtures)
    if fixture_name in ("mature_workspace", "degraded_workspace"):
        if not result.called("_load_events_defensively"):
            failures.append(Failure(invariant="defensive_read_invoked", surface=surface))
    
    # Invariant 5: canonical entity_resolve invoked for any name resolution
    if result.resolved_names_count > 0 and not result.called("entity_resolve"):
        failures.append(Failure(invariant="canonical_entity_resolve", surface=surface))
    
    # Invariant 6: no freelance widget (per Bug #32)
    if result.called("mcp__visualize__show_widget") and not result.called("render_chat_output_widget"):
        failures.append(Failure(
            invariant="no_freelance_render",
            surface=surface,
            evidence="show_widget invoked without canonical render → freelance path detected"
        ))
    
    # Invariant 7: schema-sanctioned event types only + gate routing
    # The event gate lives inside atomic_append_jsonl (cr1 Phase 4, 2026-07-02): it REJECTS an
    # unregistered type at append time, so a fire that tried to write one surfaces as a raised
    # EventGateError, not a landed unsanctioned event. Assert BOTH: nothing unsanctioned reached
    # the file, AND any surface that wrote events routed through append_event — a landed
    # unsanctioned type (or a write that skipped append_event) means the surface bypassed the gate.
    unsanctioned = [e["type"] for e in result.events if e["type"] not in SCHEMA_ENUM]
    if unsanctioned:
        failures.append(Failure(invariant="schema_compliance", surface=surface, evidence=unsanctioned))
    if result.wrote_events and not result.called("append_event"):
        failures.append(Failure(
            invariant="event_gate_routed",
            surface=surface,
            evidence="events written without append_event → legacy/bypass write path detected"
        ))
    
    return failures
```

See `references/invariants.md` for full invariant list.

### Step 5 — Report

After all 7 surfaces fire across all selected fixtures, emit summary:

```
Synthetic workspace runtime test — v3.13.8

Fixtures tested: clean_workspace, mature_workspace, degraded_workspace
Surfaces fired: 7
Total fires: 21

PASSES: 19/21
FAILURES: 2

Failures:
1. orchestrator-commitments on mature_workspace
   Invariant: defensive_read_invoked
   Evidence: cru_match.load_open_commitments called but _load_events_defensively NOT invoked
   Likely cause: Bug #52 fix incomplete — morning-briefing migration may have stale silent-filter remnant

2. orchestrator-past-meetings on degraded_workspace
   Invariant: pack_run_kind_populated
   Evidence: pack_run event written but data.kind is null
   Likely cause: Bug #61 fix didn't propagate to past-meetings orchestrator yet

Recommend: address before v3.13.8 ship. Re-run after fixing.
```

### Step 6 — Cleanup

```bash
rm -rf "$TMPDIR"
```

Skill writes a summary to `_hq/synthetic-test-runs/<timestamp>/report.md` under the resolved workspace (or a temp dir for synthetic-only operators) + raw fire traces to `<timestamp>/traces/`.

## Failure modes + mitigations

- **Fixture out of date with plugin version:** skill detects via plugin_version vs fixture_compatibility_version mismatch in fixture's `.metadata.json`; surfaces clearly + offers to regenerate.
- **Mocking too thin to catch real bugs:** skill captures actual tool-trace; failures include verbatim trace excerpts so the operator can verify manually.
- **Fixture diverges from real workspaces over time:** quarterly fixture refresh via diff against the operator's real workspace shape, not content (operator=m only — the only profile with a real workspace to diff against).

## Connection to verify-cr-release

The skills are companions, not substitutes:

| | verify-cr-release | synthetic-workspace-runtime-test |
|---|---|---|
| Environment | the operator's actual Cowork chat + Code | Pure Code subprocess |
| Substrate | the operator's real workspace | Synthetic fixture |
| Speed | ~10 min per test (M-attention) | ~30 sec per fire (automated) |
| Catches | Cowork-side LLM behavior | Plugin-side code-path behavior |
| When to run | Pre-ship Cowork-integration gate | Pre-commit + ship-cr-plugin pre-flight |

Run synthetic-workspace-runtime-test FIRST (catches code-path issues before they reach Cowork) — THEN verify-cr-release (catches Cowork-side runtime behavior).

## Implementation notes

The skill uses pure-python stdlib (no external dependencies) per the chalette skill pattern. Fixtures are JSON + markdown — version-controlled in the chalette repo alongside the skill.

References:
- `references/invariants.md` — full invariant catalog with regex + assertion logic
- `references/fire-mocking.md` — how to invoke skill code paths against a synthetic workspace
- `references/fixture-spec.md` — schema for fixture directories
- `fixtures/clean_workspace/` — baseline canonical fixture
- `fixtures/mature_workspace/` — Bug #14b + Bug #41 stress fixture
- `fixtures/degraded_workspace/` — edge-case fixture
- `fixtures/fresh_install/` — Day-1 customer fixture
