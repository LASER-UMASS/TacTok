#!/usr/bin/env bash

set -e

TT_DIR=$HOME/work/TacTok

[[ "$#" -lt 1 ]] && echo "Wrong number of parameters! This script takes at least one argument, a weights id" && exit 1

source $TT_DIR/swarm/prelude.sh

EVAL_ID=$1
shift 1

cd TacTok
python evaluate.py ours ${EVAL_ID} --path runs/${EVAL_ID}/checkpoints/model_002.pth "$@"
