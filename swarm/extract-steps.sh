#!/usr/bin/env bash

TT_DIR=$HOME/work/TacTok/

set -ex

[[ "$#" -lt 1 ]] && echo "Wrong number of parameters! This script takes one argument, a project index" && exit 1

source ${TT_DIR}/swarm/prelude.sh

PROJ=$1
shift 1
FILE_IDX=$SLURM_ARRAY_TASK_ID
FILE=$(find ${TT_DIR}/data/${PROJ} -name "*.json" | awk "NR==($FILE_IDX+1)")
cd TacTok
python extract_proof_steps.py --file "$FILE" $@
