---
name: bug-regression-suite
description: "INTERNAL — accumulated test corpus + adversarial-prompt suite (one skill, two modes). Mode 1 (regression): fires a curated catalog of known-bug repro prompts against the target workspace; asserts each fix held. Mode 2 (adversarial): fires edge-case prompts designed to elicit NEW failure modes; surfaces any architectural surprises. Catalog grows over time — every new bug found becomes a permanent regression test. Target defaults to synthetic fixtures; M's actual workspace is reachable via --target=m-workspace ONLY when config/operator.json identifies the operator as M. Triggers: 'run regression suite', 'bug regression', 'red team', 'adversarial check', 'verify bugs fixed'. All substrate-modifying tests pre-snapshot + tag test_artifact=true + emit post-suite cleanup helper. Plugin-developer use only. Companions: cr-test, ship-readiness-gate."
---

# bug-regression-suite

**The accumulated test corpus for Command Room.** Every bug ever found has a canonical repro prompt in this catalog. After every release, run this suite to verify all known fixes still hold. Plus an adversarial mode that fires edge-case prompts designed to elicit NEW failure modes — the structural defense against pattern-matching adaptation.

## Why this skill exists

Per V3.13.8_MASTER_PLAN §6 Principle 5 + the 20% gap analysis: the bugs we've found over the past month show patterns Cowork could regress on with any release. Without a permanent regression catalog, every release risks reintroducing fixed bugs.

This skill is the permanent corpus. Every bug fixed in v3.13.x is in here. Every bug fixed in v3.14.x will be added. Cumulative coverage that grows over time.

The adversarial mode adds the "try to break it" complement — fire edge-case prompts that historically surface bugs (no-email persons, first-name collisions, multi-write scenarios, corrupted substrate, malformed prompts) and assert they don't produce new failures.

## When this fires

| Trigger | Mode |
|---|---|
| `run regression suite` | All known-bug repros |
| `bug regression` | Same |
| `verify bugs fixed` | Same |
| `red team` | Adversarial mode only |
| `adversarial check` | Same |
| `run regression suite --adversarial` | Both modes (regression + adversarial) |
| `run regression suite --bug-id=N` | Single-bug repro only |
| `run regression suite --target=synthetic` (default) | Against synthetic fixtures |
| `run regression suite --target=m-workspace` | Against the operator's real workspace — ONLY when the merged operator profile (`config/operator.json` + `config/operator.local.json`) has `"operator": "m"` and `allowed_targets` includes `"real"`. Any other operator: refuse this target and run synthetic. |
| `run regression suite --cleanup` | Post-suite cleanup helper |

## Behavior

### Step 0 — Pre-fire safety

**Resolve `WORKSPACE_ROOT` before anything else. Never hardcode a literal path.**

Resolution order — first hit wins, and the default is always a synthetic fixture:

1. `--workspace-root=<path>` CLI argument, if given
2. `$CR_WORKSPACE_ROOT` environment variable, if set
3. `workspace_root` in the merged operator profile — `config/operator.json`, then
   `config/operator.local.json` overlaid per-key if present (gitignored; not every operator has one)
4. **Default:** the `clean_workspace` synthetic fixture shipped in
   `skills/synthetic-workspace-runtime-test/fixtures/`

