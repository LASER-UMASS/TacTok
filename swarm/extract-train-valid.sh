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
