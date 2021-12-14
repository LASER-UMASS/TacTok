#!/usr/bin/env bash
SFLAGS="-u $USER -h"

set -e
function usage {
        echo "Usage: $(basename $0) [-b] eval_id .." 2>&1
        echo 'Show the number of swarm tasks left.'
        echo '   -b          Show a tqdm-based progress bar'
        echo ' eval_id ..    A list of evaluation ids to check for. If empty, will check for all tasks'
        exit 1
}
TQDM=false
while getopts ":b" opt; do
  case "$opt" in
    b)
      TQDM=true
      ;;
    ?)
      usage
      ;;
  esac
done
shift $((OPTIND-1))
if [ $TQDM = true ] ; then
    [[ $# -eq 0 ]] || (echo "-b is unsupported with eval ids" && exit 1)
    TOTAL=$(squeue $SFLAGS | wc -l)
    while
        OLD_JOBS=$JOBS
        JOBS=$(squeue $SFLAGS 2> /dev/null) 2> /dev/null
        EXIT=$?
        if [[ $EXIT -ne 0 ]]; then
           continue
        fi
        if [[ $OLD_JOBS ]]; then
            diff <(echo "$OLD_JOBS" | awk '{print $1}' | sort) <(echo "$JOBS" | awk '{print $1}' | sort) | grep "< "
        fi
        sleep 0.1
        [ "$JOBS" != "" ]
    do true; done | tqdm --total $TOTAL >> /dev/null
elif [[ $# -eq 0 ]] ; then
    while
        JOBS=$(squeue $SFLAGS 2> /dev/null) 2> /dev/null
        EXIT=$?
        if [[ $EXIT -ne 0 ]]; then
           continue
        fi
        NUM_LEFT=$(echo "$JOBS" | wc -l)
        echo -n $'\r'${NUM_LEFT}'  '
        sleep 0.1
        [ "$JOBS" != "" ]
    do true; done
    echo "\r0"
else
    while
        TOTAL=0
        for i in "$@"; do
            JOBS=$(squeue $SFLAGS -n $i-evaluate-file,$i-evaluate-proof 2> /dev/null) 2> /dev/null
            EXIT=$?
            if [[ $EXIT -ne 0 ]]; then
                continue
            fi
            NUM_LEFT=$(echo "$JOBS" | wc -l)
            if [ "$JOBS" = "" ] ; then
                NUM_LEFT=0
            fi
            ((TOTAL+=$NUM_LEFT))
            echo -n '  '$NUM_LEFT'  '
        done
        echo -n $'\r'
        sleep 0.1
        [[ ${TOTAL} -gt 0 ]]
    do true; done
    echo ""
fi
