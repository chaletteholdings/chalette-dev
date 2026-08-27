#!/usr/bin/env python3
"""BENCH1 deterministic scorer.

Compares run artifacts (chat output, appended events, created files) against
the frozen transcript labels and emits countable metrics only. The same code
scores both arms; there is no arm-specific scoring logic, only arm-specific
CHANNELS (Arm A additionally has an event stream; Arm B only has chat/files).

Every per-item judgment records the evidence line it was made from, so an
adversarial reviewer (or a human) can audit each count without re-running
anything.

Metrics per run:
  extraction   confusion of expected route (book/review/observed/reject)
               vs assigned route, from events (A) and commitment-shaped chat
               lines (both arms); plus unplanted captures
  entities     right / wrong / missed per labeled mention
  hallucination  name-shaped bigrams in output that exist nowhere in the
               fixture roster, known-unknowns, or org list
  leaks        survivals of the forbidden-token catalog in user-facing output
  cost         wall clock + tokens (copied from run_meta)

Usage:
    python bench_scorer.py --runs-dir ../runs [--only RUN_ID] [--cr1 PATH]
Writes <run_dir>/scorecard.json per run and <runs-dir>/scoreboard.{json,md}.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL_ROOT = HERE.parent
LABELS_DIR = SKILL_ROOT / "fixtures" / "bench_transcripts" / "labels"
FIXTURES_ROOT = SKILL_ROOT.parent / "synthetic-workspace-runtime-test" / "fixtures"

KNOWN_UNKNOWNS = {"Skyler Stone", "Rio Stone"}

# ---------------------------------------------------------------------------
# Forbidden-token catalog. Source of truth at runtime is cr1's
# shared/scripts/docx_leak_scanner.py (--cr1 imports it live); this embedded
# copy mirrors its _FORBIDDEN_PATTERNS plus the response-classifier leak
# signals, and is the fallback when no cr1 clone is available.
# ---------------------------------------------------------------------------
EMBEDDED_LEAK_PATTERNS = {
    "internal_id": r"\b(?:project|person|org|event|thread)_\d+\b",
    "commitment_id": r"\bcmt_[0-9A-Za-z]{6,}\b|\bcommitment_seq_\d+\b",
    "substrate_path_events": r"\bevents\.jsonl\b",
    "substrate_path_entities": r"\bentities\.jsonl?\b",
    "substrate_path_aliases": r"\baliases\.json\b",
    "substrate_path_hq": r"\b_hq/(?:data|\.system|skills)\b",
    "voice_phase": r"\bPhase \d+\b",
    "voice_tier": r"\bTier \d+\b",
    "voice_stop_contract": r"\bSTOP_CONTRACT\b",
    "voice_orchestrator": r"\borchestrator\b",
    "voice_bootloader": r"\bbootloader\b",
    "voice_validator_passed": r"\bvalidator passed\b",
    "voice_classifier": r"\bclassification_confidence\b",
    "confidence_score": r"\b0\.\d{1,3}\s+confidence\b|\bconfidence[:=]\s*0\.\d+\b",
    "mojibake": r"â€|Ã©|â€™",
}

# Commitment-shaped chat line: used for the CHAT channel of both arms, so a
# mere mention of a distractor keyphrase ("we're not tracking snacks") does
# not count as a capture. Fixed, arm-symmetric, documented in the rubric.
COMMITMENT_LINE = re.compile(
    r"(\bwill\b|\bowes?\b|\bto\s+(?:send|write|book|schedule|call|post|approve|"
    r"compile|record|update|finish|cancel|circulate|deliver|introduce|pull|"
    r"draft|process|sign|get)\b|\bby\s+(?:monday|tuesday|wednesday|thursday|"
    r"friday|saturday|sunday|tomorrow|tonight|today|this week|next week|"
    r"month end|end of week|end of day)\b|\baction item\b|\bcommitment\b|"
    r"\bfollow[- ]?up\b|\btask\b|\bdue\b|\[ \]|"
    # hedge markers: a review-lane item surfaced with its own hedge language
    # is a capture. Deliberately NOT here: "aspirational"/"hedged"/"someday" --
    # those words mark dismissal roundups ("Someday/aspirational: X, Y, Z"),
    # and counting them made correct rejections score as false captures in
    # the pilot. Per-owner hedged rows are covered by the arrow-bullet shape.
    r"\bmight\b|\bcould\b|\btentative\b|\bno promises\b|\bpending\b)",
    re.IGNORECASE)

NAME_BIGRAM = re.compile(r"\b([A-Z][a-z]+) ([A-Z][a-z]+)\b")

# English words that legitimately start capitalized mid-prose; bigrams whose
# halves are both common sentence words are not names.
NONNAME_WORDS = {
    "The", "This", "That", "These", "Those", "There", "Here", "What", "When",
    "Where", "Who", "Why", "How", "And", "But", "Also", "Then", "Next", "First",
    "Second", "Third", "Last", "New", "Old", "One", "Two", "Three", "Monday",
    "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday",
    "January", "February", "March", "April", "May", "June", "July", "August",
    "September", "October", "November", "December", "Morning", "Evening",
    "Today", "Tomorrow", "Tonight", "Week", "Board", "Command", "Room",
    "Action", "Items", "Open", "Review", "Summary", "Meeting", "Meetings",
    "Notes", "Brief", "Inbox", "Calendar", "Email", "Emails", "Commitments",
    "Key", "Quick", "Full", "All", "No", "Not", "None", "Item", "Status",
    "Due", "Owner", "Needs", "Waiting", "Done", "Noise", "Reply", "Sync",
    "Series", "Hiring", "Slate", "Pricing", "Platform", "Customer", "Annual",
    "Vendor", "Brand", "Data", "Partner", "Support", "Compliance", "Market",
    "Retention", "Cadence", "Raise", "Migration", "Advisory", "Planning",
    "Consolidation", "Hygiene", "Program", "Rework", "Pass", "Expansion",
    "Push", "Refresh", "Wrap", "Friday", "Everything", "Nothing", "Something",
}


def load_leak_patterns(cr1: Path | None) -> dict[str, str]:
    pats = dict(EMBEDDED_LEAK_PATTERNS)
    if cr1 is not None:
        scripts = cr1 / "command-room" / "shared" / "scripts"
        if scripts.exists():
            sys.path.insert(0, str(scripts))
            try:
                import docx_leak_scanner  # type: ignore
                live = getattr(docx_leak_scanner, "_FORBIDDEN_PATTERNS", None)
                if isinstance(live, dict):
                    items = list(live.items())
                elif live:
                    # list of (name, pattern) tuples, or bare patterns
                    items = [tuple(x) if isinstance(x, (tuple, list)) and len(x) == 2
                             else (f"live_{i}", x) for i, x in enumerate(live)]
                else:
                    items = []
                for name, pat in items:
                    pats[str(name)] = pat if isinstance(pat, str) else getattr(pat, "pattern", str(pat))
            except Exception as exc:
                print(f"note: live leak-pattern import failed ({exc}); using embedded catalog")
    return pats


def load_labels() -> list[dict]:
    labs = []
    for f in sorted(LABELS_DIR.glob("*.labels.json")):
        labs.append(json.loads(f.read_text(encoding="utf-8")))
    if not labs:
        raise SystemExit(f"FATAL: no labels found under {LABELS_DIR}")
    return labs


def load_roster(fixture: str) -> tuple[set[str], set[str]]:
    ents = json.loads((FIXTURES_ROOT / fixture / "_hq" / "data" / "entities.json")
                      .read_text(encoding="utf-8"))
    names = {p["canonical_name"] for p in ents["entities"]["people"]}
    orgs = {o["canonical_name"] for o in ents["entities"]["orgs"]}
    return names, orgs


def read_run(run_dir: Path) -> dict:
    meta = json.loads((run_dir / "run_meta.json").read_text(encoding="utf-8"))
    chat = (run_dir / "chat.txt").read_text(encoding="utf-8") if (run_dir / "chat.txt").exists() else ""
    if (run_dir / "chat2.txt").exists():  # confirm-turn output scores with turn 1
        chat += "\n" + (run_dir / "chat2.txt").read_text(encoding="utf-8")
    events = []
    ep = run_dir / "events_diff.jsonl"
    if ep.exists():
        for line in ep.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                ev = json.loads(line)
                if isinstance(ev, dict):
                    events.append(ev)
            except json.JSONDecodeError:
                pass
    artifact_text = ""
    art = run_dir / "artifacts"
    if art.exists():
        for f in art.rglob("*"):
            if f.is_file() and f.suffix.lower() in (".md", ".txt", ".json", ".html", ".jsonl", ".csv"):
                try:
                    artifact_text += "\n" + f.read_text(encoding="utf-8", errors="replace")
                except OSError:
                    pass
    return {"meta": meta, "chat": chat, "events": events, "artifact_text": artifact_text}


# ------------------------------------------------------------------ channels

def event_route(ev: dict) -> str | None:
    t = ev.get("type")
    data = ev.get("data") or {}
    if t == "commitment_observed" or (t == "commitment" and data.get("tier") == "observed"):
        return "observed"
    if t == "commitment":
        if data.get("pending_review") or data.get("status") == "pending_review":
            return "review"
        return "book"
    if t == "commitment_review_proposed":
        return "review"
    return None


def event_text(ev: dict) -> str:
    data = ev.get("data") or {}
    return " ".join(str(data.get(k, "")) for k in ("title", "text", "evidence", "gist"))


COMMITMENT_TABLE_HEADER = re.compile(
    r"^\s*\|.*\b(commitments?|owed|owes|owner|due|action|task|deliverable)\b",
    re.IGNORECASE)


def find_chat_capture(chat: str, keyphrase: str) -> str | None:
    """Return the commitment-shaped output line containing the keyphrase, if any.

    Two shapes count: a prose line matching COMMITMENT_LINE, or a row of a
    commitment-shaped markdown table (models often render captures as tables;
    the first pilot showed a pure-table output scoring 0 recall without this).
    """
    kp = keyphrase.lower()
    has_commitment_table = any(COMMITMENT_TABLE_HEADER.search(ln)
                               for ln in chat.splitlines())
    for line in chat.splitlines():
        if kp not in line.lower():
            continue
        if COMMITMENT_LINE.search(line):
            return line.strip()
        if has_commitment_table and line.lstrip().startswith("|"):
            return line.strip()
        # Arrow-bullet capture row: "- **Owner** → deliverable — "quote""
        stripped = line.lstrip()
        if stripped.startswith(("-", "*", "•")) and ("→" in line or "->" in line):
            return line.strip()
    return None


def assign_route(run: dict, keyphrase: str, alts: list[str] | None = None) -> tuple[str, str]:
    """(assigned_route, evidence). Events channel wins when present.

    `alts` are paraphrase aliases (label-defined) matched the same way as the
    primary keyphrase — model output compresses wording ("COO" for "chief
    operating officer", hyphenation, dropped articles); the primary keyphrase
    remains the transcript anchor and the uniqueness-validated key."""
    phrases = [keyphrase.lower()] + [a.lower() for a in (alts or [])]
    for ev in run["events"]:
        r = event_route(ev)
        if r and any(p in event_text(ev).lower() for p in phrases):
            return r, json.dumps({k: ev.get(k) for k in ("seq", "type")}) + " " + event_text(ev)[:160]
    chat_all = run["chat"] + "\n" + run["artifact_text"]
    for p in phrases:
        line = find_chat_capture(chat_all, p)
        if line:
            return "chat_capture", line[:200]
    full = chat_all.lower()
    if any(p in full for p in phrases):
        return "mentioned_only", ""
    return "absent", ""


def score_extraction(run: dict, labels: list[dict]) -> dict:
    rows = []
    for lab in labels:
        for item in lab["planted"]:
            assigned, evidence = assign_route(run, item["keyphrase"], item.get("alts"))
            rows.append({
                "label_id": item["label_id"],
                "expected": item["expected_route"],
                "rail_shadowed": bool(item.get("rail_shadowed")),
                "assigned": assigned,
                "evidence": evidence,
            })

    def n(expected, assigned_set):
        return sum(1 for r in rows if r["expected"] == expected and r["assigned"] in assigned_set)

    captured = {"book", "review", "chat_capture"}
    counts = {
        # owner-lane recall: book/review planted items that surfaced as captures
        "book_expected": sum(1 for r in rows if r["expected"] == "book"),
        "book_captured": n("book", captured),
        "book_exact": n("book", {"book"}),
        "review_expected": sum(1 for r in rows if r["expected"] == "review"),
        "review_captured": n("review", captured),
        "review_exact": n("review", {"review"}),
        # Observed accounting splits on the SHIPPED caution-rail precedence
        # (capture_gate.classify_capture:870, pinned by run_w4c_capture_gate_test):
        # a dated third-party item CANNOT reach the observed tier, so for
        # rail_shadowed labels the shipped-correct outcome is the open lane.
        # Only un-dated third-party items test the observed tier itself.
        "observed_expected": sum(1 for r in rows if r["expected"] == "observed"),
        "observed_undated_expected": sum(
            1 for r in rows if r["expected"] == "observed" and not r["rail_shadowed"]),
        "observed_undated_exact": sum(
            1 for r in rows if r["expected"] == "observed" and not r["rail_shadowed"]
            and r["assigned"] == "observed"),
        "observed_shadowed_expected": sum(
            1 for r in rows if r["expected"] == "observed" and r["rail_shadowed"]),
        "observed_shadowed_open_ok": sum(
            1 for r in rows if r["expected"] == "observed" and r["rail_shadowed"]
            and r["assigned"] in ("book", "review", "chat_capture")),
        "observed_shadowed_as_observed": sum(
            1 for r in rows if r["expected"] == "observed" and r["rail_shadowed"]
            and r["assigned"] == "observed"),
        "observed_exact": n("observed", {"observed"}),
        "observed_as_open": n("observed", {"book", "review"}),
        "observed_captured_any": n("observed", captured | {"observed"}),
        "reject_expected": sum(1 for r in rows if r["expected"] == "reject"),
        "reject_false_captures": n("reject", captured | {"observed"}),
    }
    pos_expected = counts["book_expected"] + counts["review_expected"]
    pos_captured = counts["book_captured"] + counts["review_captured"]
    counts["owner_lane_recall"] = round(pos_captured / pos_expected, 4) if pos_expected else None
    denom = pos_captured + counts["reject_false_captures"]
    counts["owner_lane_precision_vs_planted"] = (
        round(pos_captured / denom, 4) if denom else None)

    # Unplanted captures: capture rows matching no planted keyphrase.
    all_kps = [p.lower() for lab in labels for i in lab["planted"]
               for p in [i["keyphrase"]] + i.get("alts", [])]
    unplanted = []
    for ev in run["events"]:
        r = event_route(ev)
        if r and not any(kp in event_text(ev).lower() for kp in all_kps):
            unplanted.append({"channel": "events", "route": r, "text": event_text(ev)[:160]})
    counts["unplanted_captures"] = len(unplanted)
    return {"rows": rows, "counts": counts, "unplanted": unplanted}


def score_entities(run: dict, labels: list[dict], roster_names: set[str],
                   strict_unknown: bool = True) -> dict:
    full = run["chat"] + "\n" + run["artifact_text"]
    full_l = full.lower()
    events_text = " ".join(json.dumps(ev, ensure_ascii=False) for ev in run["events"]).lower()
    rows = []
    for lab in labels:
        for m in lab["entity_mentions"]:
            surface = m["surface"]
            if m.get("expected") == "UNKNOWN_PERSON":
                # strict_unknown applies only where the arm processed the
                # transcript that introduced the unknown (t1). Elsewhere,
                # answering from the roster (e.g. "Skyler Sample" to "do we
                # know a Skyler?") is correct, not a wrong bind.
                wrong_bind = None
                if strict_unknown:
                    first = surface.split()[0]
                    for name in roster_names:
                        if name.split()[0] == first and name != surface and name.lower() in full_l:
                            # e.g. output asserts "Skyler Sample" for Skyler Stone
                            if surface.lower() not in full_l:
                                wrong_bind = name
                if surface.lower() in full_l:
                    verdict = "right"
                elif wrong_bind:
                    verdict = "wrong"
                elif not strict_unknown and surface.split()[0].lower() in full_l:
                    verdict = "right"  # roster answer to a first-name question
                else:
                    verdict = "missed"
                rows.append({"label_id": m["label_id"], "surface": surface,
                             "expected": "UNKNOWN_PERSON", "verdict": verdict,
                             "wrong_bind": wrong_bind})
                continue
            expected = m.get("expected") or m.get("expected_org")
            hit = expected.lower() in full_l or expected.lower() in events_text
            surfaced = surface.lower() in full_l or surface.lower() in events_text
            verdict = "right" if hit else ("partial_surface_only" if surfaced else "missed")
            rows.append({"label_id": m["label_id"], "surface": surface,
                         "expected": expected, "verdict": verdict})
    counts = {}
    for r in rows:
        counts[r["verdict"]] = counts.get(r["verdict"], 0) + 1
    return {"rows": rows, "counts": counts}


def score_hallucination(run: dict, roster_names: set[str], roster_orgs: set[str]) -> dict:
    text = run["chat"] + "\n" + run["artifact_text"]
    legal = set(roster_names) | set(roster_orgs) | KNOWN_UNKNOWNS
    org_words = {w for o in roster_orgs for w in o.split()}
    hits = {}
    for mt in NAME_BIGRAM.finditer(text):
        name = mt.group(0)
        if name in legal:
            continue
        if mt.group(1) in NONNAME_WORDS or mt.group(2) in NONNAME_WORDS:
            continue
        if mt.group(1) in org_words or mt.group(2) in org_words:
            continue
        first_names = {n.split()[0] for n in roster_names}
        if mt.group(1) not in first_names:
            continue  # only count roster-first-name + invented-surname shapes as person hallucinations
        hits[name] = hits.get(name, 0) + 1
    return {"invented_person_names": hits, "count": sum(hits.values())}


def score_leaks(run: dict, patterns: dict[str, str]) -> dict:
    text = run["chat"] + "\n" + run["artifact_text"]
    hits = {}
    for name, pat in patterns.items():
        try:
            found = re.findall(pat, text)
        except re.error:
            continue
        if found:
            hits[name] = {"count": len(found), "samples": [str(x)[:60] for x in found[:3]]}
    return {"hits": hits, "count": sum(h["count"] for h in hits.values())}


_SCHEMA_CACHE: dict = {}


def score_event_validity(run: dict, cr1: Path | None) -> dict | None:
    """Arm-symmetric: every event a run appended is validated against cr1's
    canonical events.schema.json. Added at battery start after the confirm
    turn revealed the bare arm hand-writing rows into events.jsonl — whether
    appended rows are substrate-valid is the durable-capture claim, counted.
    Skip-not-fail: no cr1 or no jsonschema -> None (metric absent, never 0)."""
    if cr1 is None or not run["events"]:
        return {"events": len(run["events"]), "invalid": 0, "errors": []} \
            if cr1 is not None else None
    try:
        import jsonschema
    except ImportError:
        return None
    key = str(cr1)
    if key not in _SCHEMA_CACHE:
        p = cr1 / "command-room" / "shared" / "data-schemas" / "events.schema.json"
        try:
            _SCHEMA_CACHE[key] = json.loads(p.read_text(encoding="utf-8"))
        except OSError:
            _SCHEMA_CACHE[key] = None
    schema = _SCHEMA_CACHE[key]
    if schema is None:
        return None
    validator = jsonschema.Draft7Validator(schema)
    invalid = 0
    errors = []
    for ev in run["events"]:
        errs = list(validator.iter_errors(ev))
        if errs:
            invalid += 1
            if len(errors) < 5:
                errors.append({"seq": ev.get("seq"), "type": ev.get("type"),
                               "error": str(errs[0].message)[:120]})
    return {"events": len(run["events"]), "invalid": invalid, "errors": errors}


def cross_check_receipts(run: dict, counts: dict) -> dict | None:
    """Arm A only: compare scorer counts against CR's own capture receipts."""
    receipts = []
    for ev in run["events"]:
        if ev.get("type") == "meeting_processed":
            cc = (ev.get("data") or {}).get("capture_counts")
            if cc:
                receipts.append(cc)
    if not receipts:
        return None
    agg = {}
    for cc in receipts:
        for k, v in cc.items():
            if isinstance(v, int):
                agg[k] = agg.get(k, 0) + v
    scorer_book = counts.get("book_exact", 0) + counts.get("review_exact", 0)
    return {"receipts": agg, "n_receipts": len(receipts),
            "scorer_booked_plus_review": scorer_book,
            "receipt_booked_plus_review": agg.get("n_book", 0) + agg.get("n_review", 0),
            "agree": (agg.get("n_book", 0) + agg.get("n_review", 0)) == scorer_book}


# ---------------------------------------------------------------------- main

def score_run(run_dir: Path, labels: list[dict], patterns: dict[str, str],
              cr1: Path | None = None) -> dict:
    run = read_run(run_dir)
    meta = run["meta"]
    roster_names, roster_orgs = load_roster(meta["fixture"])
    card = {
        "run_id": meta["run_id"], "arm": meta["arm"], "fixture": meta["fixture"],
        "task": meta["task"], "model_id": meta.get("model_id"),
        "wall_ms": meta.get("wall_ms"), "tokens": meta.get("tokens"),
        "is_error": meta.get("is_error"), "timed_out": meta.get("timed_out"),
    }
    if meta["task"] == "t1_transcripts":
        ext = score_extraction(run, labels)
        card["extraction"] = ext
        cross = cross_check_receipts(run, ext["counts"])
        if cross is not None:
            card["receipt_cross_check"] = cross
    if meta["task"] in ("t1_transcripts", "t5_entities"):
        card["entities"] = score_entities(run, labels, roster_names,
                                          strict_unknown=(meta["task"] == "t1_transcripts"))
    card["hallucination"] = score_hallucination(run, roster_names, roster_orgs)
    card["leaks"] = score_leaks(run, patterns)
    validity = score_event_validity(run, cr1)
    if validity is not None:
        card["event_validity"] = validity
    if meta["fixture"] != "clean_workspace":
        # The transcript set (labels + attendee names) binds to the
        # clean_workspace roster; other fixtures use different name/surname
        # assignments (e.g. mature has Bo Stone, not Bo Sample), so
        # name-keyed metrics score against the wrong roster there.
        card["metric_validity_note"] = (
            "hallucination and entity metrics are clean-roster-bound and "
            "N/A on this fixture pending per-fixture transcript binding; "
            "extraction, routing, leaks, event validity, and cost are valid")
    (run_dir / "scorecard.json").write_text(
        json.dumps(card, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return card


def scoreboard_md(cards: list[dict]) -> str:
    lines = ["# BENCH1 scoreboard", ""]
    lines.append("| run | arm | task | wall s | out tok | leaks | halluc | notes |")
    lines.append("|---|---|---|---|---|---|---|---|")
    for c in sorted(cards, key=lambda x: x["run_id"]):
        notes = []
        if c.get("is_error"):
            notes.append("ERROR")
        if c.get("timed_out"):
            notes.append("TIMEOUT")
        ext = c.get("extraction", {}).get("counts")
        if ext:
            obs_note = (f"obs={ext['observed_undated_exact']}/{ext['observed_undated_expected']} "
                        f"rail={ext['observed_shadowed_open_ok']}/{ext['observed_shadowed_expected']}"
                        if "observed_undated_expected" in ext else
                        f"obs={ext['observed_exact']}/{ext['observed_expected']}")
            notes.append(f"recall={ext['owner_lane_recall']} prec={ext['owner_lane_precision_vs_planted']} "
                         f"falseCap={ext['reject_false_captures']} {obs_note} "
                         f"unplanted={ext['unplanted_captures']}")
        ent = c.get("entities", {}).get("counts")
        if ent:
            notes.append(f"ent={ent}")
        ev = c.get("event_validity")
        if ev and ev["events"]:
            notes.append(f"evValid={ev['events'] - ev['invalid']}/{ev['events']}")
        tok = (c.get("tokens") or {}).get("output")
        halluc = str(c["hallucination"]["count"])
        if c.get("metric_validity_note"):
            halluc += "*"
            notes.append("*name-keyed metrics N/A on this fixture (clean-roster-bound labels)")
        lines.append(f"| {c['run_id']} | {c['arm']} | {c['task']} | "
                     f"{(c.get('wall_ms') or 0) / 1000:.0f} | {tok} | "
                     f"{c['leaks']['count']} | {halluc} | "
                     f"{'; '.join(notes)} |")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs-dir", default=str(SKILL_ROOT / "runs"))
    ap.add_argument("--only", default=None, help="score a single run id")
    ap.add_argument("--cr1", default=None, help="cr1 clone for live leak patterns")
    args = ap.parse_args()

    runs_dir = Path(args.runs_dir).resolve()
    labels = load_labels()
    patterns = load_leak_patterns(Path(args.cr1).expanduser().resolve() if args.cr1 else None)

    cards = []
    for run_dir in sorted(runs_dir.iterdir()):
        if not run_dir.is_dir() or not (run_dir / "run_meta.json").exists():
            continue
        if args.only and run_dir.name != args.only:
            continue
        cards.append(score_run(run_dir, labels, patterns,
                               cr1=Path(args.cr1).expanduser().resolve() if args.cr1 else None))
        print(f"scored {run_dir.name}")

    if cards:
        (runs_dir / "scoreboard.json").write_text(
            json.dumps(cards, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        (runs_dir / "scoreboard.md").write_text(scoreboard_md(cards), encoding="utf-8")
        print(f"scoreboard: {runs_dir / 'scoreboard.md'}")
    else:
        print("no runs found to score")
    return 0


if __name__ == "__main__":
    sys.exit(main())
