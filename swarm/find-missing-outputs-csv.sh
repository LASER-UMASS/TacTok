#!/usr/bin/env bash

set -e
shopt -s nullglob

[[ "$#" -ne 1 ]] && echo "Wrong number of parameters! This script takes one argument, a directory to search" 1>&2 && exit 1

TT_DIR=$HOME/work/TacTok

OUTPUT_DIR=$1
if [[ ! -d ${OUTPUT_DIR} ]]; then
  >&2 echo "Output directory doesn't exist!"
  exit 1
fi
NUM_PROJS=$(jq ".projs_test[]" ${TT_DIR}/projs_split.json | wc -l)
for proj_idx in $(eval echo "{0..$(($NUM_PROJS - 1))}"); do
  if [[ -f ${OUTPUT_DIR}/results_${proj_idx}.json ]] ; then
    continue
  fi
  PROJ=$(jq -r ".projs_test[]" ${TT_DIR}/projs_split.json | awk "NR==($proj_idx+1)")
  NUM_FILES=$(find ${TT_DIR}/data/${PROJ} -name "*.json" | wc -l)
  for file_idx in $(eval echo "{0..$((NUM_FILES - 1))}"); do
    if [[ ! -f ${OUTPUT_DIR}/results_${proj_idx}_${file_idx}.json ]] ; then
      SOME_PROOF_OUTPUT=false
      potential_matches=(${OUTPUT_DIR}/results_${proj_idx}_${file_idx}_*.json)
      if (( ${#potential_matches[@]} )); then
        PROOFS=$(python ${TT_DIR}/print_proof_names.py --proj=${PROJ} --file_idx=${file_idx})
        NUM_PROOFS=$(echo "$PROOFS" | wc -l)
        for proof_idx in $(eval echo "{0..$(($NUM_PROOFS - 1))}"); do
          PROOF=$(echo "$PROOFS" | awk "NR==($proof_idx+1)")
          if [[ -f ${OUTPUT_DIR}/results_${proj_idx}_${file_idx}_${PROOF}.json ]] ; then
            SOME_PROOF_OUTPUT=true
            break
          fi
        done
      fi
      FILE=$(cd data/${PROJ} && find . -name "*.json" | awk "NR==($file_idx+1)")
      if [ "$SOME_PROOF_OUTPUT" = true ] ; then
        for proof_idx in $(eval echo "{0..$(($NUM_PROOFS - 1))}"); do
          PROOF=$(echo "$PROOFS" | awk "NR==($proof_idx+1)")
          if [[ ! -f ${OUTPUT_DIR}/results_${proj_idx}_${file_idx}_${PROOF}.json ]] ; then
            echo "${proj_idx},${PROJ},${file_idx},${FILE},${proof_idx},${PROOF}"
          fi
        done
      else
        echo "${proj_idx},${PROJ},${file_idx},${FILE},,"
      fi
    fi
  done
done
