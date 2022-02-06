#!/usr/bin/env bash

#SBATCH -p defq
TT_DIR=$HOME/work/TacTok
[[ "$#" -lt 2 ]] && echo "Wrong number of parameters! This script takes at least two arguments, a weights id and a project index" && exit 1
EVAL_ID=$1
PROJ_IDX=$2
shift 2
FILE_IDX=$SLURM_ARRAY_TASK_ID

$TT_DIR/swarm/evaluate-proj.sh ${EVAL_ID} --proj_idx ${PROJ_IDX} --file_idx ${FILE_IDX} "$@"
