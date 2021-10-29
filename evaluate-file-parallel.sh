#!/usr/bin/env bash

TT_DIR=$HOME/work/TacTok
PROJ_IDX=$1
FILE_IDX=$2
shift 2
PROJ=$(jq -r ".projs_test[]" ${TT_DIR}/projs_split.json | awk "NR==(${PROJ_IDX}+1)")

PROOFS=$(python print_proof_names.py --proj=${PROJ} --file_idx=${FILE_IDX})
NUM_PROOFS=$(echo "$PROOFS" | wc -l)

mkdir -p output/evaluate

for proof_idx in $(eval echo "{0..$(($NUM_PROOFS - 1))}"); do
  PROOF=$(echo "$PROOFS" | awk "NR==(${proof_idx}+1)")
  sbatch -p longq --output=output/evaluate/evaluate_proj_${PROJ_IDX}_${FILE_IDX}_${proof_idx}.out \
    jobs/evaluate_proj.sh --proj_idx ${PROJ_IDX} --file_idx ${FILE_IDX} --proof=$PROOF "$@"
done
