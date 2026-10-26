#!/usr/bin/env python3
"""Guard 4 (REFGAP1) — every references/*.md a SKILL.md cites must be git-tracked.

The instruction-layer-gap class, inverted: cr1's G13 catches code referenced by zero
skill texts; this guard catches skill text referencing files that don't exist. A SKILL.md
telling the model to "load references/foo.md" when foo.md was never committed fails at
runtime with a missing file — silently at review time, loudly in front of the operator
(cross-skill-interaction-test did exactly this at the v5.5.1 attended gate, 2026-07-29:
Step 1 loads three reference docs, none of which had EVER been written; BUILD_VCRRETIRE
§7 had recorded the whole 13-citation dangling set and deferred the guard to its own
build — this is that build).

Mechanics:
  - Scan every tracked SKILL.md under chalette-dev/skills/ for references/*.md citations.
  - A bare `references/x.md` resolves against the citing skill's own folder. A prefixed
    `other-skill/references/x.md` resolves against that skill's folder IF the prefix
    names a skill in THIS repo; a prefix that doesn't (e.g. `command-room/…`, which
    lives in cr1) is out of this guard's jurisdiction and skipped — chalette-dev CI
    cannot see other repos.
  - Every resolved citation must be git-TRACKED (not merely on disk — an untracked file
    is absent at client install, which is where the gap detonates), present on disk, and
    non-empty (a zero-byte stub satisfies an existence check and nothing else).
  - GRANDFATHERED is the pre-existing dangling set (BUILD_VCRRETIRE §7 residue, minus
    the three cross-skill-interaction-test files this build fixed). It RATCHETS: a new
    dangling citation fails immediately, and fixing a grandfathered one without deleting
    its row here also fails — a stale baseline row would mask a re-regression.

Controls (a sweep that reports zero proves nothing until the matcher can fail):
  - positive — the extractor must find the three cross-skill-interaction-test citations
    and resolve them to tracked files;
  - negative — synthetic text citing a nonexistent file must be flagged;
  - misattribution pin — `bug-regression-suite/references/cleanup-helper.md` cited FROM
    cross-skill-interaction-test resolves to bug-regression-suite (tracked), not to the
    citing skill (the false-dangling the naive resolver produced during this build).

Run: pytest tests/  (from the repo root)
"""

import sys as _sys
import os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import os
import re
import subprocess

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SKILLS_REL = "chalette-dev/skills"

# Optional skill-path prefix, then references/<name>.md. Anchored so a longer path like
# `command-room/references/x.md` captures WITH its prefix, never as a bare citation.
CITATION_RE = re.compile(
    r"(?:^|[\s`(])((?:[A-Za-z0-9_\-]+/)*references/[A-Za-z0-9_\-.]+\.md)"
)

# Pre-existing dangling citations, grandfathered until their owning skill's own fix
# build. (skill, cited ref) pairs. Delete a row when you commit its file — the ratchet
# test below fails on a stale row by design.
GRANDFATHERED = {
    ("bug-regression-suite", "references/adversarial-prompts.md"),
    ("bug-regression-suite", "references/snapshot-format.md"),
    ("ship-readiness-gate", "references/verdict-logic.md"),
    ("ship-readiness-gate", "references/bug-catalog-parser.md"),
    ("ship-readiness-gate", "references/regression-matching.md"),
    # mis-citation: the checklist lives under cr-skill-builder/references/ — the fix is
    # re-pointing the citation, not duplicating the file
    ("skill-creator", "references/cr-contract-checklist.md"),
    ("skill-generator", "references/SKILL_SHAPE_V2.md"),
}


def _tracked_files():
    out = subprocess.run(
        ["git", "ls-files"], capture_output=True, text=True, check=True, cwd=REPO_ROOT
    ).stdout
    files = set(out.splitlines())
    assert files, "git ls-files returned nothing — guard cannot see the repo"
    return files


def _repo_skills(tracked):
    return {
        p.split("/")[2]
        for p in tracked
        if p.startswith(SKILLS_REL + "/") and p.count("/") >= 3
    }


def _extract_citations(text):
    """All references/*.md citations in a SKILL.md body, with any path prefix kept."""
    refs = []
    for line in text.splitlines():
        refs.extend(CITATION_RE.findall(line))
    return refs


def _resolve(citing_skill, ref, repo_skills):
    """Repo-relative target for a citation, or None if out of this repo's jurisdiction."""
    if ref.startswith("references/"):
        return f"{SKILLS_REL}/{citing_skill}/{ref}"
    prefix = ref[: ref.index("references/")].rstrip("/")
    owner = prefix.split("/")[-1]
    if owner in repo_skills:
        return f"{SKILLS_REL}/{owner}/" + ref[ref.index("references/"):]
    return None  # cross-repo (e.g. command-room/… in cr1) — not checkable here


