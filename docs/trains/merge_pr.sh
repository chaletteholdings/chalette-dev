#!/bin/bash
# usage: merge_pr.sh <PR> <issue> <method>   (verify text in $S/v/<issue>.md with @MERGE@ placeholders)
S="${TRAIN_DIR:?set TRAIN_DIR to the train scratch folder (holds terms.txt, v/, ledger.txt)}"
SCR=~/repos/chalette-dev/chalette-dev/skills/cr1-scrub/scripts/scrub_scan.py
P=$1; I=$2; M=${3:-squash}; R=chaletteholdings/cr1
cd ~/repos/cr1-canonical || exit 9
git fetch -q origin && git fetch -q origin pull/$P/head
H=$(gh api repos/$R/pulls/$P -q .head.sha); MAIN=$(git rev-parse origin/main)
C=$(gh api repos/$R/commits/$H/check-runs -q '[.check_runs[]|select(.name|startswith("quick check"))|select(.conclusion=="success")]|length')
[ "$C" = 3 ] || { echo "#$P shards not 3 green ($C)"; exit 1; }
MC=$(gh api "repos/$R/actions/runs?branch=main&status=completed&per_page=10" -q '[.workflow_runs[]|select(.conclusion!="cancelled")][0]|"\(.head_sha) \(.conclusion)"')
[ "${MC#* }" = success ] || { echo "newest finished main run not green: $MC"; exit 2; }
B=$(git merge-base $H origin/main)
if [ "$B" != "$MAIN" ]; then
  G='instruction_layer_names.py|ORCH_MIGRATION_CENSUS|MODULE_INDEX|SKILLS_INDEX|specs/INDEX|handoffs/INDEX|WORKSPACE_ACCESS.md|SCHEDULER_DISCOVERY.md|propagate_rule22'
  OV=$(comm -12 <(git diff --name-only --no-renames $B $H|sort) <(git diff --name-only --no-renames $B origin/main|sort))
  GEN=$(git diff --name-only --no-renames $B $H | grep -E "$G")
  if [ -n "$(git diff --name-only --no-renames $B origin/main | grep -E "$G")" ] && [ -n "$(git diff --name-only --diff-filter=A --no-renames $B $H)" ]; then GEN="$GEN main-regen+new-files"; fi
  NEWSK=$(git diff --name-only --diff-filter=A --no-renames $B $H | grep '^command-room/skills/')
  [ -z "$OV$GEN$NEWSK" ] || { echo "#$P needs update: overlap=[$OV] gen=[$GEN] newskill=[$NEWSK]"; exit 3; }
  echo "#$P not on tip but no overlap; ok"
fi
git diff $B..$H | grep -E '^\+' | grep -v '^+++' > "$S/a.txt"; git log --format=%B $B..$H >> "$S/a.txt"
PYTHONUTF8=1 python $SCR scan --terms "$S/terms.txt" "$S/a.txt" || { echo "#$P scrub hit"; exit 4; }
OUT=$(gh api -X PUT repos/$R/pulls/$P/merge -f merge_method=$M -f sha=$H -q .sha) || { echo "#$P merge refused"; exit 5; }
# A person's test is owed only on a critical fix (owner ruling 2026-11-06, ISSUES.md section 7).
# Read the label from the issue, never guess: critical gets the verify text and needs UAT; anything
# else closes on the builder's verification with a one-line comment.
if gh api repos/$R/issues/$I/labels -q '.[].name' | grep -qx critical; then
  sed "s/@MERGE@/${OUT:0:8}/g; s/@PR@/$P/g" "$S/v/$I.md" > "$S/vv.md"
  PYTHONUTF8=1 python $SCR scan --terms "$S/terms.txt" "$S/vv.md" >/dev/null || { echo "verify text scrub hit, not posted"; exit 6; }
  gh api repos/$R/issues/$I/comments -F body=@"$S/vv.md" -q .html_url
  gh api repos/$R/issues/$I/labels -f 'labels[]=needs UAT' -q '[.[].name]|join(",")'
else
  gh api repos/$R/issues/$I/comments -f body="Closed on merge: not critical (ISSUES.md section 7, owner ruling 2026-11-06). Merged in #$P as ${OUT:0:8} on the builder's verification. Refile from use with *report this* if it comes back." -q .html_url
  gh api -X PATCH repos/$R/issues/$I -f state=closed -f state_reason=completed -q .state
fi
echo "$(date +%H:%M) MERGED #$P (#$I) -> ${OUT:0:8} ($M)" >> "$S/ledger.txt"; echo "MERGED #$P -> $OUT"
