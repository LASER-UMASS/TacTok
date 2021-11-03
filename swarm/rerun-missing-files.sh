#!/usr/bin/env bash
set -e

[[ "$#" -lt 1 ]] && echo "Wrong number of parameters! This script takes at least one argument, an evaluation id" && exit 1

# determine physical directory of this script
src="${BASH_SOURCE[0]}"
while [ -L "$src" ]; do
  dir="$(cd -P "$(dirname "$src")" && pwd)"
  src="$(readlink "$src")"
  [[ $src != /* ]] && src="$dir/$src"
done
MYDIR="$(cd -P "$(dirname "$src")" && pwd)"
TT_DIR=$MYDIR/../

EVAL_ID=$1
shift 1

$TT_DIR/swarm/find-missing-outputs-csv.sh ${TT_DIR}/TacTok/evaluation/${EVAL_ID} |
while IFS=, read -r proj_idx proj_name file_idx file_name proof_idx proof_name; do
  if [[ proof_idx != "" ]]; then
      sbatch -p longq --output=output/evaluate/evaluate_proj_${proj_idx}_${file_idx}.out \
        $TT_DIR/swarm/evaluate-proj.sh ${EVAL_ID} --proj_idx ${proj_idx} --file_idx ${file_idx} "$@"
  fi
done
