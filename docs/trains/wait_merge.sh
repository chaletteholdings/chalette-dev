#!/bin/bash
# usage: wait_merge.sh <PR> <issue>; waits for the quick check on the PR head to finish (one Mac job since cr1#1238), then merges or reports.
# Exits non-zero with a message on every path that does not merge.
S="${TRAIN_DIR:?set TRAIN_DIR to the train scratch folder (holds terms.txt, v/, ledger.txt)}"
P=$1; I=$2; R=chaletteholdings/cr1; H=$(gh api repos/$R/pulls/$P -q .head.sha)
# finished only when there is at least one run and every newest run is completed (covers queued, in_progress, waiting, requested, pending)
done_all() { [ -n "$1" ] && ! echo "$1" | tr ' ' '\n' | grep -qv '^completed:'; }
st=""
for i in $(seq 1 80); do
  # newest run of each quick-check name (sorted by id, which always increases), as status:conclusion
  st=$(gh api "repos/$R/commits/$H/check-runs?per_page=100" -q '[.check_runs[]|select(.name|startswith("quick check"))]|group_by(.name)|map(sort_by(.id)|last)|map("\(.status):\(.conclusion)")|join(" ")')
  done_all "$st" && break
  sleep 30
done
echo "#$P quick check: ${st:-none}"
done_all "$st" || { echo "#$P NOT MERGED: quick check still not finished after 40 min"; exit 1; }
echo "$st" | tr ' ' '\n' | grep -qv '^completed:success$' && { echo "#$P NOT MERGED: quick check not green ($st); re-run a timeout once"; exit 1; }
for i in $(seq 1 20); do
  r=$(bash "$(dirname "$0")/merge_pr.sh" $P $I squash 2>&1); rc=$?
  case "$r" in *QUICK_NOT_GREEN*) sleep 30;; *) echo "$r"; exit $rc;; esac
done
echo "$r"; echo "#$P NOT MERGED: quick check still not green after 10 min of retries"; exit 1
