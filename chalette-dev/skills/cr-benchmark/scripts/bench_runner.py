#!/usr/bin/env python3
"""BENCH1 run harness: execute one benchmark run (or a batch) headlessly.

One run = (arm x fixture x task):
  Arm A -- Command Room: headless Claude Code with the CR plugin loaded via
           --plugin-dir, against a fresh copy of the fixture workspace
           (which carries the client-layer CLAUDE.md, fixture v1.1+).
  Arm B -- bare Claude: identical session, no plugin; CLAUDE.md replaced by a
           neutral stub carrying the same operator identity and file pointers
           but none of the Command Room routing rules.

Both arms attach the same mock connector MCP servers (--strict-mcp-config, so
nothing else leaks in), get the same injected bench transcript set, the same
prompt, and the same pinned model. Each run gets a fresh temp workspace;
nothing persists between runs.

Speaker variant (ATTRIB1 D10, 2026-09-03): --speakers picks WHICH rendering
of the same labeled transcript set is injected -- `named` (the base set,
`Sam Sample: ...`), `me_them` (the real Granola shape: the user is `Me:`,
every other voice is `Them:`, inline on one line) or `unlabelled` (no
markers). Same labels, same prompts, same arms; only the transcript's speaker
naming changes. The run id carries the variant when it is not `named`.

Usage:
    python bench_runner.py --arm A --fixture clean_workspace --task all
    python bench_runner.py --arm B --fixture clean_workspace --task t1_transcripts
    python bench_runner.py --arm A --task t1_transcripts --speakers me_them --follow-up

Artifacts per run land in <runs-dir>/<run_id>/ :
    output.json      raw headless-run JSON (usage, model id, cost, duration)
    chat.txt         the assistant's final text
    stderr.txt       stderr from the CLI
    events_diff.jsonl  events appended to _hq/data/events.jsonl during the run
    new_files.json   inventory of files the run created/modified
    artifacts/       copies of small created files
    run_meta.json    arm/fixture/task/speakers/model/commits/timing
One line per run is appended to <runs-dir>/RUNLOG.jsonl (append-only).
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL_ROOT = HERE.parent
FIXTURES_ROOT = SKILL_ROOT.parent / "synthetic-workspace-runtime-test" / "fixtures"
BENCH_TRANSCRIPTS = SKILL_ROOT / "fixtures" / "bench_transcripts"
DEFAULT_RUNS = SKILL_ROOT / "runs"
DEFAULT_CR1 = Path.home() / "repos" / "cr1-canonical"

MODEL_ALIASES = {}  # pass through; log the id the run reports
PINNED_MODEL = "claude-opus-5"  # M ruling 2026-08-27: official runs at Opus 5.0
# A CLI result that means "no model call happened and none will until a human
# acts". Spend discipline: the batch stops at the first one, never retries.
AUTH_BLOCK_MARKERS = ("Failed to authenticate", "OAuth session expired", "not logged in",
                      "Please run /login", "invalid api key", "credit balance")
RUN_TIMEOUT_SEC = 20 * 60
ARTIFACT_COPY_CAP = 200 * 1024  # bytes

NEUTRAL_CLAUDE_MD = """# {first}'s workspace

{full_name}, CEO at {org}. This folder holds my working files.

## Files

