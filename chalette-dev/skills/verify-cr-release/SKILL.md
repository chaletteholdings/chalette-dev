---
name: verify-cr-release
description: "INTERNAL — automated verification orchestrator for Command Room releases. Walks a verification-plan markdown sequentially: emits trigger prompts for M to paste into Cowork, receives Cowork responses pasted back into Code, auto-classifies pass/fail/partial via response classifier, logs findings, surfaces next test. Fires on 'verify cr release [version]', 'run verification suite', 'pre-ship check', 'continue verification', 'resume verification'. Designed to replace the manual confirm-prompt testing methodology that surfaced ~80% of v3.13.7 verification findings. Stateful — tracks current test position in _hq/verify-runs/active.json. Plugin-developer use only. Companions: synthetic-workspace-runtime-test, compare-canonical-vs-freelance."
---

# verify-cr-release

Automated verification orchestrator that replaces the manual paste-cycle from this session's testing. M says `verify cr release v3.13.8` in a Code chat — the skill walks the verification plan, generates trigger prompts for M's parallel Cowork chat, receives Cowork's responses pasted back, auto-classifies pass/partial/fail, logs to findings, and surfaces the next test.

## Why this skill exists

The v3.13.7 verification session (2026-05-23 → 2026-05-24) manually walked 32 tests. Each test was:
1. Code generates trigger prompt + watch-fors + confirm prompt
2. M pastes trigger into Cowork → reads Cowork response
3. M pastes confirm prompt → reads Cowork response
4. M switches back to Code, pastes both responses
5. Code classifies + logs + generates next test

Time cost: ~10-15 min per test × 32 tests = 6+ hours of M's attention. ~80% of bugs surfaced came from the confirm-prompt introspection step, not the visible UI check. The methodology is high-leverage but tedious.

This skill automates steps 1, 3, and 4 — leaving M with just the Cowork-side paste-and-wait loop.

## When this fires

| Trigger | Context |
|---|---|
| `verify cr release v3.13.8` | Start a new verification session against a specific version |
| `run verification suite` | Same — start fresh |
| `pre-ship check` | Same — pre-ship verification gate |
| `continue verification` | Resume an in-progress session from last test position |
| `resume verification` | Same |
| `verify cr release status` | Show current position + per-phase verdicts so far |
| `verify cr release verdict` | Emit end-of-session verdict doc + production-promote recommendation |

DOES NOT fire on `run plugin tests` (that's run-command-room-tests — different scope, pure-python unit suites). DOES NOT fire on `report bug` (that's the Command Room customer-facing skill).

## Behavior

### Step 0 — Locate plan + workspace state

When M says `verify cr release [version]`, find these files in M's workspace:

```bash
# M's workspace root
WORKSPACE_ROOT="C:\Users\asdas\Desktop\Claude\Command Room"

# Locate the verification plan markdown — prefer COMPREHENSIVE_VERIFICATION_PLAN_*.md
PLAN_FILE=$(ls -t "$WORKSPACE_ROOT"/COMPREHENSIVE_VERIFICATION_PLAN_*.md 2>/dev/null | head -1)
# If none, also accept VERIFICATION_PLAN_*.md or TEST_PLAN_*.md
[ -z "$PLAN_FILE" ] && PLAN_FILE=$(ls -t "$WORKSPACE_ROOT"/VERIFICATION_PLAN_*.md "$WORKSPACE_ROOT"/TEST_PLAN_*.md 2>/dev/null | head -1)

# Findings log (where results land)
FINDINGS_LOG=$(ls -t "$WORKSPACE_ROOT"/TEST_SESSION_FINDINGS_*.md 2>/dev/null | head -1)
# If none, create one dated today

# State file (resume support)
STATE_DIR="$WORKSPACE_ROOT/_hq/verify-runs"
mkdir -p "$STATE_DIR"
STATE_FILE="$STATE_DIR/active.json"

# Bug catalog (for cross-reference — surfaces "known bug, this fire confirmed" vs "NEW bug")
BUG_CATALOG="$FINDINGS_LOG"  # findings log doubles as catalog
```

If `PLAN_FILE` is empty: STOP and ask M for the plan path explicitly.

### Step 1 — Initialize OR resume session

