#!/usr/bin/env bash

TT_DIR=$HOME/work/TacTok

PS=$TT_DIR/projs_split.json
NUM_PROJS=$(( $(jq ".projs_train | length" $PS) + $(jq ".projs_valid | length" $PS) ))
mkdir -p output/extract/
for proj in $(eval echo "{1..$NUM_PROJS}"); do 
  sbatch --output output/extract/extract_steps_${proj}.out -p longq $TT_DIR/swarm/extract-steps.sh $proj
done

while :
do
    sleep 1
    if ! squeue | grep "extract" > /dev/null; then
        break
    fi
done
cd work/TacTok/TacTok
python process_proof_steps.py
