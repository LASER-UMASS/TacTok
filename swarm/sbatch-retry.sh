#!/usr/bin/env bash

TT_DIR=$HOME/work/TacTok/
BACKOFF_AMOUNT=0.001
SFLAGS="-u $USER -h"
while getopts ":J:" opt; do
    case "$opt" in
      J)
        SFLAGS+=" -n ${OPTARG}"
        ;;
      ?)
        continue
        ;;
    esac
done
while
    JOBS_BEFORE=$($TT_DIR/swarm/squeue-retry.sh $SFLAGS)
    sbatch $@
    JOBS_AFTER=$($TT_DIR/swarm/squeue-retry.sh $SFLAGS)
    diff <(echo "$JOBS_BEFORE" | awk '{print $1}' | sort) \
         <(echo "$JOBS_AFTER"  | awk '{print $1}' | sort) | grep -q "> "
    (( $? != 0 ))
do
    echo "Submission failed, retrying with delay ${BACKOFF_AMOUNT}s..." >&2
    /usr/bin/env sleep $BACKOFF_AMOUNT
    ((BACKOFF_AMOUNT*=2))
done
