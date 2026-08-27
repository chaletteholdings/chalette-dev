# BENCH1 v1.5 — supervised live-workspace replay (staged 2026-08-27)

Purpose: confirm the synthetic battery's DIRECTION on live workload. Counts
and deltas only — no transcript content, no names, no precision/recall claims
(real data has no ground-truth labels). Runs supervised, on M's machine, with
M present. Fixtures untouched; cr1-canonical read-only (the replay builds its
own sandbox — see cr1 `scripts/README_REPLAY.md`, the proven rig).

## Staged inputs (verified present 2026-08-27)

- Transcript cache from the EXCH1 replay: 71 files at
  `Penelopes Brain/_hq/audit-reports/replay_v515_v519_2026-08-26/transcripts/`
  — reuse; do NOT re-fetch unless M widens the window.
- Replay rig: `~/repos/cr1-canonical/scripts/replay_captures.py` (read-only
  sandbox; refuses meetings whose transcript fails the fusion back-check).
- Summarizer: `scripts/v15_counts.py` (this skill) — counts only, reason
  strings bucketed by regex and never echoed, receipt-limited output.

## M's half hour (run these with M present)

```bash
# 1. Replay the real captures through current canonical code (~minutes)
python ~/repos/cr1-canonical/scripts/replay_captures.py \
    --plugin-root ~/repos/cr1-canonical/command-room \
    --workspace "C:/Users/matth/Desktop/Claude/Penelopes Brain" \
    --transcripts "C:/Users/matth/Desktop/Claude/Penelopes Brain/_hq/audit-reports/replay_v515_v519_2026-08-26/transcripts" \
    --since 2026-08-08 \
    --out "<out-dir>/bench_v15.json" --label bench1-v15

# 2. Reduce to counts (the only thing that leaves the machine)
python <chalette-dev>/chalette-dev/skills/cr-benchmark/scripts/v15_counts.py \
    --replay "<out-dir>/bench_v15.json" --out-dir "<out-dir>"

# 3. M eyeballs V15_SUMMARY.md; the raw bench_v15.json STAYS in the
#    audit-reports dir and is never committed to chalette-dev.
```

`<out-dir>` = `Penelopes Brain/_hq/audit-reports/BENCH1_V15_<date>/`.

## What the counts confirm (direction-checks vs the battery)

1. **Rail dominance**: share of open-lane vs observed routing on real
   captures — the battery says dated items dominate and the observed tier is
   small; the live distribution should rhyme.
2. **Review-lane composition**: the battery found the queue filling with
   person-resolution failures rather than hedges (filed as
   BUG_review-lane-underbooks-hedged); the live `review_lane_reason_buckets`
   either corroborates or weakens that.
3. **Substrate discipline**: replayed lanes vs historical lanes (drift =
   `historical_lane` != `replay_lane`) — countable, no content.

## What goes in the results doc

One paragraph, counts only: "direction validated on a live operator
workspace over N meetings (M scored with verified transcripts): <lane
distribution>, <review composition>." Nothing else crosses over.

## Hard rules

- M present for the whole run (ruled: supervised).
- The workspace is READ: any git/status change in cr1-canonical or any write
  outside `<out-dir>` aborts the session.
- bench_v15.json contains real titles/evidence — it never leaves
  `_hq/audit-reports/`, never enters chalette-dev, never gets pasted.
