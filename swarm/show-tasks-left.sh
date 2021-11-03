#!/usr/bin/env bash

NUM_LEFT=$(squeue -u $USER | grep -v "JOBID" | wc -l)
echo -n $'\r'${NUM_LEFT}'  '
while [[ ${NUM_LEFT} -gt 0 ]]; do
    NUM_LEFT=$(squeue -u $USER | grep -v "JOBID" | wc -l)
    echo -n $'\r'${NUM_LEFT}'  '
    sleep 0.1
done