def _scan():
    """-> (per-citation list of (citing_skill, ref, target), skill_md_count)"""
    tracked = _tracked_files()
    repo_skills = _repo_skills(tracked)
    rows = []
    skill_mds = sorted(
        p for p in tracked
        if p.startswith(SKILLS_REL + "/") and p.endswith("/SKILL.md")
    )
    for md in skill_mds:
        citing_skill = md.split("/")[2]
        with open(os.path.join(REPO_ROOT, md), encoding="utf-8") as f:
            text = f.read()
        for ref in _extract_citations(text):
            target = _resolve(citing_skill, ref, repo_skills)
            if target is not None:
                rows.append((citing_skill, ref, target))
    return rows, len(skill_mds), tracked


# ---- Fence: no dangling references outside the grandfathered baseline ----------------

def test_every_cited_reference_is_tracked_on_disk_and_nonempty():
    rows, _, tracked = _scan()
    problems = []
    for citing_skill, ref, target in rows:
        if (citing_skill, ref) in GRANDFATHERED:
            continue
        if target not in tracked:
            problems.append(f"{citing_skill}: {ref} -> {target} is NOT git-tracked")
            continue
        abs_target = os.path.join(REPO_ROOT, target)
        if not os.path.exists(abs_target):
            problems.append(f"{citing_skill}: {ref} -> {target} tracked but MISSING on disk")
        elif os.path.getsize(abs_target) == 0:
            problems.append(f"{citing_skill}: {ref} -> {target} tracked but EMPTY")
    assert not problems, (
        "Dangling SKILL.md reference citation(s) — the instruction-layer gap this guard "
        "exists for. Commit the file(s) with the SKILL.md that cites them:\n  "
        + "\n  ".join(problems)
    )


# ---- Fence: the baseline ratchets — a fixed entry must be deleted from it ------------

def test_grandfathered_entries_are_still_dangling():
    rows, _, tracked = _scan()
    cited = {(s, r): t for s, r, t in rows}
    stale = []
    for skill, ref in sorted(GRANDFATHERED):
        target = cited.get((skill, ref))
        if target is None:
            stale.append(f"({skill}, {ref}) — citation no longer present in its SKILL.md")
        elif target in tracked:
            stale.append(f"({skill}, {ref}) — now tracked")
    assert not stale, (
        "GRANDFATHERED row(s) no longer dangling — delete them from the baseline so a "
        "future re-regression cannot hide behind them:\n  " + "\n  ".join(stale)
    )


# ---- Fence: the scan actually covered the skills tree --------------------------------

def test_scan_visited_every_skill():
    rows, skill_md_count, tracked = _scan()
    skills = _repo_skills(tracked)
    assert skill_md_count == len(skills), (
        f"scanned {skill_md_count} SKILL.md files but the repo has {len(skills)} skills "
        "— a skill without SKILL.md (or a glob miss) makes this guard falsely green"
    )
    assert skill_md_count >= 15, f"only {skill_md_count} SKILL.md files scanned — glob broken?"
    assert rows, "zero citations extracted repo-wide — extractor broken (see controls)"


# ---- Controls: prove the matcher can both succeed and fail ---------------------------

def test_control_positive_the_repaired_citations_resolve_tracked():
    rows, _, tracked = _scan()
    mine = {r for s, r, _ in rows if s == "cross-skill-interaction-test"}
    for expected in (
        "references/sequence-catalog.md",
        "references/temporal-wait-strategy.md",
        "references/multi-phase-verdict-aggregation.md",
    ):
        assert expected in mine, f"extractor lost a known citation: {expected}"
        target = f"{SKILLS_REL}/cross-skill-interaction-test/{expected}"
        assert target in tracked, f"REFGAP1 regression: {target} not tracked"


def test_control_negative_a_fabricated_dangling_citation_is_flagged():
    tracked = _tracked_files()
    repo_skills = _repo_skills(tracked)
    refs = _extract_citations("Step 1 loads `references/does-not-exist-xyzzy.md` first.")
    assert refs == ["references/does-not-exist-xyzzy.md"], f"extractor missed it: {refs}"
    target = _resolve("cross-skill-interaction-test", refs[0], repo_skills)
    assert target is not None and target not in tracked, (
        "a citation of a nonexistent file failed to register as dangling — "
        "the guard cannot fail, so its green means nothing"
    )


def test_control_prefixed_citation_resolves_to_owner_not_citer():
    rows, _, tracked = _scan()
    hits = [
        (s, r, t) for s, r, t in rows
        if s == "cross-skill-interaction-test" and r.endswith("cleanup-helper.md")
    ]
    assert hits, "known cross-skill citation (bug-regression-suite cleanup-helper) not found"
    for _s, _r, target in hits:
        assert target == f"{SKILLS_REL}/bug-regression-suite/references/cleanup-helper.md", (
            f"prefixed citation misattributed to the citing skill: {target}"
        )
        assert target in tracked