```bash
# --- operator-profile resolution (canonical pattern — keep byte-synced across skills) ---
# Locate THIS plugin's root by searching for config/operator.json, then hand python a
# NATIVE path. Two Git-Bash-on-Windows traps this is fenced against (MAINT2, 2026-07-24):
#   1. `${BASH_SOURCE[0]}` is EMPTY when an agent runs this block through a Bash tool —
#      it is not a sourced script. `dirname ""` is `.`, so the plugin root silently became
#      whatever the cwd's grandparent happened to be.
#   2. `pwd` under Git Bash yields an MSYS path (`/c/Users/…`). Native python.exe resolves
#      `/c/…` to `C:\c\…`, so BOTH config reads miss, the merged profile comes back EMPTY,
#      and resolution falls through to the synthetic fixture with NO error — an operator
#      granted `real` silently ran synthetic. `cygpath -m` yields `C:/Users/…`, which MSYS
#      bash and Windows python both read.
# Never hardcode a machine path: search, then the $CHALETTE_DEV_ROOT escape hatch, then FAIL LOUD.
_cr_native() { if command -v cygpath >/dev/null 2>&1; then cygpath -m "$1"; else printf '%s\n' "$1"; fi; }
DEV_PLUGIN_ROOT=""
for _c in "${CHALETTE_DEV_ROOT:-}" "$PWD" "$PWD/chalette-dev" "$(dirname "$PWD")" \
          ~/repos/chalette-dev/chalette-dev ~/.claude/plugins/marketplaces/*/chalette-dev; do
  [ -n "$_c" ] && [ -f "$_c/config/operator.json" ] && DEV_PLUGIN_ROOT="$(_cr_native "$_c")" && break
done
[ -n "$DEV_PLUGIN_ROOT" ] || { echo "FATAL: chalette-dev plugin root not found (no config/operator.json in any searched location). Set CHALETTE_DEV_ROOT=<plugin root> and re-run." >&2; exit 1; }
OPERATOR_CFG="$DEV_PLUGIN_ROOT/config/operator.json"
OPERATOR_OVERLAY="$DEV_PLUGIN_ROOT/config/operator.local.json"      # gitignored M-only overlay
# --- end operator-profile resolution ---
FIXTURES="$DEV_PLUGIN_ROOT/skills/synthetic-workspace-runtime-test/fixtures"

# Merged operator profile = operator.json then operator.local.json overlaid per-key.
WORKSPACE_ROOT="${CR_WORKSPACE_ROOT:-}"
if [ -z "$WORKSPACE_ROOT" ]; then
  # `or ''` is load-bearing: workspace_root ships as null, and .get(k) returns None
  # for a key that EXISTS with a null value — so expanduser(None) would raise TypeError.
  # `sys.exit` on zero files read: an empty merged profile must NEVER pass silently.
  WORKSPACE_ROOT=$(python -c "import json,os,sys
p={}; _n=0
for f in ('$OPERATOR_CFG','$OPERATOR_OVERLAY'):
    if os.path.exists(f): p.update(json.load(open(f))); _n+=1
if not _n: sys.exit('FATAL: operator profile unreadable at $OPERATOR_CFG')
print(os.path.expanduser(p.get('workspace_root') or ''))") || exit 1
fi
# Default: synthetic fixture. Never a literal machine path.
[ -z "$WORKSPACE_ROOT" ] && WORKSPACE_ROOT="$FIXTURES/clean_workspace"

# Refuse a real workspace unless the merged profile grants allowed_targets: ["real"].
MAY_TARGET_REAL=$(python -c "import json,os,sys
p={}; _n=0
for f in ('$OPERATOR_CFG','$OPERATOR_OVERLAY'):
    if os.path.exists(f): p.update(json.load(open(f))); _n+=1
if not _n: sys.exit('FATAL: operator profile unreadable at $OPERATOR_CFG')
print('yes' if 'real' in p.get('allowed_targets',[]) else 'no')") || exit 1
case "$WORKSPACE_ROOT" in
  "$FIXTURES"/*) : ;;                       # synthetic — always allowed
  *) [ "$MAY_TARGET_REAL" = "yes" ] || {
       echo "REFUSING non-synthetic target '$WORKSPACE_ROOT' — operator.json does not grant allowed_targets: [\"real\"]." >&2
       exit 2
     } ;;
esac

SNAPSHOT_DIR="$WORKSPACE_ROOT/_hq/.system/regression-snapshots/$(date +%Y-%m-%dT%H-%M-%S)"
mkdir -p "$SNAPSHOT_DIR"

cp "$WORKSPACE_ROOT/_hq/data/entities.json" "$SNAPSHOT_DIR/entities.json.before"
cp "$WORKSPACE_ROOT/_hq/data/events.jsonl" "$SNAPSHOT_DIR/events.jsonl.before"
cp "$WORKSPACE_ROOT/_hq/data/aliases.json" "$SNAPSHOT_DIR/aliases.json.before" 2>/dev/null || true
wc -l "$WORKSPACE_ROOT/_hq/data/events.jsonl" > "$SNAPSHOT_DIR/baseline_counts.txt"
```

Before running ANY substrate-modifying test, snapshot the workspace's mutable substrate (above).

Snapshot path captured for post-fire diff + cleanup reference.

### Step 1 — Load the bug catalog

Catalog lives in `references/bug-catalog.md` — markdown file with one entry per known bug. Format:

