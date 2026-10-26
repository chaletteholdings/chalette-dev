---
name: ship-readiness-gate
description: "INTERNAL — automated post-push verification orchestrator. Fires in Code (the plugin-dev environment) after a push to staging main (chaletteholdings/cr1). Detects the fresh ship, then runs the full canonical-surface verification battery against all synthetic fixtures + cross-references findings against the bug catalog + emits a PROMOTE/HOLD/BLOCKED verdict doc. No paste-back loop required — fully unattended. Triggers: 'ship readiness gate', 'post-push verify', 'production rehearsal', 'pre-promote check'. Used to gate the production-promote decision without needing the operator to walk a Cowork verification cycle manually. Plugin-developer use only. Companion to battery (the single entry point; this skill is its tier 4) and synthetic-workspace-runtime-test (per-fire code-path gate)."
---

# ship-readiness-gate

> **Team toolkit (chalette-dev).** Anyone on the team may run this. A contractor runs it against the synthetic fixtures or a copied test brain only, never a real client folder, and never ships or promotes. The owner's own workspace needs the owner's yes in the chat. Who is running is read the way `cr1-test` reads it, from `config/operator.json`.

**The fully-unattended pre-promote verification gate.** Fires in Code immediately after a push to staging main (chaletteholdings/cr1). Runs the full verification battery automatically (no Cowork paste-back loop) + emits a PROMOTE / HOLD / BLOCKED verdict on production-promote decision.

