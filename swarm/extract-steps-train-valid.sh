#!/usr/bin/env bash

TT_DIR=$HOME/work/TacTok/

set -ex

[[ "$#" -ne 1 ]] && echo "Wrong number of parameters! This script takes one argument, a project index" && exit 1

source ${TT_DIR}/prelude.sh

PROJ=$(cat <(jq -r ".projs_train[]" projs_split.json) <(jq -r ".projs_valid[]" projs_split.json) | awk "NR==$1")
cd TacTok
python extract_proof_steps.py --data_root "../data/$PROJ"
