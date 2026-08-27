#!/usr/bin/env python3
"""BENCH1 v1.5 — counts-only summarizer for a live-workspace capture replay.

Reads the JSON that cr1's scripts/replay_captures.py emits over M's REAL
workspace and produces ONLY counts and percentages — no titles, no names, no
evidence text, nothing forwardable-restricted. This is the entire bridge
between the live validation layer and the official (synthetic) benchmark:
one summary paragraph's worth of denominated counts.

Privacy rule enforced by construction: the only free-text field this script
ever reads is `reason`, and it is bucketed by regex class, never echoed.

Usage:
    python v15_counts.py --replay bench_v15.json --out-dir <dir>

Writes V15_COUNTS.json and V15_SUMMARY.md into --out-dir. Refuses to
overwrite an existing V15_COUNTS.json (receipt-limited, same discipline as
precision_report.py).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

REASON_BUCKETS = [
    ("no_person_record", re.compile(r"has no person record", re.I)),
    ("fusion", re.compile(r"fusion|evidence.*(?:not|cannot).*(?:found|locat)", re.I)),
    ("floor", re.compile(r"floor|discussed|retold|never accepted|no (?:identifiable )?owner|"
                         r"no concrete deliverable|nothing depends", re.I)),
    ("caution_rail", re.compile(r"carries a due date or money|always surfaces", re.I)),
    ("party", re.compile(r"you are a party|between other people|whose this is|third", re.I)),
]


def bucket_reason(reason: str) -> str:
    r = (reason or "").strip()
    if not r:
        return "(none)"
    for name, pat in REASON_BUCKETS:
        if pat.search(r):
            return name
    return "other"


def pct(n: int, d: int) -> str:
    return f"{n}/{d} ({100 * n / d:.1f}%)" if d else f"{n}/0 (n/a)"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--replay", required=True)
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    if (out_dir / "V15_COUNTS.json").exists():
        raise SystemExit("REFUSED: V15_COUNTS.json already exists in out-dir "
                         "(receipt-limited; use a fresh dir for a re-run)")

    d = json.loads(Path(args.replay).read_text(encoding="utf-8"))
    rows = d.get("rows") or []
    n = len(rows)

    lanes = Counter((r.get("replay_lane") or "(none)") for r in rows)
    hist = Counter((r.get("historical_lane") or "(none)") for r in rows)
    floor_codes = Counter(r.get("floor_code") for r in rows if r.get("floor_code"))
    reasons = Counter(bucket_reason(r.get("reason")) for r in rows)
    dupes = sum(1 for r in rows if r.get("duplicate"))
    scored_with_transcript = sum(1 for r in rows if r.get("transcript"))

    review_rows = [r for r in rows if (r.get("replay_lane") or "") == "review"]
    review_reasons = Counter(bucket_reason(r.get("reason")) for r in review_rows)

    counts = {
        "generated_from": Path(args.replay).name,
        "label": d.get("label"),
        "plugin_root": str(d.get("plugin_root", "")),
        "meetings": d.get("meetings"),
        "meetings_with_transcript": d.get("meetings_with_transcript"),
        "n_rejected_transcript_meetings": len(d.get("rejected_transcripts") or []),
        "n_items": d.get("n_items", n),
        "rows_scored": n,
        "rows_with_transcript_check": scored_with_transcript,
        "replay_lane": dict(lanes),
        "historical_lane": dict(hist),
        "floor_codes": dict(floor_codes),
        "reason_buckets": dict(reasons),
        "review_lane_reason_buckets": dict(review_reasons),
        "duplicates": dupes,
        "_privacy": "counts only; no titles, names, or evidence text",
    }
    (out_dir / "V15_COUNTS.json").write_text(
        json.dumps(counts, indent=2) + "\n", encoding="utf-8")

    md = ["# BENCH1 v1.5 — live-workspace replay, counts only", ""]
    md.append(f"Source: `{counts['generated_from']}` (label `{counts['label']}`), "
              f"{counts['meetings']} meetings, {counts['meetings_with_transcript']} scored "
              f"with a verified transcript, {counts['n_rejected_transcript_meetings']} refused "
              f"(transcript could not be verified — never scored).")
    md.append("")
    md.append("| Lane (replayed) | Count |")
    md.append("|---|---|")
    for lane, c in sorted(lanes.items(), key=lambda kv: -kv[1]):
        md.append(f"| {lane} | {pct(c, n)} |")
    md.append("")
    md.append("Review-lane composition (why rows are in the queue):")
    for b, c in sorted(review_reasons.items(), key=lambda kv: -kv[1]):
        md.append(f"- {b}: {pct(c, len(review_rows))}")
    md.append("")
    md.append(f"Duplicates collapsed: {pct(dupes, n)}. Floor codes: "
              + (", ".join(f"{k} {v}" for k, v in floor_codes.most_common()) or "(none)"))
    md.append("")
    md.append("_Counts only; no meeting content leaves the machine. Direction-check "
              "against the synthetic battery lives in the results doc._")
    (out_dir / "V15_SUMMARY.md").write_text("\n".join(md) + "\n", encoding="utf-8")

    print(f"wrote {out_dir / 'V15_COUNTS.json'}")
    print(f"wrote {out_dir / 'V15_SUMMARY.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
