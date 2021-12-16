#!/usr/bin/env bash

TT_DIR=$HOME/work/TacTok

[[ "$#" -lt 1 ]] && echo "Wrong number of parameters! This script takes at least one argument, a weights id" && exit 1

EVAL_ID=$1
shift 1
DEST="$TT_DIR/TacTok/evaluation/$EVAL_ID"

if [ -d $DEST ]; then
    read -r -p "Destination directory exists. Remove it? [y/N] " input
    case $input in 
        [yY][eE][sS]|[yY])
        rm -r "$DEST" ;;
        *)
        read -r -p "Continue from existing run? [y/N] " input
        case $input in 
            [yY][eE][sS]|[yY])
            $TT_DIR/swarm/rerun-missing-files.sh ${EVAL_ID} "$@" ;;
            *)
            echo "Aborting..." && exit 1 ;;
        esac ;;
    esac
fi

./swarm/save-run.sh ${EVAL_ID}

for proj_idx in {0..26}; do
    $TT_DIR/swarm/evaluate-proj-parallel.sh ${EVAL_ID} $proj_idx "$@"
done

