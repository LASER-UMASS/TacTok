#!/usr/bin/env bash

SFLAGS="-u $USER -h"
if [[ $# -gt 0 ]]; then
  SFLAGS+=" -n "
  for i in "$@"; do
    SFLAGS+="$i-evaluate-file,$i-evaluate-proof,"
  done
fi

squeue $SFLAGS | awk '{print $1}' | xargs -n 1 scancel
