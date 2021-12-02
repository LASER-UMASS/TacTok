#!/usr/bin/env bash

TT_DIR=$HOME/TacTok
EVAL_ID=$1
shift 1

COMMIT=$(git log -1 | head -n 1 | awk -F' ' '{print $2}')
TAG=$COMMIT
NEXT_IDX=1
while [ -d $TT_DIR/TacTok/runs/${EVAL_ID}-${TAG} ]; do
    TAG=${COMMIT}-${NEXT_IDX}
    ((NEXT_IDX++))
done
OUTDIR=$TT_DIR/TacTok/runs/${EVAL_ID}-${TAG}
mkdir -p ${OUTDIR}
git log -20 > ${OUTDIR}/glog.txt
git status > ${OUTDIR}/gstatus.txt
git diff > ${OUTDIR}/gdiff.txt
echo "CACHED" >> ${OUTDIR}/gdiff.txt
git diff --cached >> ${OUTDIR}/gdiff.txt
echo "$@" > ${OUTDIR}/flags.txt

cd $TT_DIR/TacTok
python main.py --no_validation --exp_id=${EVAL_ID}-${TAG} $@
