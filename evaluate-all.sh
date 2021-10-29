#!/usr/bin/env bash

mkdir -p output/evaluate/

for proj_idx in {0..26}; do
    ./evaluate-proj-parallel.sh $proj_idx "$@"
done

