#!/usr/bin/env python3
"""Nested-Demos guard — mechanism + instruction pin (demo1 train, rider).

The demo-prospect-workspace skill's Step 1 refuses to build when the `Demos/`
directory sits INSIDE a real Command Room workspace, because the real
workspace's cleanup and deliverable sweeps walk every subfolder beneath their
root — a nested Demos/ would surface generated demo session notes and
documents in the operator's real work as if they were real.

That guard shipped as ENGLISH ONLY. Eric flagged it in the PR ("no product
code enforces it") and a fresh read confirmed it: run_demo_prospect_fixture_test
exercises `find_workspace_root` on the HAPPY path (a child resolves to the
fixture root) and never on the nested one. Prose with no pin is the
instruction-layer gap class — the failure is invisible while the battery is
green.

There is no demo-generator MODULE to test (the skill is instruction-only), so
this pins the two things that actually carry the guard:

  [A] THE MECHANISM. The skill's Step 1 detects nesting by calling
      `workspace_root.find_workspace_root` on the Demos/ directory itself and
      treating "it resolves" as STOP. These checks build both layouts on disk
      and assert that call answers correctly:
        * Demos/ nested inside a workspace  -> resolves to the workspace root
          (the guard fires)
        * Demos/ beside a workspace          -> raises FileNotFoundError
          (the guard passes)
        * a prospect folder INSIDE a nested Demos/ -> still resolves UP to the
          real workspace, which is the leak this guard exists to stop. Note
          this one is the sharp edge: a demo workspace has its own
          _hq/data/entities.json anchor, so once built it shadows the real
          root — the guard has to run BEFORE the build, which is exactly why
          the skill puts it at Step 1 "before anything else".
      If find_workspace_root's walk-up ever changes, these go red and the
      skill's Step 1 stops meaning what it says.

  [B] THE INSTRUCTION. The SKILL.md still carries the guard, names the
      mechanism, and states the consequence — so the step cannot be quietly
      softened to a suggestion.

House convention: check(name, cond) prints OK/FAIL, exit 1 on any failure,
auto-discovered by run_all.py (filename starts `run_`), stdlib only.
"""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
PLUGIN = REPO / "chalette-dev"

# cr1 payload resolution — see test_demo_prospect_fixture.py for the full
# rationale. Same contract: operator profile, then defaults, then the env
# escape hatch, never a hardcoded machine path; SKIP (loud, never a silent
# pass) when cr1 is absent.
from test_demo_prospect_fixture import _resolve_cr1  # noqa: E402

CR1 = _resolve_cr1()
if CR1 is None:
    pytest.skip(
        "cr1 payload not found — set CR1_CLONE, or add cr1_clone to "
        "chalette-dev/config/operator.json. This guard pins Command Room's "
        "workspace_root.find_workspace_root, which is the mechanism Step 1 uses.",
        allow_module_level=True,
    )

sys.path.insert(0, str(CR1 / "shared" / "scripts"))

from workspace_root import find_workspace_root  # noqa: E402

SKILL = PLUGIN / "skills" / "demo-prospect-workspace" / "SKILL.md"

passed = 0
failed = 0


def check(name: str, cond: bool, detail: str = "") -> None:
    global passed, failed
    if cond:
        passed += 1
        print(f"  OK {name}")
    else:
        failed += 1
        print(f"  FAIL {name}")
        if detail:
            print(f"      {detail}")


def _anchor(d: Path) -> None:
    """Make `d` a workspace root by planting the substrate anchor."""
    data = d / "_hq" / "data"
    data.mkdir(parents=True, exist_ok=True)
    (data / "entities.json").write_text(
        json.dumps({"people": [], "orgs": [], "threads": []}), encoding="utf-8")


# ---------------------------------------------------------------------------
# [A] The mechanism — find_workspace_root answers the guard's question
# ---------------------------------------------------------------------------