> **Operator profile (read first).** Load `config/operator.json`, then overlay `config/operator.local.json` per-key if present (gitignored; the operator's local overlay — not every operator has one). Resolve `cr1_clone` (staging clone to inspect), `workspace_root` (where verdict docs land), and `allowed_targets`. **Default target is synthetic fixtures** — the `mature_workspace`/`clean_workspace`/`degraded_workspace`/`fresh_install` fixtures are populated. Targeting a real workspace requires `"real"` in `allowed_targets` (M only); any other operator that asks for `--target=m-workspace` is refused and run against synthetic.
> ```python
> import json, os, sys
> op = {}
> for _n in ("operator.json", "operator.local.json"):
>     _p = os.path.join(SKILL_PLUGIN_ROOT, "config", _n)
>     if os.path.exists(_p): op.update(json.load(open(_p)))
> # SKILL_PLUGIN_ROOT must be a NATIVE path — on Windows `C:/Users/…`, never an MSYS
> # `/c/Users/…` (convert with `cygpath -m`): python.exe reads `/c/…` as `C:\c\…`, both
> # files miss, and an empty profile silently becomes the default. Fail loud instead.
> if not op: sys.exit(f"FATAL: operator profile unreadable under {SKILL_PLUGIN_ROOT}")
> ```

## Why this skill exists

Per V3.13.8_MASTER_PLAN §10 Decision 5: production-promote follows a 24h M-only smoke window AFTER ship to staging. That smoke window is currently manual — M fires things in Cowork, checks for issues, decides whether to promote.

**This skill compresses the smoke window** by running an automated battery against synthetic fixtures + invariant assertions + bug-catalog cross-reference + emitting a PROMOTE verdict. M reviews the verdict doc (~5 min instead of 24h watch).

Caveat: this skill catches code-path issues but NOT Cowork-side LLM behavior. Final decision still the owner's. But the gate eliminates ~80% of the bug classes that have surfaced post-ship historically.

## When this fires

| Trigger | Context |
|---|---|
| `ship readiness gate` | Manual fire after a recent push |
| `post-push verify` | Same |
| `production rehearsal` | Same |
| `pre-promote check` | Same |
| `ship readiness gate --auto-detect` | Auto-detect fresh push via git log; abort if HEAD is > 24h old |
| `ship readiness gate --target=m-workspace` | Run battery against the operator's real workspace (NOT synthetic fixtures) — permitted ONLY when the merged profile has `"real"` in `allowed_targets`; any other operator is refused and falls back to synthetic |
| `ship readiness gate --target=synthetic` (default) | Run battery against the populated synthetic fixtures |

DOES NOT fire on `verify cr release` / `run verification suite` (`battery` owns those — they alias `battery --attended`, the hand-walked dogfood ritual, since `verify-cr-release` was retired). DOES NOT fire on `run synthetic workspace test` (that's a single-fixture single-skill test).

### Target mode behavior

**Default target is the populated synthetic fixtures.** A real workspace is targeted only when the merged operator profile grants `"real"` in `allowed_targets` (the owner's profile) — the contractor-safe default runs synthetic only. When real is granted, the operator's live workspace adds realistic-scale edge cases the fixtures may not carry; when it isn't, the fixtures are the bar.

The skill runs:
- **bug-regression-suite** against the resolved target (real workspace runs carry the safety envelope: pre-snapshot + test_artifact tagging + cleanup helper)
- **cross-skill-interaction-test** against the resolved target (multi-fire sequences with substrate snapshots) — real-workspace only, per its own fence
- **synthetic-workspace-runtime-test** against the fixtures

Always uses bug-regression-suite + synthetic-workspace-runtime-test as primary gates. cross-skill-interaction-test is a SUPPLEMENTARY gate that activates when its dependency (a real target) is met.

## Behavior

### Step 0 — Detect fresh push

```bash
# Locate the Command Room staging clone. Prefer the operator profile's cr1_clone
# (M defaults it to ~/repos/cr1-canonical); fall back to an installed marketplace clone.
# --- operator-profile resolution (canonical pattern — keep byte-synced across skills) ---
# Locate THIS plugin's root by searching for config/operator.json, then hand python a
# NATIVE path. Two Git-Bash-on-Windows traps this is fenced against (MAINT2, 2026-07-24):
#   1. `${BASH_SOURCE[0]}` is EMPTY when an agent runs this block through a Bash tool —
#      it is not a sourced script. `dirname ""` is `.`, so the plugin root silently became
#      whatever the cwd's grandparent happened to be.
#   2. `pwd` under Git Bash yields an MSYS path (`/c/Users/…`). Native python.exe resolves
#      `/c/…` to `C:\c\…`, so BOTH config reads miss, the merged profile comes back EMPTY,
#      and resolution falls through with NO error — here that meant `cr1_clone` was invisible
#      and the gate silently inspected a stale marketplace clone. `cygpath -m` yields
#      `C:/Users/…`, which MSYS bash and Windows python both read.
# Never hardcode a machine path: search, then the $CHALETTE_DEV_ROOT escape hatch, then FAIL LOUD.
_cr_native() { if command -v cygpath >/dev/null 2>&1; then cygpath -m "$1"; else printf '%s\n' "$1"; fi; }
DEV_PLUGIN_ROOT=""
for _c in "${CHALETTE_DEV_ROOT:-}" "$PWD" "$PWD/chalette" "$(dirname "$PWD")" \
          ~/repos/chalette/chalette ~/.claude/plugins/marketplaces/*/chalette; do
  [ -n "$_c" ] && [ -f "$_c/config/operator.json" ] && DEV_PLUGIN_ROOT="$(_cr_native "$_c")" && break
done
[ -n "$DEV_PLUGIN_ROOT" ] || { echo "FATAL: chalette plugin root not found (no config/operator.json in any searched location). Set CHALETTE_DEV_ROOT=<plugin root> and re-run." >&2; exit 1; }
OPERATOR_CFG="$DEV_PLUGIN_ROOT/config/operator.json"
OPERATOR_OVERLAY="$DEV_PLUGIN_ROOT/config/operator.local.json"      # gitignored M-only overlay
# --- end operator-profile resolution ---
CR1_CLONE=$(python -c "import json,os,sys
p={}; _n=0
for f in ('$OPERATOR_CFG','$OPERATOR_OVERLAY'):
    if os.path.exists(f): p.update(json.load(open(f))); _n+=1
if not _n: sys.exit('FATAL: operator profile unreadable at $OPERATOR_CFG')
print(os.path.expanduser(p.get('cr1_clone') or ''))") || exit 1
if [ -n "$CR1_CLONE" ] && [ -d "$CR1_CLONE/command-room" ]; then
    STAGING_ROOT="$CR1_CLONE/command-room"
else
    STAGING_ROOT=~/.claude/plugins/marketplaces/cr1/command-room
fi

cd "$STAGING_ROOT"
git fetch origin main --quiet
LAST_COMMIT_TS=$(git log -1 --format="%ct" origin/main)
NOW=$(date +%s)
AGE_HOURS=$(( (NOW - LAST_COMMIT_TS) / 3600 ))

if [ "$AGE_HOURS" -gt 24 ]; then
    echo "ABORT: most recent commit is $AGE_HOURS hours old — not a fresh ship"
    exit 1
fi

VERSION=$(jq -r .version "$STAGING_ROOT/.claude-plugin/plugin.json")
COMMIT_REF=$(git rev-parse --short origin/main)
echo "Verifying ship: v$VERSION at $COMMIT_REF"
```

If no recent push detected and trigger wasn't `--force`, abort cleanly. M can override with `ship readiness gate --force` to run anyway.

### Step 1 — Run synthetic-workspace-runtime-test against all 4 fixtures

```python
fixtures = ["clean_workspace", "mature_workspace", "degraded_workspace", "fresh_install"]
canonical_surfaces = [
    "morning-briefing", "orchestrator-inbox", "orchestrator-commitments",
    "orchestrator-dont-forget", "orchestrator-upcoming-meetings", 
    "orchestrator-past-meetings", "orchestrator-friday-wrap",
]

verdicts = {}
for fixture in fixtures:
    for surface in canonical_surfaces:
        result = run_synthetic_fire(fixture, surface)
        invariant_failures = verify_invariants(result, surface, fixture)
        verdicts[(fixture, surface)] = invariant_failures
```

See `synthetic-workspace-runtime-test/SKILL.md` for the invariant catalog (18 invariants per fire).

### Step 2 — Cross-reference against bug catalog

For every PASS/FAIL outcome, cross-reference against the latest findings log:

```python
# The bug catalog is the canonical known-bug source, shipped in the plugin.
findings_log = Path(SKILL_PLUGIN_ROOT) / "skills/bug-regression-suite/references/bug-catalog.md"
known_bugs = parse_bug_catalog(findings_log)

# Did any KNOWN bug surface in this run? (regression detection)
regressions = []
for verdict in verdicts.values():
    if verdict.has_failures():
        matched_bugs = match_against_catalog(verdict, known_bugs)
        if matched_bugs:
            regressions.extend(matched_bugs)

# Did any NEW failure surface that doesn't match catalog? (new bug class)
new_failures = [v for v in verdicts.values() if v.has_failures() and not v.matched_known_bug]
```

### Step 3 — Aggregate verdict

```python
verdict = compute_ship_readiness_verdict(verdicts, regressions, new_failures)

# Logic:
# BLOCKED — any Tier 1 ship-blocker test FAILED OR any KNOWN ship-blocker bug regressed
# HOLD — any Tier 2 fix verification PARTIAL OR new failure class surfaced
# PROMOTE — all Tier 1 PASS, no regressions, no new failures
```

### Step 4 — Emit verdict doc

Write `<workspace_root>/SHIP_READINESS_v{version}_{date}.md` (workspace_root resolved from the operator profile; a synthetic-only operator writes it to a scratch/temp dir):

```markdown
# Ship Readiness Gate — v{version}

**Date:** {ISO}
**Ship commit:** {ref}
**Auto-fired:** {true | false}
**Verdict:** {PROMOTE | HOLD | BLOCKED}

## §1. Surface verification — synthetic fixtures

{tabular results per fixture × surface}

## §2. Render-path invariants — I1 / I2 / I16

{per-fire results for I1 `canonical_render_invoked`, I2 `no_freelance_render`, I16 `file_uri_transport` — from Step 1. These three ARE the render-path check; the retired per-skill ladder diff has no successor step here (see "What this skill catches"). Report only invariants Step 1 actually returned — never a per-skill ladder tally.}

## §3. Known bug regression check

{any bugs from catalog that reappeared}

## §4. New failure classes detected

{any failures that don't match catalog — surface for the operator's call}

## §5. Production-promote recommendation

{PROMOTE | HOLD | BLOCKED} with rationale

{If PROMOTE:}
**You may safely run:**
- ship-cr-plugin Step 9 production promote (fans out core to all ChaletteHQ client repos via scripts/promote_core_to_clients.py — dry-run first)

{If HOLD:}
**Pending:**
- {list of items needing the operator's judgment call}

{If BLOCKED:}
**Must fix before promote:**
- {list of failing tests + likely cause + recommended action}
```

### Step 5 — Surface to chat

```
Ship Readiness Gate — v3.13.8

Verifying ship at commit abc1234 (2 hours ago)...

Synthetic fixtures: 4/4 fired
Canonical surfaces: 7/7 per fixture (28 total fires)

PASS: 27/28 fires
PARTIAL: 1/28 (mature_workspace × morning-briefing — I6 defensive_read partially fired but skipped_lines not surfaced)

Known bug regression check: 0 regressions detected
- Bug #4 email cascade: not regressed ✓
- Bug #14 commitments transmission: not regressed ✓
- Bug #19 disambiguation: not regressed ✓
- ... (all 21 known ship-blockers checked)

New failure classes: 1 detected
- morning-briefing × mature_workspace: defensive_read called but skipped_lines not surfaced to user
- Likely cause: Bug #52 fix partially incomplete

VERDICT: HOLD

Recommended action: review the morning-briefing skipped_lines surface; either fix in v3.13.8.1 OR accept as known-residual-fix.

Full report: <workspace_root>/SHIP_READINESS_v3.13.8_2026-05-25.md (resolved from the operator profile)
```

## What this skill catches

**High coverage:**
- Canonical render path bypass (Bug #32 + #45 + #52 + #53 class) — synthetic invariants I1, I2, I7, I8, I9
- Substrate corruption tolerance (Sub-bug #14b family) — invariant I6 against mature_workspace fixture
- Schema compliance (Bugs #24, #34, #43, #49) — invariant I10
- Leak gate (Bugs #54, #57, #59) — invariant I5 + universal post-render scan
- Atomic-write multi-write deadlock (Bug #20) — invariant I14
- Widget ladder adherence (Bug #46) — synthetic invariants **I1** (`canonical_render_invoked`), **I2** (`no_freelance_render`) and **I16** (`file_uri_transport`). I2 is the direct successor of the retired per-skill canonical-vs-freelance ladder diff: it asserts `show_widget` is never reached off the canonical path at all, which is the property the diff was inferring. (The ladder diff retired with its skill in v0.3.1 — the mocked freelance fallback it diffed against no longer exists.)
- Action-label drift (Bug #48) — **not** a synthetic invariant. It is asserted by cr1's renderer validator (`CanonicalActionError`), which runs in the **unit tier** (`tests/run_all.py`, i.e. `battery --quick`), not here. I15 (`apply_choices_canonical_dispatch`) covers the dispatch *shape*, not the labels. Run the unit tier before trusting this gate on label drift.

**Partial coverage:**
- Voice contract violations (Bugs #16, #60) — synthetic captures chat narration; word-boundary scan applies; but LLM-driven variations limit detection
- Cross-mount corruption (Bug #55) — environmental, can't be reproduced synthetically

**NO coverage (still requires the attended tier, Cowork-side):**
- Cowork LLM judgment quality
- Voice / tone subjective assessment
- Customer-specific edge cases not in fixtures
- Cowork's prompt-pattern-matching adaptation over time
- Virgin-workspace onboarding + honest empty states (a fixture is never a first-run)
- Destructive / garbage-input probes, and the fresh-runtime skill-load canary

**Conclusion:** This skill is ~80% of pre-promote verification. The remaining 20% is the attended tier — `battery --attended`: freeform dogfood on a real workspace **plus** `battery/references/VERIFICATION_PLAN.md` walked against a fresh empty workspace.

**Read this before trusting that 20%.** It used to be driven by a skill (`verify-cr-release`, retired) that tracked position through the plan, auto-classified each pasted-back response, and emitted a verdict doc. Nothing does that now — the attended tier is walked **by hand**. So the 20% is still *addressable*, but it is no longer *enforced*: there is no mechanical guarantee that every plan item was actually run, no auto-classified findings, and no verdict artifact to point at. Two consequences for this gate:

1. **Never infer the attended tier from a PROMOTE here.** This verdict speaks to the 80% only. A PROMOTE plus an unwalked plan is an 80% ship.
2. **Make the operator say it.** Before a promote, ask what was actually walked, and record the answer in the verdict doc — "attended: dogfood only, plan not walked" is a legitimate and useful thing to write down. Silence is not coverage.

## Verdict logic

```python
def compute_ship_readiness_verdict(verdicts, regressions, new_failures) -> str:
    """
    BLOCKED — any Tier 1 ship-blocker test FAILED OR any KNOWN ship-blocker bug regressed
    HOLD — Tier 2 verifications PARTIAL OR new failure class surfaced
    PROMOTE — all Tier 1 PASS, no regressions, no new failures
    """
    tier_1_failures = [v for v in verdicts.values() if v.is_ship_blocker and v.failed]
    if tier_1_failures:
        return "BLOCKED"
    
    ship_blocker_regressions = [r for r in regressions if r.severity == "HIGH"]
    if ship_blocker_regressions:
        return "BLOCKED"
    
    tier_2_partials = [v for v in verdicts.values() if v.is_high_value and v.partial]
    if tier_2_partials or new_failures:
        return "HOLD"
    
    return "PROMOTE"
```

## Connection to V3.13.8_MASTER_PLAN

This skill operationalizes V3.13.8_MASTER_PLAN §10 Decision 5 (24h M-only smoke before promote). Instead of M watching for issues over 24h, this skill compresses the gate to ~10 minutes of automated verification + ~5 min M review of the verdict doc.

The compression doesn't ELIMINATE the smoke window — M still observes real-use behavior in Cowork over the following 24h before final promote click. The gate just adds a high-confidence automated checkpoint at the beginning of that window.

## Failure modes

**Synthetic fixtures missing:** the fixtures ship populated (`clean_workspace`/`mature_workspace`/`degraded_workspace`/`fresh_install`); if a fixture dir is absent or empty, skill returns "BLOCKED — fixtures missing" with a pointer to `synthetic-workspace-runtime-test/fixtures/README.md` and its `_generate_fixtures.py`.

**Plugin code path crashes during synthetic fire:** captured in trace; surfaces as a CRASH verdict rather than PASS/FAIL. Surfaces stack trace for operator debugging.

**Bug catalog drift:** if findings log moved or renamed, skill falls back to last-known-good catalog + flags the issue.

## Pre-promote workflow (the operator's ship ritual)

```
1. (Code session) Implement fixes per plan
2. Run pre-commit hook + tests pass
3. git push to staging main (chaletteholdings/cr1)
4. (Same Code session) ship readiness gate
5. Review SHIP_READINESS_v3.13.8.X_<date>.md
6. If PROMOTE → safe to fire ship-cr-plugin Step 9 production promote
   If HOLD → check the partial-pass items + fix in v3.13.8.X+1 OR accept residual
   If BLOCKED → must fix the blocker before any promote consideration
```

## Implementation references

- `references/verdict-logic.md` — full ship-readiness verdict decision tree
- `references/bug-catalog-parser.md` — how to extract bug records from findings log
- `references/regression-matching.md` — how to detect known-bug regressions in test failures
- Reuses `synthetic-workspace-runtime-test` fixture system + invariant catalog
