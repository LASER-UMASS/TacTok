#!/usr/bin/env bash

TT_DIR=$HOME/work/TacTok

PS=$TT_DIR/projs_split.json
NUM_PROJS=$(( $(jq ".projs_train | length" $PS) + $(jq ".projs_valid | length" $PS) ))
DEST=./proof_steps/
REALDEST=TacTok/${DEST}
mkdir -p output/extract/

if [ -d "$REALDEST" ]; then
    read -r -p "Destination directory $REALDEST exists. Remove it? [y/N] " input
    case $input in
        [yY][eE][sS]|[yY])
        rm -r "$REALDEST" ;;
        *)
        echo "Aborting..." && exit 1 ;;
    esac
fi

for proj in $(eval echo "{1..$NUM_PROJS}"); do 
  sbatch --output output/extract/extract_steps_${proj}.out -p longq $TT_DIR/swarm/extract-steps-train-valid.sh $proj --output=${DEST}
done

$TT_DIR/swarm/show-tasks-left.sh -b
DEST='TacTok/processed/proof_steps'
if [ -d $DEST ]; then
    read -r -p "Processed destination directory $DEST exists. Remove it? [y/N] " input
    case $input in
        [yY][eE][sS]|[yY])
        rm -r "$DEST" ;;
        *)
        echo "Aborting..." && exit 1 ;;
    esac
fi

cd $TT_DIR/TacTok
python process_proof_steps.py
