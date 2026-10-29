#!/bin/bash
# usage: wait_merge.sh <PR> <issue>; waits for the 3 quick shards on the PR head to complete, then merges or reports
S="${TRAIN_DIR:?set TRAIN_DIR to the train scratch folder (holds terms.txt, v/, ledger.txt)}"
P=$1; I=$2; H=$(gh api repos/chaletteholdings/cr1/pulls/$P -q .head.sha)
for i in $(seq 1 80); do
  st=$(gh api repos/chaletteholdings/cr1/commits/$H/check-runs -q '[.check_runs[]|select(.name|startswith("quick check"))]|group_by(.name)|map(sort_by(.started_at)|last)|map("\(.status):\(.conclusion)")|join(" ")')
  [ $(echo "$st" | grep -o 'completed:' | wc -l) -ge 3 ] && break; sleep 30
done
echo "#$P shards: $st"
case "$st" in *failure*|*cancelled*|*timed_out*) echo "#$P NOT MERGED: shard failure"; exit 1;; esac
for i in $(seq 1 20); do r=$(bash "$(dirname "$0")/merge_pr.sh" $P $I squash 2>&1); case "$r" in *"not green"*) sleep 30;; *) echo "$r"; break;; esac; done
