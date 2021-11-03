#!/usr/bin/env bash

set -e

[[ "$#" -ne 1 ]] && echo "Wrong number of parameters! This script takes one argument, a project index" && exit 1

TT_DIR=$HOME/work/TacTok

source ${TT_DIR}/prelude.sh

PROJ=$(jq -r ".projs_test[]" projs_split.json | awk "NR==$1")
cd coq_projects
make $PROJ

