#!/usr/bin/env bash
set -e

[[ "$#" -lt 1 ]] && echo "Wrong number of parameters! This script takes at least one argument, an evaluation id" && exit 1

TT_DIR=$HOME/work/TacTok

EVAL_ID=$1
shift 1

$TT_DIR/swarm/find-missing-outputs-csv.sh ${TT_DIR}/TacTok/evaluation/${EVAL_ID} |
while IFS=, read -r proj_idx proj_name file_idx file_name proof_idx proof_name; do
  if [[ proof_idx != "" ]]; then
      sbatch -p longq -J ${EVAL_ID}-evaluate-file \
        --output=output/evaluate/evaluate_proj_${proj_idx}_${file_idx}.out \
        $TT_DIR/swarm/evaluate-proj.sh ${EVAL_ID} --proj_idx ${proj_idx} --file_idx ${file_idx} "$@"
  fi
done
