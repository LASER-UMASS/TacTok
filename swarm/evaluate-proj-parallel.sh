#!/usr/bin/env bash

TT_DIR=$HOME/work/TacTok
[[ "$#" -lt 2 ]] && echo "Wrong number of parameters! This script takes at least two arguments, a weights id and a project index" && exit 1
EVAL_ID=$1
PROJ_IDX=$2
shift 2
PROJ=$(jq -r ".projs_test[]" ${TT_DIR}/projs_split.json | awk "NR==($PROJ_IDX+1)")
NUM_FILES=$(find ${TT_DIR}/data/${PROJ} -name "*.json" | wc -l)
if (( $NUM_FILES == 0 )); then exit 0 fi

mkdir -p output/evaluate/${EVAL_ID}
$TT_DIR/swarm/sbatch-retry.sh -J ${EVAL_ID}-evaluate-file -p longq \
  --output=output/evaluate/${EVAL_ID}/evaluate_proj_${PROJ_IDX}_%a.out \
  --array=0-$(($NUM_FILES - 1 )) \
  $TT_DIR/swarm/evaluate-proj-array-item.sbatch ${EVAL_ID} ${PROJ_IDX} "$@"

