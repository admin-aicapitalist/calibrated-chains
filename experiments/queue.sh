#!/usr/bin/env bash
# Run variants sequentially on a sample; a lock keeps one model copy in RAM at a time.
# usage: experiments/queue.sh dev10 v1_criteria v2_framing ...
set -u
cd "$(dirname "$0")/.."
sample=$1; shift
exec 9> experiments/runs/.model.lock
flock 9
for v in "$@"; do
  uv run python -m experiments.run "$v" "$sample" 2>&1 | grep -vE "Loading weights|falling back" > "experiments/runs/${v}__${sample}.log"
done
