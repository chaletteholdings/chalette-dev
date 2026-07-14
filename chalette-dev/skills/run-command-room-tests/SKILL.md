---
name: run-command-room-tests
description: "INTERNAL DIAGNOSTIC — fires solely on the exact phrase 'internal: run plugin tests'. Plugin-developer use only; not for customer chat."
---

# run-command-room-tests

User-facing test runner. Runs the three test suites that ship with the plugin (renderer + helpers + audit fixtures) and surfaces pass/fail counts in chat. Use this after every plugin install to verify the code is healthy without burning a real scheduled-task fire.

## What it runs

- `tests/run_chat_output_test.py` — renderer + validators (CanonicalActionError, LeakDetectedError, DataShapeError)
- `tests/run_helpers_test.py` — discovery helpers (mail, calendar, transcript, drive — cross-stack), brief_path
- `tests/run_audit_v2_13_0.py` — 5-orchestrator data-shape audit fixtures
- `tests/run_cru_match_test.py` — CRU layer (v2.14.6+) — match scoring, signal detectors, send + transcript matchers, event builders
- `tests/run_schedule_config_test.py` — schedule customization (v2.14.10+) — cron parsing, English rendering, config load/merge, display names

These are pure Python with stdlib only. No external dependencies. Run in seconds.

## Behavior

### Step 1 — Discover plugin root + run all three suites in one bash call

Each `mcp__workspace__bash` call is independent (no cwd carryover per Cowork's confirmed sandbox model). Wrap the entire test sequence in ONE bash invocation:

```bash
SESSION_DIR=$(echo "$CLAUDE_CODE_TMPDIR" | sed "s|/tmp$||")
PLUGIN_ROOT=$(ls -d "$SESSION_DIR"/mnt/.remote-plugins/plugin_* 2>/dev/null | head -1)
if [ -z "$PLUGIN_ROOT" ]; then
    echo "ERROR: plugin not found in remote-plugins"
    exit 1
fi
cd "$PLUGIN_ROOT" && \
echo "=== chat_output ===" && python3 tests/run_chat_output_test.py 2>&1 | tail -3 && \
echo "=== helpers ===" && python3 tests/run_helpers_test.py 2>&1 | tail -3 && \
echo "=== audit ===" && python3 tests/run_audit_v2_13_0.py 2>&1 | tail -5 && \
echo "=== cru_match ===" && python3 tests/run_cru_match_test.py 2>&1 | tail -3 && \
echo "=== schedule_config ===" && python3 tests/run_schedule_config_test.py 2>&1 | tail -3
```

### Step 2 — Parse stdout + report pass/fail in plain English

Capture each suite's last few lines. Each test runner writes a clear summary line:
- `chat_output`: `✓ all 17 tests passed` (or `✗ N tests failed`)
- `helpers`: `=== 32 passed, 0 failed ===` (or non-zero)
- `audit`: `Total issues: 0` (or non-zero with breakdown)
- `cru_match`: `OK 35 cru_match tests passed` (or non-zero)
- `schedule_config`: `OK 22 schedule_config tests passed` (or non-zero)

Surface in chat:

```
Command Room plugin health check:

✓ Renderer + validators:  17/17 tests passed
✓ Discovery helpers:      32/32 tests passed
✓ Audit fixtures:         5/5 orchestrators clean
✓ CRU match:              35/35 tests passed
✓ Schedule config:        22/22 tests passed

All ship gates green. Plugin v2.14.x is healthy.
```

If ANY suite has failures:

```
Command Room plugin health check:

✓ Renderer + validators:  17/17 tests passed
✗ Discovery helpers:      30/32 passed, 2 failed
✓ Audit fixtures:         5/5 orchestrators clean

Failures:
  - mail send: Outlook detected when no Gmail
  - drive: OneDrive detected

Build is degraded. Do not fire scheduled tasks until fixed.
```

### Step 3 — STOP

No widget. No further commentary. Just the report. Per CONTRACT.md Rule 4: no internal jargon, no file paths in user-facing output (test names like "renderer + validators" are fine — they're meaningful labels, not internal mechanics).

## What this skill does NOT do

- Does NOT modify any plugin file or workspace data
- Does NOT run scheduled tasks
- Does NOT call any external connector (Gmail / Calendar / Granola / etc.)
- Does NOT consume tokens beyond the test execution itself (~5 seconds total)

Pure read-only verification. Same model as `verify command room prompts` (which checks registered scheduled-task prompt versions); this one checks the plugin code itself.

## Trigger pattern

`run command room tests` / `command room health check` / `verify plugin code` / `run plugin tests`

## When to use

- Right after installing a new plugin version (before firing any scheduled task)
- Before reporting a bug — confirms the issue is environmental, not a code regression
- As a sanity check after `set up command room schedules` runs

## See also

- `verify command room prompts` — checks registered scheduled-task prompt content (separate concern; runs server-side checks against Cowork's task DB)
- `usage report` — surfaces telemetry from past fires (separate concern; reads events.jsonl)
