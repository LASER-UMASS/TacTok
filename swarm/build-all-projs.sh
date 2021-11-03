#!/usr/bin/env bash


set -e

# determine physical directory of this script
TT_DIR=$HOME/work/Tactok/

[[ "$#" -ne 0 ]] && echo "Wrong number of parameters! This script takes no parameters" && exit 1

source ${TT_DIR}/prelude.sh

cd coq_projects
make -j16
