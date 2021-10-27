#!/usr/bin/env bash

set -e

[[ "$#" -ne 1 ]] && echo "Wrong number of parameters! This script takes one argument, a project index" && exit 1

echo "Evaluating project $1 on ${HOST}"
read-opam.sh
opam switch "4.07.1+flambda"
eval $(opam env)

cd work/Diva
COQ_ROOT=$(pwd)/coq
COQBIN=$COQ_ROOT/bin/
export PATH=$COQBIN:$PATH

sertop --version

cd TacTok
python evaluate.py ours diva_results --path runs/tok/checkpoints/model_003.pth --proj_idx $1
