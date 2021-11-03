#!/usr/bin/env bash

set -e

TT_DIR=$HOME/work/TacTok

echo "Evaluating project $1 on ${HOST}"
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