```markdown
## Bug #19 — find_existing_person fuzzy-name match silent corruption

**Mode:** regression
**Severity:** SHIP-BLOCKER
**Fixed in:** v3.13.7

**Trigger (single-token, against workspace with multi-name collision):**
`add a new person: Daniel`

**Expected behavior (post-fix):**
- Cowork detects existing Daniels (Sample, Stone, others)
- Surfaces disambiguation widget (Path B freelance elicit form OR canonical disambiguation per v3.13.8)
- REFUSES to silent-create

**Expected pass signals (response classifier):**
- Disambiguation widget OR form appears
- "found N existing Daniels" or similar language
- No new person_NNN record minted without explicit confirmation

**Expected fail signals (regression):**
- Silent person creation
- Existing Daniel record updated with new context (Sample overwritten with Stone context)
- MultipleCandidatesError not raised

**Safety:** modifies entities.json. PRE-snapshot required. Cleanup: delete any new person record created via disambiguation widget click; if user accidentally clicked through.

**Variants:**
- Variant A: single-token (the canonical test)
- Variant B: full-name "Daniel Stone" (should NOT trigger disambiguation — full-name distinct)
- Variant C: alias-like "Dan" (should trigger disambiguation if "Dan" matches multiple aliases)
```

See `references/bug-catalog.md` for the full 60+-entry catalog.

### Step 2 — Per-bug fire + classify

For each bug entry (or filtered subset per `--bug-id` flag):

1. Emit the trigger prompt to M (M pastes into Cowork)
2. Wait for M's paste-back of Cowork response
3. Run response classifier (see `references/response-classifier.md`)
4. Verdict: PASS (fix held) / FAIL (regression detected) / PARTIAL (works by good faith, no structural guarantee)
5. Log to findings + advance to next bug

Adversarial mode:
- Picks bugs from catalog tagged `mode: adversarial`
- These are edge-case prompts that have historically surfaced bugs
- Asserts no new failures — if a NEW pattern surfaces, log as candidate-bug for v3.14.x

### Step 3 — Cross-skill interactions sub-suite (lighter than cross-skill-interaction-test)

A few bugs require multi-fire sequences. Catalog flags these:

```markdown
## Bug #51 — show-my-list cascade-close to source commitment

**Mode:** regression
**Severity:** SHIP-BLOCKER
**Fixed in:** v3.13.8 §2.9

**Sequence:**
1. Fire: `show my list`
2. Wait for widget
3. Click `resolved` on a discuss-wrapper item (note its source commitment seq from data.commitment_id)
4. Fire: `morning brief`
5. Verify the underlying source commitment does NOT appear in "you owe" count

**Expected pass:**
- Source commitment_resolved event written ALONGSIDE wrapper close
- Morning brief reflects the closure
```

The skill drives M through the sequence + classifies the multi-fire response.

### Step 4 — Adversarial mode

Adversarial prompts test EDGE CASES designed to elicit failures. Catalog:

```markdown
## Adversarial #1 — Email to person with no email on file

**Mode:** adversarial
**Target bug class:** Bug #44 (dead-chrome) + related
**Trigger:** `draft email to [person with no email]`
**Expected pass:** add-email-then-send recovery widget OR clear "no email on file, add one to enable send" message
**Expected fail:** dead-chrome Send button OR silent gmail call failing

## Adversarial #2 — Disambiguation with 3+ Daniels
**Trigger:** `add a new person: Daniel`
**Expected pass:** disambiguation surface; never silent-create
**Expected fail:** silent-create OR existing-Daniel updated

## Adversarial #3 — Multi-write update-bridge migration
**Setup:** ensure 8 malformed lines in events.jsonl OR seed them
**Trigger:** trigger update-bridge migration phase
**Expected pass:** corruption_recovery + spaeth-fix + brain_name prompt all complete under single lock
**Expected fail:** deadlock OR partial-state

## Adversarial #4 — Commitments at 218+ items
**Trigger:** `commitments` against accumulated workspace
**Expected pass:** widget renders with 7-item cap + show more; transmits successfully
**Expected fail:** socket-closed error OR oversize widget OR cap not enforced

[catalog continues — 30+ adversarial entries]
```

### Step 5 — Aggregate verdict

After all selected bugs fire:

```
Bug Regression Suite — run at 2026-05-26T10:00:00Z

Mode: regression
Target: <resolved workspace_root> (operator profile)
Catalog: 14 Tier 1 ship-blockers + 18 Tier 2 + 12 Tier 3 adversarial = 44 tests

Results:
PASS: 41/44 (93%)
FAIL: 0/44 (0 regressions!)
PARTIAL: 3/44

Partial details:
- Bug #46 widget ladder: ladder codified in EMAIL_DRAFT_PROTOCOL.md but render_path_router.py not yet enforced at runtime
- Bug #60 process narration: Some surfaces still leak project_NNN; voice scrub partial
- Bug #61 telemetry capture: 5/7 orchestrators emit pack_run correctly; 2 still skip

No regressions detected. v3.13.8 ship holds.

Pending v3.13.8.1 (or follow-up):
- Bug #46 render_path_router enforcement
- Bug #60 voice scrub completion (2 orchestrators)
- Bug #61 pack_run emission (2 orchestrators)

Full report: <workspace_root>/REGRESSION_SUITE_2026-05-26.md (resolved from the operator profile)
```