**For `verify cr release [version]` / `run verification suite` / `pre-ship check`:**
- Read plan into memory; parse Phase blocks (Phase 0, Phase A, Phase B-Tier 1-6, etc.) and per-phase test items
- See `references/test-parsing.md` for parse logic
- Initialize `active.json`:
  ```json
  {
    "session_id": "v3.13.8_verify_2026-05-24",
    "version_under_test": "v3.13.8",
    "plan_file": "<absolute path>",
    "findings_log": "<absolute path>",
    "started_at": "<ISO>",
    "tests": [
      {"id": "0.1", "phase": "0", "name": "Cowork update", "status": "pending"},
      {"id": "A1", "phase": "A", "name": "Bug #4 email cascade", "status": "pending"},
      ...
    ],
    "current_test_idx": 0,
    "verdicts": {},
    "new_bugs_this_session": []
  }
  ```
- Surface: "Loaded N tests from PLAN_FILE. Starting at test 0.1. Paste responses back as Cowork returns them."

**For `continue verification` / `resume verification`:**
- Read `active.json`
- Resume from `current_test_idx`
- Surface: "Resuming at test X.Y (was last at test X-1.Z). Last test verdict was PASS/PARTIAL/FAIL."

**For `verify cr release status`:**
- Read `active.json`
- Surface per-phase pass/fail summary + current position

**For `verify cr release verdict`:**
- Read `active.json`
- Generate `V<version>_VERIFIED_<date>.md` per `references/verdict-doc-template.md`
- Surface production-promote recommendation

### Step 2 — Per-test loop (called repeatedly)

For the current test (idx = `current_test_idx`):

1. **Generate trigger prompt** from the parsed plan entry. Trigger prompt is the literal "paste this into Cowork" string.

2. **Generate watch-fors** — bullet list of expected pass signals + red flags. Pulls from plan's per-test directives + cross-referenced known bugs.

3. **Generate confirm prompt** — uses `references/confirm-prompt-templates.md` to pick a phrasing that:
   - Asks Cowork to introspect specific underlying state (events written, widget kind, render path, canonical helper invocation)
   - Rotates through 3+ phrasings per test type (anti-pattern-matching, per §7 risk mitigation)
   - 5% of fires inject a deliberately-wrong premise to test honesty (anti-pattern-matching, per Phase 5D / B1-1 pattern)

4. **Output to chat** for M:
   ```
   # TEST [id] — [name]
   
   [optional context: known bug being verified, prior-version state]
   
   ## Step 1 — Paste this into Cowork:
   ```
   [trigger prompt]
   ```
   
   ## Step 2 — Watch for:
   - ✅ [expected pass signal 1]
   - ✅ [expected pass signal 2]
   - 🚩 [red flag 1]
   - 🚩 [red flag 2]
   
   ## Step 3 — When Cowork finishes, paste this confirm prompt:
   ```
   [confirm prompt — selected from rotated phrasings]
   ```
   
   ## Step 4 — Paste BOTH Cowork responses back here.
   ```

5. **Wait for M's response.** M will paste back the Cowork output — either:
   - Trigger response only (still doing confirm step in Cowork)
   - Trigger + confirm responses together
   - "STOP" / "skip" / "defer"
   - A bug observation interrupting the test

