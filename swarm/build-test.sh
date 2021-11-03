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
NUM_PROJS=$(jq ".projs_test | length" $PS)
mkdir -p output/builds/
for proj in $(eval echo "{1..$NUM_PROJS}"); do 
  sbatch --output output/builds/build_${proj}.out ${TT_DIR}/swarm/build-proj.sh $proj
done
