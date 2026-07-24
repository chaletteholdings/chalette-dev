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

Run: pytest tests/  (from the repo root)
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
QUICK_VALIDATE = os.path.join(SKILLS_DIR, "skill-creator", "scripts", "quick_validate.py")


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


def test_committed_operator_workspace_root_null():
    op = _load_committed_operator()
    assert op.get("workspace_root") is None, (
        "committed operator.json must have workspace_root == null "
        f"(got {op.get('workspace_root')!r})"
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
