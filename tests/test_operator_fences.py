#!/usr/bin/env python3
"""
Fences on the operator profile and skill validity. Run: pytest tests/ (from the repo root).

1. The committed config/operator.json stays the contractor default: operator is not the
   owner, and the file carries exactly the keys the four skills read. Dead fields were
   removed on 2026-10-24 (v0.8.1); this fence keeps them from creeping back.
2. config/operator.local.json (the owner's gitignored overlay) is never tracked.
3. Every shipped skill passes scripts/quick_validate.py.
4. Every skill that reads the operator profile fails loud on an unreadable one, and no
   skill resolves a path from BASH_SOURCE (empty when an agent runs a block through a
   Bash tool, so it silently resolves against the cwd).

The bash-preamble execution tests that used to live here were removed in v0.8.1: no skill
on main carries the $OPERATOR_CFG preamble any more, so they had been skipped on every
run since v0.7.0.
"""

import json
import os
import subprocess
import sys

import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PLUGIN_ROOT = os.path.join(REPO_ROOT, "chalette-dev")
CONFIG_DIR = os.path.join(PLUGIN_ROOT, "config")
OPERATOR_JSON = os.path.join(CONFIG_DIR, "operator.json")
SKILLS_DIR = os.path.join(PLUGIN_ROOT, "skills")
QUICK_VALIDATE = os.path.join(REPO_ROOT, "scripts", "quick_validate.py")

# The keys the four skills read. A key is added here only when a skill starts reading it.
OPERATOR_KEYS = {"operator", "operator_name"}


def _load_committed_operator():
    with open(OPERATOR_JSON, encoding="utf-8") as f:
        return json.load(f)


# ---- Fence 1: committed operator.json is the contractor default -----------------------

def test_committed_operator_is_not_m():
    op = _load_committed_operator()
    assert op.get("operator") != "m", (
        "committed operator.json operator must NOT be 'm'; that is the owner's overlay-only profile"
    )


def test_committed_operator_has_exactly_the_keys_the_skills_read():
    op = _load_committed_operator()
    keys = {k for k in op if not k.startswith("_comment")}
    assert keys == OPERATOR_KEYS, (
        f"committed operator.json carries {sorted(keys)}; the skills read {sorted(OPERATOR_KEYS)}. "
        "A field no skill reads is a rule with nothing behind it. Add the key here when a skill "
        "starts reading it, not before."
    )


def test_operator_key_fence_can_fail():
    """Non-vacuity: a planted extra key must be judged wrong by the same comparison."""
    planted = {k for k in {**_load_committed_operator(), "may_ship": False} if not k.startswith("_comment")}
    assert planted != OPERATOR_KEYS


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


def test_skills_are_discoverable():
    assert len(_skill_dirs()) >= 4, f"expected the four cr1 skills, found {_skill_dirs()}"


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


# ---- Fence 4: operator reads fail loud; no BASH_SOURCE path resolution ------------------

def _read_skill(skill):
    with open(os.path.join(SKILLS_DIR, skill, "SKILL.md"), encoding="utf-8") as f:
        return f.read()


def test_no_skill_resolves_a_path_from_bash_source():
    """`${BASH_SOURCE[0]}` is EMPTY when an agent runs a SKILL.md block through a Bash tool.

    `dirname ""` is `.`, so it silently resolved against whatever the cwd happened to be.
    Comment lines may mention it (that is where the trap is documented); executable lines may not.
    """
    offenders = [
        f"{s}:{n}"
        for s in _skill_dirs()
        for n, ln in enumerate(_read_skill(s).splitlines(), 1)
        if "BASH_SOURCE" in ln and not ln.lstrip().startswith("#")
    ]
    assert not offenders, (
        f"BASH_SOURCE used to locate paths at: {offenders}. It is always empty in an "
        f"agent-run block."
    )


def _operator_reading_skills():
    return sorted(s for s in _skill_dirs() if "operator.local.json" in _read_skill(s))


def test_operator_reading_skills_are_discoverable():
    """A fence over an empty set passes vacuously; pin that the four skills still read the profile."""
    assert len(_operator_reading_skills()) >= 4, _operator_reading_skills()


@pytest.mark.parametrize("skill", _operator_reading_skills())
def test_every_operator_read_fails_loud_on_an_empty_profile(skill):
    """An empty merged profile is a resolution FAILURE, never a silent default."""
    body = _read_skill(skill)
    assert "FATAL: operator profile unreadable" in body, (
        f"{skill}: reads the operator profile but has no loud-failure line. An unreadable "
        f"profile must abort; silently defaulting is how an operator once ran the wrong target."
    )
