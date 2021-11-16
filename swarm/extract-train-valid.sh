#!/usr/bin/env bash

TT_DIR=$HOME/work/TacTok

PS=$TT_DIR/projs_split.json
NUM_PROJS=$(( $(jq ".projs_train | length" $PS) + $(jq ".projs_valid | length" $PS) ))
mkdir -p output/extract/
for proj in $(eval echo "{1..$NUM_PROJS}"); do 
  sbatch --output output/extract/extract_steps_${proj}.out -p longq $TT_DIR/swarm/extract-steps-train-valid.sh $proj
done

$TT_DIR/swarm/show-tasks-left.sh

cd $TT_DIR/TacTok
python process_proof_steps.py
