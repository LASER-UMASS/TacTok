#!/usr/bin/env bash


set -e

# determine physical directory of this script
TT_DIR=$HOME/work/Tactok/

[[ "$#" -ne 0 ]] && echo "Wrong number of parameters! This script takes no parameters" && exit 1

read-opam.sh
opam switch "4.07.1+flambda"
eval $(opam env)

cd $TT_DIR
COQ_ROOT=$(pwd)/coq
COQBIN=$COQ_ROOT/bin/
export PATH=$COQBIN:$PATH

cd coq_projects
make -j16
