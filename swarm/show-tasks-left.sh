#!/usr/bin/env bash
SFLAGS="-u $USER -h"
if [[ $# -gt 0 ]]; then
  SFLAGS+=" -n $1-evaluate-file,$1-evaluate-proof"
fi

NUM_LEFT=$(squeue $SFLAGS | wc -l)
echo -n $'\r'${NUM_LEFT}'  '
while [[ ${NUM_LEFT} -gt 0 ]]; do
    NUM_LEFT=$(squeue $SFLAGS | wc -l)
    echo -n $'\r'${NUM_LEFT}'  '
    sleep 0.1
done
