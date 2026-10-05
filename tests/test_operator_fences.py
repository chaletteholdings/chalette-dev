#!/usr/bin/env python3
"""
Guard 2 (CONSOL1) — permanent CI fences on the operator profile + skill validity.

These run against the REAL repo layout (not toy fixtures — real-data-fixture discipline):

1. The committed config/operator.json MUST stay the contractor-safe default. If it ever
   drifts into M's real-workspace profile (the exact contractor-safety inversion the
   CONSOL1 ruling forbids), CI fails here.
2. config/operator.local.json (the gitignored M-only overlay) MUST NOT be tracked.
3. Every shipped skill MUST pass skill-creator/scripts/quick_validate.py (no template_version
   keys, descriptions <= 1024 chars, kebab-case names, no angle brackets in descriptions).
4. (MAINT2) The operator-profile resolution pattern MUST actually resolve. The shipped bash
   preamble is EXECUTED out of each SKILL.md and asserted to read a non-empty merged profile.
   This is the fence for the silent no-op found in SHIP_RECORD_CONSOL2 finding 3: the blocks
   built the plugin root from `${BASH_SOURCE[0]}` (empty when an agent runs the block through
   a Bash tool) and `pwd` (an MSYS `/c/Users/…` path under Git Bash, which native python.exe
   resolves to `C:\\c\\…`), so BOTH config reads missed, the merged profile came back empty,
   and every skill silently fell through to its synthetic default — an operator granted
   `real` ran synthetic with no error. Static checks could not see it; only running it can.

Run: pytest tests/  (from the repo root)
"""

import json
import os
import re
import shutil
import subprocess
import sys

import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PLUGIN_ROOT = os.path.join(REPO_ROOT, "chalette-dev")
CONFIG_DIR = os.path.join(PLUGIN_ROOT, "config")
OPERATOR_JSON = os.path.join(CONFIG_DIR, "operator.json")
SKILLS_DIR = os.path.join(PLUGIN_ROOT, "skills")
QUICK_VALIDATE = os.path.join(REPO_ROOT, "scripts", "quick_validate.py")


def _load_committed_operator():
    with open(OPERATOR_JSON, encoding="utf-8") as f:
        return json.load(f)


# ---- Fence 1: committed operator.json is the contractor-safe default -----------------

def test_committed_operator_allowed_targets_synthetic_only():
    op = _load_committed_operator()
    assert op.get("allowed_targets") == ["synthetic"], (
        "committed operator.json must have allowed_targets == ['synthetic'] "
        f"(got {op.get('allowed_targets')!r}) — real-workspace access is M's overlay, "
        "never the committed default"
    )


def test_committed_operator_may_ship_false():
    op = _load_committed_operator()
    assert op.get("may_ship") is False, "committed operator.json must have may_ship == false"


def test_committed_operator_may_promote_false():
    op = _load_committed_operator()
    assert op.get("may_promote") is False, "committed operator.json must have may_promote == false"


def test_committed_operator_may_build_own_spec_true():
    """GATE1: the third authority key — the one that is pinned ON, on purpose.

    `may_build_own_spec` grants spec->build in one pass and is deliberately independent
    of `may_ship` (a contractor builds and still holds zero ship authority; the pull
    request is the review point). M ruled 2026-07-27 that it SHIPS on rather than being
    granted per-machine in the overlay: it grants nothing a PR review doesn't already
    catch, and an overlay is a hand-created file that a re-clone silently loses.

    So this fence runs the OPPOSITE direction from its two neighbours. It is not a
    safety fence, it is a don't-silently-take-it-away fence: a revert to `false` sends
    every contractor back to the pre-build handoff with no error and no clue why. The
    safety fences are `may_ship` / `may_promote` / `allowed_targets` above, and they are
    unaffected by this one — that separation IS the GATE1 change.
    """
    op = _load_committed_operator()
    assert op.get("may_build_own_spec") is True, (
        "committed operator.json must have may_build_own_spec == true "
        f"(got {op.get('may_build_own_spec')!r}) — build-from-own-spec ships ON (M's "
        "ruling 2026-07-27). Reverting it silently reimposes the pre-build handoff. If "
        "the ruling has genuinely changed, change this fence deliberately and say so in "
        "the CHANGELOG; do not let it drift."
    )


