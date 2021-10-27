#!/usr/bin/env bash

set -e

[[ "$#" -ne 1 ]] && echo "Wrong number of parameters! This script takes one argument, a directory to search" && exit 1

TT_DIR=$HOME/work/TacTok

OUTPUT_DIR=$1
NUM_PROJS=$(jq ".projs_test[]" ${TT_DIR}/projs_split.json | wc -l)
for proj_idx in $(eval echo "{0..$(($NUM_PROJS - 1))}"); do
  if [[ -f ${OUTPUT_DIR}/results_${proj_idx}.json ]] ; then
    continue
  fi
  PROJ=$(jq -r ".projs_test[]" ${TT_DIR}/projs_split.json | awk "NR==($proj_idx+1)")
  NUM_FILES=$(find ${TT_DIR}/data/${PROJ} -name "*.json" | wc -l)
  for file_idx in $(eval echo "{0..$((NUM_FILES - 1))}"); do
    if [[ ! -f ${OUTPUT_DIR}/results_${proj_idx}_${file_idx}.json ]] ; then
      echo "In project ${proj_idx} (${PROJ}), output for file ${file_idx} could not be found"
    fi
  done
done