6. **Auto-classify response.** See `references/response-classifier.md`. The classifier scans Cowork's text for:
   - Canonical render markers (`render_chat_output_widget`, `apply choices: [...]`, validator-pass language)
   - Freelance render markers (`mcp__visualize__show_widget` directly, bespoke HTML, sendPrompt)
   - Event-write trace (specific event types per the test's expected writes)
   - Leak tokens (per Bug #54 word-boundary scan: `project_NNN`, `events.jsonl`, `0.\d+ confidence`, etc.)
   - Known-bug signatures (cross-reference findings log)

7. **Emit verdict** — one of:
   - `PASS` — all pass signals present, no red flags
   - `PARTIAL` — critical safety property landed, defensive/UX gap remains
   - `FAIL` — red flag present, fix didn't take
   - `NEW_BUG` — observation doesn't match any known pattern, surface for M
   - `NEEDS_HUMAN_REVIEW` — classifier confidence < 0.7, surface for M to call

8. **Log finding** to findings log per `references/findings-log-format.md`. Append to existing findings log; never overwrite.

9. **Update `active.json`** — set `verdicts[test_id]` + advance `current_test_idx` + append to `new_bugs_this_session` if NEW_BUG.

10. **Surface next test** OR end-of-phase decision gate per the plan's gate rules (e.g., "Phase A all green → green-light prod promote").

### Step 3 — Phase decision gates

Per V3.13.8_MASTER_PLAN §6 and prior verification plan conventions, phase boundaries trigger decision gates. The skill emits the gate decision when phase wraps:

- **After Phase 0:** all 3 sanity checks pass → green-light Phase A
- **After Phase A (8 tests):** all green → green-light prod promote; any FAIL → triage with M, consider patch
- **After Phase B-Tier 1 (4 tests):** Bug #4 cascade verified for downstream skills
- **End of all phases:** auto-generate `V<version>_VERIFIED_<date>.md` decision doc

### Step 4 — Risk mitigations (anti-pattern-matching per §7)

Built into prompt generation:

1. **Phrasing rotation:** 3+ confirm-prompt phrasings per test type; rotate per fire. Source: `references/confirm-prompt-templates.md`.

2. **Substrate-inspection variation:** ask Cowork to inspect DIFFERENT substrate slices per fire (events.jsonl tail vs entities.json sample vs aliases.json structure vs widget_kind value). Don't ask the same introspection question twice in the same session.

3. **Wrong-premise injection:** 5% of confirm prompts include a deliberately-wrong premise to test honesty. Example: "I noticed you wrote a `commitment_resolved` event with type=B — show me the trace." If Cowork's actual write was type=A, an honest agent corrects the premise; a pattern-matching agent narrates a fabricated B-type trace. Confidence boost when honesty surfaces.

4. **40% paraphrase re-check:** If response classifier detects > 40% of Cowork's reply is paraphrasing the confirm prompt back vs case-specific introspection, force re-verification with a sharper phrasing.

### Step 5 — STOP conditions

The skill stops sequential progression when:
- M says `STOP` / `pause` / `stop verify`
- Phase decision gate failure (Phase A FAIL) — surface to M, don't auto-continue
- Cowork weekly usage limit reached (M tells skill: "weekly limit hit") — save state, exit cleanly
- `verify cr release verdict` fired — generate end doc, exit cleanly
- Classifier surfaces unknown bug class (NEW_BUG) — pause for M's decision before next test

## Architectural design — anti-degradation

Three things break this skill if not designed against:

1. **Cowork's prompt-pattern-matching adaptation.** As Cowork sees the same confirm prompts repeatedly, it gets better at producing pattern-matching responses without doing real introspection. Mitigation: prompt rotation + substrate-inspection variation + wrong-premise injection. See `references/confirm-prompt-templates.md`.

2. **Response classifier brittleness.** Regex over Cowork's natural-language responses is fragile. Mitigation: classifier returns a confidence score; below 0.7 → `NEEDS_HUMAN_REVIEW` — surface for M's call. Don't silently mis-classify.

3. **Plan-format drift.** Different verification plans have different markdown structures. Mitigation: parser is best-effort + falls back to "ask M to provide test list explicitly" if parsing fails. See `references/test-parsing.md`.

## Companion skills

- `synthetic-workspace-runtime-test` — pre-ship gate: fires canonical surfaces against synthetic fixtures. Catches pattern static tests miss (per V3.13.8_MASTER_PLAN §6 Principle 1).
- `compare-canonical-vs-freelance` — post-v3.13.8 only: fires skill once through canonical + once through mocked freelance, side-by-side diff. Validates §3.6 ladder per-skill.

## Connection to chalette plugin family

- `run-command-room-tests` — pure-python unit suites. Run BEFORE verify-cr-release in any pre-ship gate.
- `ship-cr-plugin` — release flow. Run AFTER verify-cr-release passes Phase A.
- `process-bug-report` — handles customer bug reports. Out-of-band from verification cycle.

## Output examples

### Starting a new session

```
verify cr release v3.13.8

Loaded 32 tests from COMPREHENSIVE_VERIFICATION_PLAN_2026-05-23.md
Plan version under test: v3.13.8
Findings will be appended to TEST_SESSION_FINDINGS_2026-05-21.md
State persisted to _hq/verify-runs/active.json

Starting at test 0.1 (Phase 0 — Cowork update + sanity checks).

# TEST 0.1 — Cowork update

This is the version-bump verification step. Update Cowork to v3.13.8 via Customize → Personal plugins → Command Room → Check for updates → Update → fully quit Cowork → reopen.

## Step 1 — Paste this into Cowork:
```
command room update
```

## Step 2 — Watch for:
- ✅ Plugin v3.13.8 confirmed
- ✅ Both Layer 1 dashboards installed
- ✅ Substrate migrations clean
- 🚩 ANY corruption_recovery event NOT appearing (Sub-bug #14b sweep should fire on first v3.13.8 update)
- 🚩 Plugin version still 3.13.7 (update didn't land)

## Step 3 — Confirm prompt (paste after Cowork responds):
```
For the v3.13.8 update you just ran, confirm: (1) Plugin version 3.13.8 confirmed in plugin.json. (2) Did the corruption_recovery migration fire? Show me the corruption_recovery event in events.jsonl with data.recovery_version. (3) Were any malformed events.jsonl lines quarantined to _hq/.system/quarantine/? (4) Confirm next_seq.py helper is installed at shared/scripts/next_seq.py.
```

## Step 4 — Paste BOTH Cowork responses back here when ready.
```

### Receiving a response + auto-classifying

M pastes back Cowork's responses. Skill classifies:

```
TEST 0.1 — auto-classified PASS (confidence 0.92)

Evidence:
✓ Plugin v3.13.8 confirmed
✓ corruption_recovery event found (seq 1779712345..., data.recovery_version="v3.13.8")
✓ 8 lines quarantined to _hq/.system/quarantine/events_quarantine_2026-05-25T...
✓ next_seq.py at shared/scripts/next_seq.py (verified)

No red flags. Substrate migration landed cleanly.

Logged to TEST_SESSION_FINDINGS_2026-05-21.md (line 1845+).

## Next: TEST A1 — Bug #4 email-writer cascade (SHIP BLOCKER verification)

[next trigger prompt + watch-fors + confirm prompt]
```

### End-of-session verdict

When all phases complete or M fires `verify cr release verdict`:

```
verify cr release verdict

V3.13.8_VERIFIED_2026-05-25.md generated.

Summary:
- 32 tests run: 28 PASS / 3 PARTIAL / 1 FAIL
- 0 new bugs surfaced
- All 14 Tier 1 fixes verified per §2 of master plan
- 8/10 Tier 2 fixes verified per §3 of master plan (2 deferred for fresh-install case)

Production-promote recommendation: SAFE
New-customer onboarding: SAFE

Decision doc saved to Desktop/Claude/Command Room/V3.13.8_VERIFIED_2026-05-25.md
```

## Implementation notes

The skill uses these files:
- `references/test-parsing.md` — markdown → test-list parser logic
- `references/confirm-prompt-templates.md` — rotated phrasings per test type + wrong-premise injection patterns
- `references/response-classifier.md` — regex patterns for canonical markers / freelance markers / event writes / leak tokens
- `references/findings-log-format.md` — append-only format for findings log entries
- `references/verdict-doc-template.md` — end-of-session V<version>_VERIFIED.md template
- `references/phase-decision-gates.md` — per-phase gate logic (Phase A green-light, etc.)

All canonical helpers are pure-python stdlib. No external dependencies. Skill state lives in `_hq/verify-runs/active.json`.

## Failure modes + mitigations

- **Plan parsing fails** → ask M for test list explicitly; offer to use last-known-good plan format
- **Response classifier confidence < 0.7** → emit `NEEDS_HUMAN_REVIEW` + show M what triggered the low confidence
- **State file corrupted** → backup + ask M to reseed from latest findings log
- **Cowork weekly limit hit** → save state cleanly; on resume, surface "you paused at test X.Y on date — resume?"
- **Bug catalog drift** (new bugs in plan not in catalog) → emit them as `NEW_BUG` + ask M to confirm whether to add to catalog
