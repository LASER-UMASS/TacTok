#!/usr/bin/env bash

# determine physical directory of this script
src="${BASH_SOURCE[0]}"
while [ -L "$src" ]; do
  dir="$(cd -P "$(dirname "$src")" && pwd)"
  src="$(readlink "$src")"
  [[ $src != /* ]] && src="$dir/$src"
done
MYDIR="$(cd -P "$(dirname "$src")" && pwd)"
TT_DIR=$MYDIR/../

[[ "$#" -lt 3 ]] && echo "Wrong number of parameters! This script takes at least three arguments, an evaluation id, a project id, and a file id" && exit 1
EVAL_ID=$1
PROJ_IDX=$2
FILE_IDX=$3
shift 3
PROJ=$(jq -r ".projs_test[]" ${TT_DIR}/projs_split.json | awk "NR==(${PROJ_IDX}+1)")

PROOFS=$(python print_proof_names.py --proj=${PROJ} --file_idx=${FILE_IDX})
NUM_PROOFS=$(echo "$PROOFS" | wc -l)

mkdir -p output/evaluate/${EVAL_ID}

for proof_idx in $(eval echo "{0..$(($NUM_PROOFS - 1))}"); do
  PROOF=$(echo "$PROOFS" | awk "NR==(${proof_idx}+1)")
  sbatch -p longq \
    --output=output/evaluate/${EVAL_ID}/evaluate_proj_${PROJ_IDX}_${FILE_IDX}_${proof_idx}.out \
    ${TT_DIR}/swarm/evaluate-proj.sh ${EVAL_ID} --proj_idx ${PROJ_IDX} --file_idx ${FILE_IDX} --proof ${PROOF} "$@"
done
