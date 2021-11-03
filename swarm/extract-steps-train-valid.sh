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

set -ex

[[ "$#" -ne 1 ]] && echo "Wrong number of parameters! This script takes one argument, a project index" && exit 1

read-opam.sh
opam switch "4.07.1+flambda"
eval $(opam env)

cd $TT_DIR
COQ_ROOT=$(pwd)/coq
COQBIN=$COQ_ROOT/bin/
export PATH=$COQBIN:$PATH

PROJ=$(cat <(jq -r ".projs_train[]" projs_split.json) <(jq -r ".projs_valid[]" projs_split.json) | awk "NR==$1")
cd TacTok
python extract_proof_steps.py --data_root "../data/$PROJ"