### Step 6 — Post-suite cleanup

If `--cleanup` flag fired, OR M asks "cleanup test artifacts":

```bash
# Diff pre/post snapshot
diff "$SNAPSHOT_DIR/events.jsonl.before" "$WORKSPACE_ROOT/_hq/data/events.jsonl" \
  | grep "^>" | jq -r '. | select(.data.test_artifact == true) | .seq' > /tmp/test_seqs

# Mark events as archived (don't delete — preserve audit trail)
for seq in $(cat /tmp/test_seqs); do
    # Append archive event
    ...
done

# For person/org records created during testing
jq '.entities.people | to_entries | .[] | select(.value.test_artifact == true) | .key' \
  "$WORKSPACE_ROOT/_hq/data/entities.json" > /tmp/test_person_ids

for pid in $(cat /tmp/test_person_ids); do
    # Mark archived + test_artifact via people_writer
    ...
done
```

Cleanup is conservative — marks artifacts as archived rather than deleting. Audit trail preserved.

## Catalog maintenance (the accumulating part)

When a NEW bug surfaces in production:

1. M adds entry to `references/bug-catalog.md` (this used to also happen autonomously from the retired `verify-cr-release`; it is a manual step now)
2. Entry includes: trigger prompt, expected pass/fail signals, severity, fix version reference
3. The bug is now PERMANENTLY tested on every future regression-suite run

This is the structural defense against re-introducing bugs. **The catalog never shrinks** — only grows.

Catalog seed (v3.13.8 ship state): 61 entries covering Bugs #1-#61 + sub-bugs.

## Safety: substrate-modifying tests

**Critical:** running this against M's real workspace WILL create test artifacts unless explicit care is taken. Every catalog entry declares:

- `modifies_substrate: true | false`
- `expected_writes: [event_type_1, event_type_2, ...]`
- `cleanup_strategy: archive_via_test_artifact_flag | delete_post_fire | manual_review`

The skill respects these flags + executes cleanup per strategy.

Substrate-modifying tests (e.g., Bug #19 disambiguation) MUST snapshot pre-fire + tag writes with `test_artifact: true`. Read-only tests (e.g., Bug #11 entity_resolve query) skip the snapshot.

## Modes summary

| Mode | What it tests | When to use |
|---|---|---|
| Default (regression) | All known-bug fixes still hold | Every release before promote |
| Adversarial | Edge cases that historically broke things | Periodically, especially before major releases |
| Single-bug | One bug's repro test | Debugging a specific bug, e.g., after a fix |
| Cross-skill | Sequenced multi-fire tests | When fixing temporal substrate bugs |

## Integration with ship-readiness-gate

ship-readiness-gate orchestrates this skill as part of its post-push verification battery. After a push to ChaletteHQ/cr1 main, ship-readiness-gate runs:
1. synthetic-workspace-runtime-test (against fixtures)
2. **bug-regression-suite (against the resolved workspace)** ← this skill
3. bug-catalog cross-reference (known-bug regression vs new failure class)
4. Aggregate PROMOTE / HOLD / BLOCKED verdict

## What this skill does NOT cover

- Cowork's LLM-driven prose synthesis quality (that's the attended tier — `cr test --attended`, walked by hand)
- Customer-shape diversity (M's workspace ≠ all customers; v3.14.x customer-shape fixtures fill this)
- Cross-skill temporal interactions across time (cross-skill-interaction-test covers this — runs sequences across minutes/hours/days)
- Performance at scale (scale-stress-test)
- 24h smoke-watch passive observation (smoke-watch)

Each of those gaps has a dedicated skill — bug-regression-suite is the canonical known-bug catalog.

## References

- `references/bug-catalog.md` — the canonical catalog (60+ entries, growing)
- `references/adversarial-prompts.md` — edge-case prompts catalog (30+ entries)
- `references/cleanup-helper.md` — post-suite cleanup logic
- `references/snapshot-format.md` — pre/post snapshot format + diff logic
