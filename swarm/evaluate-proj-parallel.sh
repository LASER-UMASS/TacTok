#!/usr/bin/env bash

TT_DIR=$HOME/work/TacTok
[[ "$#" -lt 2 ]] && echo "Wrong number of parameters! This script takes at least two arguments, a weights id and a project index" && exit 1
EVAL_ID=$1
PROJ_IDX=$2
shift 2
PROJ=$(jq -r ".projs_test[]" ${TT_DIR}/projs_split.json | awk "NR==($PROJ_IDX+1)")
NUM_FILES=$(find ${TT_DIR}/data/${PROJ} -name "*.json" | wc -l)

mkdir -p output/evaluate/${EVAL_ID}

for file_idx in $(eval echo "{0..$(($NUM_FILES - 1))}"); do
  sbatch -p longq -J ${EVAL_ID}-evaluate-file \
    --output=output/evaluate/${EVAL_ID}/evaluate_proj_${PROJ_IDX}_${file_idx}.out \
    $TT_DIR/swarm/evaluate-proj.sh ${EVAL_ID} --proj_idx $PROJ_IDX --file_idx ${file_idx} "$@"
done
