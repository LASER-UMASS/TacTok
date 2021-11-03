#!/usr/bin/env bash

squeue -u $USER | grep -v JOBID | awk '{print $1}' | xargs -n 1 scancel
