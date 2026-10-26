---
name: scale-stress-test
description: "INTERNAL — verifies Command Room helpers degrade gracefully at scale. Loads an events.jsonl (the operator's real workspace when allowed_targets includes 'real', else the populated synthetic mature_workspace fixture) + runs canonical helpers (load_open_commitments, entity_resolve, brief_writer) + measures latency / memory / correctness. Identifies performance cliffs before customers hit them. Triggers: 'scale stress test', 'performance check', 'helper scale audit'. Assumes file-URI transport + brief_writer migrations have landed. Plugin-developer use only."
---

# scale-stress-test

> **Team toolkit (chalette-dev).** Anyone on the team may run this. A contractor runs it against the synthetic fixtures or a copied test brain only, never a real client folder, and never ships or promotes. The owner's own workspace needs the owner's yes in the chat. Who is running is read the way `cr1-test` reads it, from `config/operator.json`.

**Performance verification at real data scale.** Loads an events.jsonl + measures canonical helper performance + identifies performance cliffs.

> **Operator profile (read first).** Load `config/operator.json`, then overlay `config/operator.local.json` per-key if it exists (gitignored; the operator's local overlay — not every operator has one). Resolve the events source: if the merged `allowed_targets` includes `"real"`, use `<workspace_root>/_hq/data/events.jsonl`; otherwise use the bundled synthetic `mature_workspace` fixture — this skill has a genuine synthetic mode and never assumes a live workspace.
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
> if "real" in op.get("allowed_targets", []) and op.get("workspace_root"):
>     events_path = os.path.join(os.path.expanduser(op["workspace_root"]), "_hq/data/events.jsonl")
> else:
>     events_path = os.path.join(SKILL_PLUGIN_ROOT, "skills/synthetic-workspace-runtime-test/fixtures/mature_workspace/_hq/data/events.jsonl")
> ```

**STATUS: SCAFFOLD.** Implementation deferred to a dedicated session. Triggers + outline below.

## When this fires (post-implementation)

| Trigger | Context |
|---|---|
| `scale stress test` | Run all helpers against the resolved events.jsonl (real workspace or synthetic fixture) |
| `performance check` | Same |
| `helper scale audit` | Same |
| `scale stress test --helper=load_open_commitments` | Single helper deep dive |
| `scale stress test --simulated --events=20000` | Synthesize a 20K-event events.jsonl + run against it |

## Behavior (post-implementation TODO)

### Step 1 — Read the resolved events.jsonl

```python
# events_path resolved in the operator preamble above (real workspace_root or synthetic mature_workspace fixture)
line_count = sum(1 for _ in open(os.path.expanduser(events_path)))
file_size = events_path.stat().st_size
print(f"Events: {line_count} lines, {file_size} bytes")
```

### Step 2 — Run canonical helpers + measure

```python
import time
helpers_to_test = [
    ("load_open_commitments", lambda: cru_match.load_open_commitments(workspace_root)),
    ("entity_resolve_all", lambda: entity_resolve.resolve_all("Daniel", workspace_root)),
    ("brief_writer_memo", lambda: brief_writer.make_brief(brief_kind="memo", workspace_root=workspace_root, ...)),
    # ... 10+ canonical helpers
]

for name, fn in helpers_to_test:
    start = time.perf_counter()
    result = fn()
    duration = (time.perf_counter() - start) * 1000  # ms
    print(f"{name}: {duration:.1f}ms")
```

### Step 3 — Identify performance cliffs

For each helper, measure:
- p50 / p95 / p99 latency
- Memory peak
- Result correctness (vs expected)

Surface helpers above acceptable thresholds:

```
Performance audit — events.jsonl at 1830 lines

Helper                          p50    p95    p99    Memory   Cliff?
load_open_commitments           45ms   120ms  340ms  4.2 MB   no
entity_resolve_all (10 queries) 18ms   42ms   78ms   1.1 MB   no
brief_writer make_brief         220ms  680ms  1.2s   12 MB    🟡 monitor
chat_output_renderer (70KB)     85ms   210ms  450ms  5.8 MB   no

Verdict: load_open_commitments + entity_resolve + brief_writer scale healthily at current substrate size. brief_writer trending toward concern at >2000-line events.jsonl. Schedule v3.14.x speed-pass optimization.

Recommend re-running this audit at every 1000-line growth threshold.
```

### Step 4 — Project growth

```python
# Linear regression on past pack_run telemetry events to project growth rate
# If events.jsonl grew 100 lines/week → at 6 months: ~4500 lines
# Estimate latency at projected scale using current p99 + growth factor
```

### Step 5 — Simulated extreme-scale fixture

```python
# Generate synthetic 20K-event events.jsonl (mostly placeholder events) + run helpers against it
# This catches algorithmic complexity issues that linear scale won't surface yet
```

## Implementation TODO

Substantive code needed:
1. Performance instrumentation wrapper around canonical helpers (time + memory)
2. Synthetic events.jsonl generator (scale up to N events without taking real customer data shape)
3. Statistical reporting (p50/p95/p99 + cliff detection heuristics)
4. Growth projection from pack_run telemetry trends
5. Cliff threshold definitions per helper (what's "acceptable" latency)

Estimated implementation: 2-3 hours dedicated session.

## What this skill catches

- Algorithmic complexity bugs (O(n²) in canonical helpers)
- Memory cliffs at scale
- Performance regressions from one release to next

## What it doesn't catch

- Bugs that only surface in production environment (Cowork has different resource constraints than the operator's local Code)
- Cross-skill performance interactions
- Network latency (everything is local)

## Connection to V3.13.8_MASTER_PLAN

Per §9 v3.14.x performance / speed pass — this skill operationalizes the speed-pass priority documentation. Catches what needs optimizing before customers complain.