def _run_mechanism_checks() -> None:
    print("\n[A] find_workspace_root distinguishes nested Demos/ from beside")
    tmp = Path(tempfile.mkdtemp(prefix="cr-demo-nested-"))
    try:
        # Layout 1 — the FORBIDDEN one: Demos/ inside a real workspace.
        bad_ws = tmp / "bad" / "Real Workspace"
        _anchor(bad_ws)
        bad_demos = bad_ws / "Demos"
        bad_demos.mkdir(parents=True)

        resolved = None
        try:
            resolved = find_workspace_root(bad_demos)
        except FileNotFoundError:
            pass
        check("nested Demos/ RESOLVES to the real workspace root (guard fires)",
              resolved == bad_ws.resolve(), f"resolved={resolved}")

        # Layout 2 — the CORRECT one: Demos/ beside the workspace.
        good_parent = tmp / "good"
        good_ws = good_parent / "Real Workspace"
        _anchor(good_ws)
        good_demos = good_parent / "Demos"
        good_demos.mkdir(parents=True)

        raised = False
        try:
            find_workspace_root(good_demos)
        except FileNotFoundError:
            raised = True
        check("Demos/ BESIDE the workspace raises (guard passes the build)",
              raised)

        # Layout 3 — the leak this guard exists to stop. A prospect folder
        # under a nested Demos/, BEFORE it gets its own anchor, still resolves
        # up to the real workspace: everything written there lands inside the
        # operator's real root, where cleanup and the deliverable sweep walk.
        prospect = bad_demos / "Acme Corp"
        prospect.mkdir(parents=True)
        leaked = None
        try:
            leaked = find_workspace_root(prospect)
        except FileNotFoundError:
            pass
        check("a prospect folder under a nested Demos/ resolves UP to the real "
              "root (this is the leak)",
              leaked == bad_ws.resolve(), f"resolved={leaked}")

        # And the sharp edge, stated as a pin so nobody 'fixes' the guard by
        # moving it after the build: once the prospect folder carries its own
        # anchor it shadows the real root, so a post-build check would pass on
        # a layout that is still wrong.
        _anchor(prospect)
        shadowed = find_workspace_root(prospect)
        check("once built, the demo folder SHADOWS the real root — so the "
              "guard must run before the build, not after",
              shadowed == prospect.resolve(), f"resolved={shadowed}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ---------------------------------------------------------------------------
# [B] The instruction — the guard is still in the skill, still mandatory
# ---------------------------------------------------------------------------

def _guard_paragraph(text: str) -> str:
    """The guard's OWN paragraph, not the whole file.

    Scoping matters: `STOP`, `cleanup` and `sweep` all appear elsewhere in this
    SKILL.md, so a whole-file substring test would stay green while the guard
    itself was softened to a suggestion. Mutation-checked — softening the
    paragraph must turn these red.
    """
    marker = "Nested-Demos guard"
    i = text.find(marker)
    if i < 0:
        return ""
    # The guard is one bullet; end it at the next bullet or blank-line break.
    rest = text[i:]
    end = rest.find("\n- ")
    return rest if end < 0 else rest[:end]


def _run_instruction_checks() -> None:
    print("\n[B] the SKILL.md still carries the guard and its reason")
    check("the demo-prospect-workspace SKILL.md exists", SKILL.is_file(),
          str(SKILL))
    if not SKILL.is_file():
        return
    text = SKILL.read_text(encoding="utf-8")
    para = _guard_paragraph(text)

    check("the guard is named", bool(para))
    check("it runs before anything else",
          "before anything else" in para)
    check("it names the mechanism it checks with",
          "find_workspace_root" in para)
    check("it states the refusal, not a preference",
          "STOP" in para)
    check("it states WHERE Demos/ must sit",
          "beside" in para.lower() and "never inside" in para.lower())
    check("it states the consequence (real sweeps would walk it)",
          "cleanup" in para and "sweep" in para)


def main() -> int:
    _run_mechanism_checks()
    _run_instruction_checks()
    print(f"\n=== {passed} passed, {failed} failed ===")
    return 1 if failed else 0


def test_nested_demos_guard() -> None:
    """Mechanism + instruction, one pytest entry point (checks unchanged)."""
    assert main() == 0, "nested-Demos guard checks failed — see output above"


if __name__ == "__main__":
    raise SystemExit(main())
