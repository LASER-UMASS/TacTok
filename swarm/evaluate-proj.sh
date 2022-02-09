#!/usr/bin/env bash

set -e

TT_DIR=$HOME/work/TacTok

[[ "$#" -lt 1 ]] && echo "Wrong number of parameters! This script takes at least one argument, a weights id" && exit 1

source $TT_DIR/swarm/prelude.sh

EVAL_ID=$1
PROJ_IDX=$2
shift 1

OUTDIR=$TT_DIR/TacTok/evaluation/${EVAL_ID}/

cd TacTok
if [ $PROJ_IDX -eq 0 ]; then
  python evaluate.py ours ${EVAL_ID} --path runs/${EVAL_ID}/checkpoints/model_002.pth --export_config=${OUTDIR}/flags.json "$@"
else
  python evaluate.py ours ${EVAL_ID} --path runs/${EVAL_ID}/checkpoints/model_002.pth "$@"
fi