#!/usr/bin/env bash
set -e

function usage {
  echo "Usage: $(basename $0) [-N <max-proofs>] eval_id .." 2>&1
  echo "Rerun the missing proofs from a particular run." 2>&1
  echo "    -N <max-proofs> Fail if there are more than <max-proofs> proofs to run." 2>&1
  exit 1
}

while getopts ":N:" opt; do
  case "$opt" in
    N)
      MAX_PROOFS="${OPTARG}"
      ;;
    ?)
      usage
      ;;
  esac
done
shift $((OPTIND-1))

[[ "$#" -lt 1 ]] && usage

TT_DIR=$HOME/work/TacTok

EVAL_ID=$1
shift 1

mkdir -p output/evaluate/${EVAL_ID}

NUM_PROOFS_DISPATCHED=0

$TT_DIR/swarm/find-missing-outputs-csv.sh ${TT_DIR}/TacTok/evaluation/${EVAL_ID} |
while IFS=, read -r proj_idx proj_name file_idx file_name proof_idx proof_name; do
  if [[ $proof_idx == "" ]]; then 
      PROOFS=$(python $TT_DIR/print_proof_names.py --proj=${proj_name} --file_idx=${file_idx})
      NUM_PROOFS=$(echo "$PROOFS" | wc -l)
      for proof_idx in $(eval echo "{0..$(($NUM_PROOFS - 1))}"); do
          PROOF=$(echo "$PROOFS" | awk "NR==(${proof_idx}+1)")
          $TT_DIR/swarm/sbatch-retry.sh -J ${EVAL_ID}-evaluate-proof -p defq \
            --output=output/evaluate/${EVAL_ID}/evaluate_proj_${proj_idx}_${file_idx}_${proof_idx}.out \
            $TT_DIR/swarm/evaluate-proj.sh ${EVAL_ID} \
            --proj_idx ${proj_idx} --file_idx ${file_idx} --proof=${PROOF} "$@"
      done
      NUM_PROOFS_DISPATCHED=$(($NUM_PROOFS_DISPATCHED+$NUM_PROOFS))
  else
      $TT_DIR/swarm/sbatch-retry.sh -J ${EVAL_ID}-evaluate-proof -p defq \
        --output=output/evaluate/${EVAL_ID}/evaluate_proj_${proj_idx}_${file_idx}_${proof_idx}.out \
        $TT_DIR/swarm/evaluate-proj.sh ${EVAL_ID} \
          --proj_idx ${proj_idx} --file_idx ${file_idx} --proof=${proof_name} "$@"
      NUM_PROOFS_DISPATCHED=$(($NUM_PROOFS_DISPATCHED+1))
  fi
  if [[ -n "$MAX_PROOFS" ]] && [[ "$NUM_PROOFS_DISPATCHED" -gt "$MAX_PROOFS" ]]; then
      echo "Hit max number of rerun proofs! Aborting."
      scancel -u $USER -n ${EVAL_ID}-evaluate-proof
      exit 1
  fi
done
