#!/usr/bin/env bash

set -e

[[ "$#" -ne 1 ]] && echo "Wrong number of parameters! This script takes one argument, a directory to search" && exit 1

TT_DIR=$HOME/work/TacTok

$TT_DIR/jobs/find_missing_outputs_csv.sh $@ | awk -F, \
  '{if ($5=="") {print "In project "$1" ("$2"), output for file "$3" ("$4") could not be found"} \
    else        {print "In project "$1" ("$2"), in file "$3" ("$4"), proof "$5" ("$6") could not be found"}}'