- `_hq/data/entities.json` -- people, orgs, projects I work with
- `_hq/data/events.jsonl` -- append-only log of past activity
- `_hq/data/aliases.json` -- name shorthand registry
"""


def now_utc() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def run_stamp() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def find_claude(explicit: str | None) -> str:
    if explicit:
        return explicit
    found = shutil.which("claude")
    if found:
        return found
    fallback = Path.home() / ".local" / "bin" / "claude.exe"
    if fallback.exists():
        return str(fallback)
    raise SystemExit("FATAL: claude CLI not found; pass --claude")


def git_head(repo: Path) -> str:
    try:
        return subprocess.run(["git", "-C", str(repo), "rev-parse", "--short", "HEAD"],
                              capture_output=True, text=True, timeout=30).stdout.strip()
    except Exception:
        return "unknown"


SPEAKER_VARIANTS = ("named", "me_them", "unlabelled")


def transcript_set_dir(speakers: str) -> Path:
    """Where a speaker variant's rendering lives. `named` IS the base set;
    the others sit beside it and share its labels/ (one frozen label set)."""
    return BENCH_TRANSCRIPTS if speakers == "named" else BENCH_TRANSCRIPTS / speakers


def inject_bench_transcripts(ws: Path, speakers: str = "named") -> dict:
    """Replace the placeholder granola docs with the labeled bench set, in
    the requested speaker rendering. The connector doc keeps the calendar's
    attendee names in every variant -- under me_them the transcript no longer
    names the parties, the calendar still does (the real shape)."""
    src = transcript_set_dir(speakers)
    manifest = json.loads((src / "manifest.json").read_text(encoding="utf-8"))
    docs = {}
    for row in manifest["transcripts"]:
        tid = row["id"]
        docs[tid] = {
            "title": row["title"],
            "date": manifest["meeting_date"],
            "attendees": row["attendees"],
            "duration": "30m",
            "transcript": (src / f"{tid}.txt").read_text(encoding="utf-8"),
        }
    gpath = ws / "_hq" / "connectors" / "granola_responses.json"
    gpath.write_text(json.dumps({"granola_get_transcript": {"doc_ids": docs}},
                                indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    return {"speakers": speakers, "set_version": manifest.get("set_version"),
            "variants_version": manifest.get("variants_version")}


def neutralize_claude_md(ws: Path) -> None:
    ents = json.loads((ws / "_hq" / "data" / "entities.json").read_text(encoding="utf-8"))
    people = ents["entities"]["people"]
    orgs = {o["id"]: o["canonical_name"] for o in ents["entities"]["orgs"]}
    primary = next((p for p in people if p.get("is_primary_user")), people[0] if people else None)
    if primary is None:
        (ws / "CLAUDE.md").write_text("# Workspace\n", encoding="utf-8", newline="\n")
        return
    first = primary["canonical_name"].split()[0]
    org = orgs.get(primary.get("org_id") or primary.get("primary_org_id") or "", "the company")
    (ws / "CLAUDE.md").write_text(
        NEUTRAL_CLAUDE_MD.format(first=first, full_name=primary["canonical_name"], org=org),
        encoding="utf-8", newline="\n")


def write_mcp_config(ws: Path, tmp: Path) -> Path:
    connectors = ws / "_hq" / "connectors"
    server = HERE / "bench_mcp_server.py"
    cfg = {"mcpServers": {
        name: {
            "command": sys.executable,
            "args": [str(server), "--server", name, "--connectors-dir", str(connectors)],
            "env": {"PYTHONUTF8": "1"},
        } for name in ("gmail", "calendar", "granola")
    }}
    p = tmp / "bench_mcp.json"
    p.write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8", newline="\n")
    return p


def _main_model(parsed: dict | None) -> str | None:
    """The pinned model = the one that did the work. modelUsage can carry
    trivial helper calls on other models (e.g. a 15-token haiku ping), so
    take the entry with the most output tokens, and record the rest."""
    mu = (parsed or {}).get("modelUsage") or {}
    if not mu:
        return (parsed or {}).get("model")
    return max(mu, key=lambda k: (mu[k] or {}).get("outputTokens", 0))


def inventory(ws: Path) -> dict[str, int]:
    inv = {}
    for f in ws.rglob("*"):
        if f.is_file():
            inv[str(f.relative_to(ws)).replace("\\", "/")] = f.stat().st_size
    return inv


def one_run(*, arm: str, fixture: str, task_key: str, prompt: str, model: str,
            claude: str, cr1: Path, runs_dir: Path, keep_workspace: bool,
            follow_up: str | None = None, speakers: str = "named") -> dict:
    run_id = f"{run_stamp()}_{arm}_{fixture}_{task_key}"
    if speakers != "named":
        run_id += f"_{speakers}"
    run_dir = runs_dir / run_id
    run_dir.mkdir(parents=True, exist_ok=False)

    tmp = Path(tempfile.mkdtemp(prefix=f"bench_{arm}_"))
    ws = tmp / "workspace"
    shutil.copytree(FIXTURES_ROOT / fixture, ws)
    # .metadata.json is harness bookkeeping, not workspace content.
    meta_file = ws / ".metadata.json"
    if meta_file.exists():
        meta_file.unlink()

    transcript_set = inject_bench_transcripts(ws, speakers)
    if arm == "B":
        neutralize_claude_md(ws)

    mcp_cfg = write_mcp_config(ws, tmp)

    events_path = ws / "_hq" / "data" / "events.jsonl"
    baseline_events = events_path.read_text(encoding="utf-8").splitlines() if events_path.exists() else []
    baseline_inv = inventory(ws)

    cmd = [claude, "-p", prompt,
           "--output-format", "json",
           "--model", MODEL_ALIASES.get(model, model),
           "--mcp-config", str(mcp_cfg),
           "--strict-mcp-config",
           "--permission-mode", "bypassPermissions"]
    if arm == "A":
        cmd += ["--plugin-dir", str(cr1 / "command-room")]

    env = dict(os.environ)
    env.update({"PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"})

    t0 = time.monotonic()
    started = now_utc()
    try:
        proc = subprocess.run(cmd, cwd=str(ws), env=env, capture_output=True,
                              text=True, encoding="utf-8", errors="replace",
                              timeout=RUN_TIMEOUT_SEC)
        timed_out = False
        rc, stdout, stderr = proc.returncode, proc.stdout, proc.stderr
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        rc = -1
        stdout = (exc.stdout or "") if isinstance(exc.stdout, str) else ""
        stderr = (exc.stderr or "") if isinstance(exc.stderr, str) else ""
    wall_ms = int((time.monotonic() - t0) * 1000)

    (run_dir / "stderr.txt").write_text(stderr or "", encoding="utf-8", newline="\n")
    parsed = None
    try:
        parsed = json.loads(stdout)
    except (json.JSONDecodeError, TypeError):
        (run_dir / "output_raw.txt").write_text(stdout or "", encoding="utf-8", newline="\n")
    if parsed is not None:
        (run_dir / "output.json").write_text(
            json.dumps(parsed, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
        (run_dir / "chat.txt").write_text(str(parsed.get("result", "")), encoding="utf-8", newline="\n")

    # Optional second confirm turn (protocol addition 2026-08-27): the
    # preview-first draft posture means a single shot can measure the preview
    # and never the capture. Resumed in the SAME session, both arms get the
    # identical confirmation. Usage/wall are summed; both raw outputs kept.
    parsed2 = None
    if follow_up and parsed is not None and not timed_out and not parsed.get("is_error"):
        sid = parsed.get("session_id")
        if sid:
            cmd2 = [claude, "-p", follow_up, "--resume", str(sid),
                    "--output-format", "json",
                    "--model", MODEL_ALIASES.get(model, model),
                    "--mcp-config", str(mcp_cfg),
                    "--strict-mcp-config",
                    "--permission-mode", "bypassPermissions"]
            if arm == "A":
                cmd2 += ["--plugin-dir", str(cr1 / "command-room")]
            t1 = time.monotonic()
            try:
                proc2 = subprocess.run(cmd2, cwd=str(ws), env=env, capture_output=True,
                                       text=True, encoding="utf-8", errors="replace",
                                       timeout=RUN_TIMEOUT_SEC)
                try:
                    parsed2 = json.loads(proc2.stdout)
                except (json.JSONDecodeError, TypeError):
                    (run_dir / "output2_raw.txt").write_text(proc2.stdout or "", encoding="utf-8", newline="\n")
                (run_dir / "stderr2.txt").write_text(proc2.stderr or "", encoding="utf-8", newline="\n")
            except subprocess.TimeoutExpired:
                timed_out = True
            wall_ms += int((time.monotonic() - t1) * 1000)
            if parsed2 is not None:
                (run_dir / "output2.json").write_text(
                    json.dumps(parsed2, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
                (run_dir / "chat2.txt").write_text(str(parsed2.get("result", "")), encoding="utf-8", newline="\n")

    # Substrate delta.
    post_events = events_path.read_text(encoding="utf-8").splitlines() if events_path.exists() else []
    new_events = post_events[len(baseline_events):]
    (run_dir / "events_diff.jsonl").write_text(
        "\n".join(new_events) + ("\n" if new_events else ""), encoding="utf-8", newline="\n")

    post_inv = inventory(ws)
    new_files = sorted(set(post_inv) - set(baseline_inv))
    changed = sorted(f for f in post_inv if f in baseline_inv and post_inv[f] != baseline_inv[f])
    (run_dir / "new_files.json").write_text(json.dumps(
        {"created": new_files, "modified": changed}, indent=2) + "\n", encoding="utf-8", newline="\n")
    art = run_dir / "artifacts"
    for rel in new_files:
        src = ws / rel
        if src.stat().st_size <= ARTIFACT_COPY_CAP:
            dst = art / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)

    usage = dict((parsed or {}).get("usage") or {})
    if parsed2 is not None:
        for k, v in ((parsed2.get("usage") or {}).items()):
            if isinstance(v, (int, float)) and isinstance(usage.get(k), (int, float)):
                usage[k] = usage[k] + v
            elif k not in usage:
                usage[k] = v
    meta = {
        "run_id": run_id, "ts": started, "arm": arm, "fixture": fixture,
        "task": task_key, "speakers": speakers, "transcript_set": transcript_set,
        "model_requested": model,
        "model_id": _main_model(parsed),
        "harness_commit": git_head(SKILL_ROOT.parent.parent.parent),
        "cr1_commit": git_head(cr1),
        "exit_code": rc, "timed_out": timed_out,
        "wall_ms": wall_ms,
        "duration_api_ms": (parsed or {}).get("duration_api_ms"),
        "num_turns": (parsed or {}).get("num_turns"),
        "total_cost_usd": (parsed or {}).get("total_cost_usd"),
        "tokens": {
            "input": usage.get("input_tokens"),
            "output": usage.get("output_tokens"),
            "cache_read": usage.get("cache_read_input_tokens"),
            "cache_creation": usage.get("cache_creation_input_tokens"),
        },
        "is_error": (parsed or {}).get("is_error", rc != 0),
        "follow_up_used": bool(follow_up and parsed2 is not None),
        "events_appended": len(new_events),
        "files_created": len(new_files),
    }
    if meta["is_error"]:
        # Why the row is an ERROR row, on the row itself (RUNLOG is the only
        # place a reader looks); the CLI puts auth failures in `result`.
        err = str((parsed or {}).get("result") or (stderr or "").strip()[-300:] or "")[:300]
        meta["error"] = err
        meta["auth_blocked"] = any(m.lower() in err.lower() for m in AUTH_BLOCK_MARKERS)
    if parsed2 is not None:
        meta["total_cost_usd"] = ((parsed or {}).get("total_cost_usd") or 0) + \
                                 (parsed2.get("total_cost_usd") or 0)
        meta["num_turns"] = ((parsed or {}).get("num_turns") or 0) + \
                            (parsed2.get("num_turns") or 0)
    (run_dir / "run_meta.json").write_text(
        json.dumps(meta, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    with open(runs_dir / "RUNLOG.jsonl", "a", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(meta, ensure_ascii=False) + "\n")

    if keep_workspace:
        meta["workspace_kept_at"] = str(ws)
        print(f"  workspace kept at {ws}")
    else:
        shutil.rmtree(tmp, ignore_errors=True)

    status = "TIMEOUT" if timed_out else ("ERROR" if meta["is_error"] else "ok")
    print(f"[{status}] {run_id}  wall={wall_ms / 1000:.0f}s  "
          f"tokens_out={usage.get('output_tokens')}  events+={len(new_events)}")
    return meta


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", required=True, choices=["A", "B"])
    ap.add_argument("--fixture", default="clean_workspace")
    ap.add_argument("--task", default="all",
                    help="'all' or comma-separated task keys from tasks.json")
    ap.add_argument("--model", default=PINNED_MODEL)
    ap.add_argument("--runs-dir", default=str(DEFAULT_RUNS))
    ap.add_argument("--cr1", default=str(DEFAULT_CR1))
    ap.add_argument("--claude", default=None)
    ap.add_argument("--keep-workspace", action="store_true")
    ap.add_argument("--follow-up", action="store_true",
                    help="run the task's confirm turn from tasks.json follow_ups "
                         "(protocol addition 2026-08-27; requires M's sign-off for official runs)")
    ap.add_argument("--speakers", default="named", choices=SPEAKER_VARIANTS,
                    help="transcript speaker rendering to inject (ATTRIB1 D10): named "
                         "(default, the base set), me_them (real Granola shape), unlabelled")
    args = ap.parse_args()

    tasks_doc = json.loads((HERE / "tasks.json").read_text(encoding="utf-8"))
    tasks = tasks_doc["tasks"]
    follow_ups = tasks_doc.get("follow_ups") or {}
    keys = list(tasks) if args.task == "all" else [k.strip() for k in args.task.split(",")]
    unknown = [k for k in keys if k not in tasks]
    if unknown:
        raise SystemExit(f"FATAL: unknown task keys {unknown}; known: {list(tasks)}")

    fixture_dir = FIXTURES_ROOT / args.fixture
    if not fixture_dir.exists():
        raise SystemExit(f"FATAL: fixture {fixture_dir} not found")
    if not (BENCH_TRANSCRIPTS / "manifest.json").exists():
        raise SystemExit("FATAL: bench transcripts missing; run _generate_bench_transcripts.py")
    if not (transcript_set_dir(args.speakers) / "manifest.json").exists():
        raise SystemExit(f"FATAL: {args.speakers} transcript variant missing; run "
                         f"_generate_bench_transcripts.py --speakers {args.speakers}")

    cr1 = Path(args.cr1).expanduser().resolve()
    if args.arm == "A" and not (cr1 / "command-room" / ".claude-plugin").exists():
        raise SystemExit(f"FATAL: {cr1}/command-room does not look like the CR plugin")

    claude = find_claude(args.claude)
    runs_dir = Path(args.runs_dir).resolve()
    runs_dir.mkdir(parents=True, exist_ok=True)

    print(f"arm={args.arm} fixture={args.fixture} tasks={keys} model={args.model} "
          f"speakers={args.speakers}")
    for k in keys:
        meta = one_run(arm=args.arm, fixture=args.fixture, task_key=k, prompt=tasks[k],
                       model=args.model, claude=claude, cr1=cr1, runs_dir=runs_dir,
                       keep_workspace=args.keep_workspace,
                       follow_up=follow_ups.get(k) if args.follow_up else None,
                       speakers=args.speakers)
        if meta.get("auth_blocked"):
            print(f"FATAL: the claude CLI cannot authenticate ({meta['error'][:120]}); "
                  f"stopping the batch -- log in (`claude /login`) and re-run. "
                  f"The ERROR row stays in RUNLOG.jsonl.", file=sys.stderr)
            return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
