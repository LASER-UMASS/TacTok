#!/usr/bin/env bash

# determine physical directory of this script
TT_DIR=$HOME/work/TacTok

[[ "$#" -lt 3 ]] && echo "Wrong number of parameters! This script takes at least three arguments, an evaluation id, a project id, and a file id" && exit 1
EVAL_ID=$1
PROJ_IDX=$2
FILE_IDX=$3
shift 3
PROJ=$(jq -r ".projs_test[]" ${TT_DIR}/projs_split.json | awk "NR==(${PROJ_IDX}+1)")

PROOFS=$(python $TT_DIR/print_proof_names.py --proj=${PROJ} --file_idx=${FILE_IDX})
NUM_PROOFS=$(echo "$PROOFS" | wc -l)

mkdir -p output/evaluate/${EVAL_ID}

for proof_idx in $(eval echo "{0..$(($NUM_PROOFS - 1))}"); do
  PROOF=$(echo "$PROOFS" | awk "NR==(${proof_idx}+1)")
  $TT_DIR/swarm/sbatch-retry.sh -J ${EVAL_ID}-evaluate-proof -p defq \
    --comment="${PROJ_IDX}_${FILE_IDX}_${proof_idx}" \
    --output=output/evaluate/${EVAL_ID}/evaluate_proj_${PROJ_IDX}_${FILE_IDX}_${proof_idx}.out \
    ${TT_DIR}/swarm/evaluate-proj.sh ${EVAL_ID} --proj_idx ${PROJ_IDX} --file_idx ${FILE_IDX} --proof ${PROOF} "$@"
done
