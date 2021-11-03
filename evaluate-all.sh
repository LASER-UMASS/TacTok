#!/usr/bin/env bash

mkdir -p output/evaluate/

[[ "$#" -lt 1 ]] && echo "Wrong number of parameters! This script takes at least one argument, a weights id" && exit 1
EVAL_ID=$1
shift 1

for proj_idx in {0..26}; do
    ./evaluate-proj-parallel.sh ${EVAL_ID} $proj_idx "$@"
done

