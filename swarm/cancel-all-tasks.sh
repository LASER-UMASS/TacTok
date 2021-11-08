#!/usr/bin/env bash

SFLAGS="-u $USER -h"
if [[ $# -gt 0 ]]; then
  SFLAGS+=" -n $1-evaluate-file,$1-evaluate-proof"
fi

squeue $SFLAGS | awk '{print $1}' | xargs -n 1 scancel
