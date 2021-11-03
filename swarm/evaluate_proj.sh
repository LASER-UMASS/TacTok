#!/usr/bin/env bash

set -e

TT_DIR=$HOME/work/TacTok

[[ "$#" -lt 1 ]] && echo "Wrong number of parameters! This script takes at least one argument, a weights id" && exit 1

$HOME/opam-scripts/read-opam.sh
opam switch "4.07.1+flambda"
eval $(opam env)

cd $TT_DIR
COQ_ROOT=$(pwd)/coq
COQBIN=$COQ_ROOT/bin/
export PATH=$COQBIN:$PATH

EVAL_ID=$1
shift 1

cd TacTok
python evaluate.py ours ${EVAL_ID} --path runs/${EVAL_ID}/checkpoints/model_003.pth "$@"
