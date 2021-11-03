#!/usr/bin/env bash

set -e

[[ "$#" -ne 1 ]] && echo "Wrong number of parameters! This script takes one argument, a directory to search" && exit 1

# determine physical directory of this script
src="${BASH_SOURCE[0]}"
while [ -L "$src" ]; do
  dir="$(cd -P "$(dirname "$src")" && pwd)"
  src="$(readlink "$src")"
  [[ $src != /* ]] && src="$dir/$src"
done
MYDIR="$(cd -P "$(dirname "$src")" && pwd)"
TT_DIR=$MYDIR/../

$TT_DIR/swarm/find-missing-outputs-csv.sh "$@" | awk -F, \
  '{if ($5=="") {print "In project "$1" ("$2"), output for file "$3" ("$4") could not be found"} \
    else        {print "In project "$1" ("$2"), in file "$3" ("$4"), proof "$5" ("$6") could not be found"}}'
