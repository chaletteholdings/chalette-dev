#!/usr/bin/env python3
"""
Guard 1 (CONSOL1) — the shared QA/dev toolkit lives in exactly ONE plugin.

chalette-dev is the single canonical home of the shared toolkit skills. Before CONSOL1
the same ~18 skills were duplicated into Matthew's private `chalette` plugin (chalette030),
and the two copies silently drifted. This guard fails the build if ANY skill directory
name appears in BOTH plugins' skills/ dirs — i.e. if the duplicate class ever re-forms.

Usage:
    python scripts/check_toolkit_overlap.py <chalette-dev-clone> <chalette030-clone>

Each argument is the path to a repo clone (or directly to a plugin dir). The script
locates each plugin's skills/ dir, compares directory names (excluding `_shared`), and
exits 1 listing any intersection. Exit 0 (with a one-line OK) when disjoint.

Runs in three places (SPEC_CONSOL1 §6): chalette-dev CI (token-gated), the chalette
release preflight, and the chalette-dev release preflight.
"""

import os
import sys

EXCLUDE = {"_shared"}


def find_skills_dir(root):
    """Return the skills/ dir for a plugin, given a repo clone or plugin dir path.

    Handles both `<clone>/skills` and the nested `<clone>/<plugin-name>/skills`
    layout used by these repos (e.g. chalette-dev/chalette-dev/skills,
    chalette030/chalette/skills).
    """
    root = os.path.abspath(os.path.expanduser(root))
    # direct: <root>/skills
    direct = os.path.join(root, "skills")
    if os.path.isdir(direct):
        return direct
    # nested one level: <root>/<child>/skills
    candidates = []
    if os.path.isdir(root):
        for child in sorted(os.listdir(root)):
            p = os.path.join(root, child, "skills")
            if os.path.isdir(p):
                candidates.append(p)
    if len(candidates) == 1:
        return candidates[0]
    if len(candidates) > 1:
        raise SystemExit(
            f"ambiguous: multiple skills/ dirs under {root}: {candidates}. "
            "Pass the plugin dir explicitly."
        )
    raise SystemExit(f"no skills/ dir found under {root}")


def skill_names(skills_dir):
    # A directory counts as a skill only if it contains a SKILL.md. This ignores empty
    # husk dirs left behind by `git rm` (git drops tracked files but can leave the now-empty
    # directory on disk) and dirs holding only untracked material — neither is a live skill.
    return {
        name
        for name in os.listdir(skills_dir)
        if name not in EXCLUDE
        and os.path.isfile(os.path.join(skills_dir, name, "SKILL.md"))
    }


def main(argv):
    if len(argv) != 3:
        print(__doc__)
        raise SystemExit(2)

    dev_dir = find_skills_dir(argv[1])
    chalette_dir = find_skills_dir(argv[2])

    dev = skill_names(dev_dir)
    chalette = skill_names(chalette_dir)
    overlap = sorted(dev & chalette)

    if overlap:
        print("TOOLKIT OVERLAP GUARD — FAIL")
        print(f"  chalette-dev skills: {dev_dir}")
        print(f"  chalette   skills:   {chalette_dir}")
        print(
            f"  {len(overlap)} skill name(s) exist in BOTH plugins "
            "(the shared toolkit must live in chalette-dev only):"
        )
        for name in overlap:
            print(f"    - {name}")
        raise SystemExit(1)

    print(
        f"TOOLKIT OVERLAP GUARD — OK ({len(dev)} chalette-dev skills, "
        f"{len(chalette)} chalette skills, 0 overlap)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
