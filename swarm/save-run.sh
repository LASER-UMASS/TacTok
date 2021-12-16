#!/usr/bin/env bash

TT_DIR=$HOME/work/TacTok/
EVAL_ID=$1
shift 1

COMMIT=$(git rev-parse --short HEAD)

OUTDIR=$TT_DIR/TacTok/evaluation/${EVAL_ID}/
mkdir -p $OUTDIR
git log -20 > ${OUTDIR}/glog.txt
git status > ${OUTDIR}/gstatus.txt
git diff > ${OUTDIR}/gdiff.txt
echo "CACHED" >> ${OUTDIR}/gdiff.txt
git diff --cached >> ${OUTDIR}/gdiff.txt
echo "$@" > ${OUTDIR}/flags.txt
