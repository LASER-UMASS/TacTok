#!/usr/bin/env bash

TT_DIR=$HOME/work/TacTok

PS=$TT_DIR/projs_split.json
NUM_PROJS=$(jq ".projs_test | length" $PS)
mkdir -p output/builds/
for proj in $(eval echo "{1..$NUM_PROJS}"); do 
  sbatch --output output/builds/build_${proj}.out ${TT_DIR}/swarm/build-proj.sh $proj
done