def test_committed_operator_workspace_root_null():
    op = _load_committed_operator()
    assert op.get("workspace_root") is None, (
        "committed operator.json must have workspace_root == null "
        f"(got {op.get('workspace_root')!r})"
    )


def test_committed_operator_scrub_roster_null():
    """TI2: null is the fail-closed default AND the leak fence.

    A non-null value here would be the operator's real roster path — an M-workspace path
    committed to a repo a contractor forks. Null also disables triage-intake's outbound
    packet/BACKLOG emission entirely, which is the correct contractor posture.
    """
    op = _load_committed_operator()
    assert op.get("scrub_roster") is None, (
        "committed operator.json must have scrub_roster == null "
        f"(got {op.get('scrub_roster')!r}) — the real roster path is overlay-only; null keeps "
        "the outbound scrub gate fail-closed for anyone without an overlay"
    )


def test_committed_operator_is_not_m():
    op = _load_committed_operator()
    assert op.get("operator") != "m", (
        "committed operator.json operator must NOT be 'm' — that is M's overlay-only profile"
    )


# ---- Fence 2: the local overlay must never be committed -------------------------------

def test_operator_local_json_not_tracked():
    out = subprocess.run(
        ["git", "ls-files"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.splitlines()
    tracked = [p for p in out if os.path.basename(p) == "operator.local.json"]
    assert not tracked, (
        f"config/operator.local.json must be gitignored, never tracked. Tracked: {tracked}"
    )


# ---- Fence 3: every shipped skill passes quick_validate ------------------------------

def _skill_dirs():
    return sorted(
        name
        for name in os.listdir(SKILLS_DIR)
        if os.path.isdir(os.path.join(SKILLS_DIR, name))
        and os.path.exists(os.path.join(SKILLS_DIR, name, "SKILL.md"))
    )


@pytest.mark.parametrize("skill", _skill_dirs())
def test_skill_passes_quick_validate(skill):
    skill_path = os.path.join(SKILLS_DIR, skill)
    result = subprocess.run(
        [sys.executable, QUICK_VALIDATE, skill_path],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"quick_validate failed for {skill}: {result.stdout.strip()}{result.stderr.strip()}"
    )


# ---- Fence 4 (MAINT2): the operator-profile pattern must actually RESOLVE ---------------
#
# The bug this fences: a silent no-op. Nothing raised, nothing logged — resolution just
# fell through to the synthetic default. So these tests EXECUTE the shipped preamble rather
# than pattern-matching it, and the interpolation-into-`python -c` is reproduced verbatim
# because that interpolation is where the MSYS path actually broke (MSYS rewrites path-like
# ARGV for a native .exe, but never text inside a `-c` script string).

PREAMBLE_START = "# --- operator-profile resolution"
PREAMBLE_END = "# --- end operator-profile resolution ---"

# The probe reproduces the real consumer: the same two paths, interpolated into the same
# `python -c` shape every reading skill uses.
PROFILE_PROBE = """
python -c "import json,os,sys
p={}; _n=0
for f in ('$OPERATOR_CFG','$OPERATOR_OVERLAY'):
    if os.path.exists(f): p.update(json.load(open(f))); _n+=1
print('FILES_READ=%d KEYS=%d' % (_n, len(p)))"
"""


def _read_skill(skill):
    with open(os.path.join(SKILLS_DIR, skill, "SKILL.md"), encoding="utf-8") as f:
        return f.read()


def _bash_preamble_skills():
    """Skills whose SKILL.md interpolates the operator paths into a bash `python -c` read.

    Selected by the CONSUMER (`'$OPERATOR_CFG'`), deliberately NOT by the preamble sentinel:
    if a skill drops or rewrites the canonical preamble it must FAIL these tests, not
    silently vanish from the parametrization.
    """
    return sorted(s for s in _skill_dirs() if "'$OPERATOR_CFG'" in _read_skill(s))


def _extract_preamble(skill):
    body = _read_skill(skill)
    assert PREAMBLE_START in body and PREAMBLE_END in body, (
        f"{skill}: interpolates $OPERATOR_CFG into a python read but carries no "
        f"'{PREAMBLE_START}' / '{PREAMBLE_END}' block. The resolution preamble is the "
        f"canonical pattern — do not hand-roll a variant."
    )
    i = body.index(PREAMBLE_START)
    j = body.index(PREAMBLE_END, i) + len(PREAMBLE_END)
    return body[i:j]


def _code_lines(preamble):
    """Preamble with comment + blank lines stripped — the part that must not drift."""
    return [
        ln.rstrip()
        for ln in preamble.splitlines()
        if ln.strip() and not ln.lstrip().startswith("#")
    ]


def _fwd(path):
    """C:\\x -> C:/x. MSYS bash and Windows python both read the forward-slash form."""
    return path.replace("\\", "/")


def _run_preamble(skill, cwd, env_extra=None):
    env = dict(os.environ)
    env.pop("CHALETTE_DEV_ROOT", None)
    env.update(env_extra or {})
    script = _extract_preamble(skill) + "\n" + PROFILE_PROBE
    return subprocess.run(
        ["bash", "-s"],
        input=script,
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
    )


requires_bash = pytest.mark.skipif(
    shutil.which("bash") is None, reason="no bash on PATH (pattern is a bash preamble)"
)


@requires_bash
@pytest.mark.parametrize("skill", _bash_preamble_skills())
def test_bash_preamble_resolves_profile_from_repo_root(skill):
    """cwd = repo root, no env hints: the search must find the plugin and READ the profile.

    This is the regression. On the pre-MAINT2 pattern the probe returned FILES_READ=0
    (silently) from every cwd, including this one.
    """
    r = _run_preamble(skill, cwd=REPO_ROOT)
    assert r.returncode == 0, f"{skill}: preamble exited {r.returncode}\n{r.stderr}"
    m = re.search(r"FILES_READ=(\d+) KEYS=(\d+)", r.stdout)
    assert m, f"{skill}: probe produced no verdict\nstdout:{r.stdout}\nstderr:{r.stderr}"
    files_read, keys = int(m.group(1)), int(m.group(2))
    assert files_read >= 1, (
        f"{skill}: the merged operator profile read ZERO files — this is the silent no-op "
        f"(SHIP_RECORD_CONSOL2 finding 3). Resolution would fall through to the synthetic "
        f"default with no error.\nstdout:{r.stdout}\nstderr:{r.stderr}"
    )
    assert keys >= 1, f"{skill}: profile read but merged to an empty dict\n{r.stdout}"


@requires_bash
@pytest.mark.parametrize("skill", _bash_preamble_skills())
def test_bash_preamble_resolves_profile_from_unrelated_cwd(skill, tmp_path):
    """cwd nowhere near the repo, located via the $CHALETTE_DEV_ROOT escape hatch.

    Also the native-path assertion: CHALETTE_DEV_ROOT goes in as a Windows path, and the
    profile must still be READ — i.e. it reached python in a form python can open.
    """
    r = _run_preamble(
        skill, cwd=str(tmp_path), env_extra={"CHALETTE_DEV_ROOT": _fwd(PLUGIN_ROOT)}
    )
    assert r.returncode == 0, f"{skill}: preamble exited {r.returncode}\n{r.stderr}"
    m = re.search(r"FILES_READ=(\d+) KEYS=(\d+)", r.stdout)
    assert m and int(m.group(1)) >= 1, (
        f"{skill}: profile unreadable from an unrelated cwd — the resolved path did not "
        f"survive into python (the MSYS `/c/…` failure mode).\n"
        f"stdout:{r.stdout}\nstderr:{r.stderr}"
    )


@requires_bash
@pytest.mark.parametrize("skill", _bash_preamble_skills())
def test_bash_preamble_fails_loud_when_root_is_unfindable(skill, tmp_path):
    """The other half of the fix: an unresolvable root must ABORT, never default silently."""
    home = tmp_path / "home"
    cwd = tmp_path / "cwd"
    home.mkdir()
    cwd.mkdir()
    r = _run_preamble(
        skill,
        cwd=str(cwd),
        env_extra={"HOME": _fwd(str(home)), "USERPROFILE": _fwd(str(home))},
    )
    assert r.returncode != 0, (
        f"{skill}: preamble exited 0 with no locatable plugin root — silent fallthrough is "
        f"exactly the bug.\nstdout:{r.stdout}"
    )
    assert "FATAL" in r.stderr, f"{skill}: aborted without a FATAL message\n{r.stderr}"


@pytest.mark.parametrize("skill", _bash_preamble_skills())
def test_bash_preamble_code_is_byte_synced_across_skills(skill):
    """The pattern is copied per-skill by design; the CODE must not drift between copies.

    Comments may differ (each skill states its own consequence); executable lines may not.
    """
    reference = _code_lines(_extract_preamble(_bash_preamble_skills()[0]))
    assert _code_lines(_extract_preamble(skill)) == reference, (
        f"{skill}: resolution code has drifted from the canonical preamble. Re-sync it — a "
        f"per-skill variant is how this pattern broke in the first place."
    )


def test_no_skill_resolves_a_path_from_bash_source():
    """`${BASH_SOURCE[0]}` is EMPTY when an agent runs a SKILL.md block through a Bash tool.

    `dirname ""` is `.`, so it silently resolved against whatever the cwd happened to be.
    Never reintroduce it: search for config/operator.json instead.
    """
    # Comment lines are allowed — that is where the trap is documented. Executable lines
    # are not.
    offenders = [
        f"{s}:{n}"
        for s in _skill_dirs()
        for n, ln in enumerate(_read_skill(s).splitlines(), 1)
        if "BASH_SOURCE" in ln and not ln.lstrip().startswith("#")
    ]
    assert not offenders, (
        f"BASH_SOURCE used to locate paths at: {offenders}. It is always empty in an "
        f"agent-run block — use the canonical search preamble."
    )


@pytest.mark.parametrize("skill", sorted(
    s for s in os.listdir(SKILLS_DIR)
    if os.path.exists(os.path.join(SKILLS_DIR, s, "SKILL.md"))
    and "operator.local.json" in open(
        os.path.join(SKILLS_DIR, s, "SKILL.md"), encoding="utf-8"
    ).read()
))
def test_every_operator_read_fails_loud_on_an_empty_profile(skill):
    """An empty merged profile is a resolution FAILURE, never a silent default."""
    body = _read_skill(skill)
    assert "FATAL: operator profile unreadable" in body, (
        f"{skill}: reads the operator profile but has no loud-failure line. An unreadable "
        f"profile must abort — silently defaulting is the CONSOL2 finding-3 bug class."
    )


@pytest.mark.skipif(sys.platform != "win32", reason="MSYS path mechanism is Windows-only")
def test_msys_path_form_is_unreadable_by_this_python():
    """Documents the mechanism, so the fix above never looks like superstition.

    Windows python resolves a leading `/c/…` against the CURRENT DRIVE — `/c/Users/x`
    becomes `C:\\c\\Users\\x` — so an MSYS-flavoured path is not merely wrong, it is
    silently wrong: os.path.exists() returns False rather than raising.
    """
    native = os.path.abspath(OPERATOR_JSON)
    assert os.path.exists(native)
    drive, rest = os.path.splitdrive(native)
    msys = "/" + drive.rstrip(":").lower() + rest.replace("\\", "/")
    assert not os.path.exists(msys), (
        f"expected the MSYS form {msys!r} to be unreadable by native python — if this ever "
        f"passes, the fence's premise changed and the pattern should be revisited"
    )
