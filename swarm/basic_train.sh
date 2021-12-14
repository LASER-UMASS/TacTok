#!/usr/bin/env bash

TT_DIR=$HOME/TacTok
EVAL_ID=$1
shift 1

NUM_PROC_STEPS=$(ls $TT_DIR/TacTok/processed/proof_steps/train | wc -l)
EXPECTED_STEPS=22460
if [[ ${NUM_PROC_STEPS} -ne ${EXPECTED_STEPS} ]] ; then
    echo "Wrong number of proof steps in $TT_DIR/TacTok/processed/proof_steps/train/; expected ${EXPECTED_STEPS}, got ${NUM_PROC_STEPS}"
    exit 1
fi

COMMIT=$(git rev-parse --short HEAD)
TAG=$COMMIT
NEXT_IDX=1
while [ -d $TT_DIR/TacTok/runs/${EVAL_ID}-${TAG} ]; do
    TAG=${COMMIT}-${NEXT_IDX}
    ((NEXT_IDX++))
done
OUTDIR=$TT_DIR/TacTok/runs/${EVAL_ID}-${TAG}
mkdir -p ${OUTDIR}/checkpoints
git log -20 > ${OUTDIR}/glog.txt
git status > ${OUTDIR}/gstatus.txt
git diff > ${OUTDIR}/gdiff.txt
echo "CACHED" >> ${OUTDIR}/gdiff.txt
git diff --cached >> ${OUTDIR}/gdiff.txt
echo "$@" > ${OUTDIR}/flags.txt

cd $TT_DIR/TacTok
python main.py --no_validation --exp_id=${EVAL_ID}-${TAG} $@
