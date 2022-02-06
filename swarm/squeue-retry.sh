#!/usr/bin/env bash

BACKOFF_AMOUNT=0.001
while
    squeue "$@" 2> /dev/null
    (( $? != 0 ))
do 
   /usr/bin/env sleep $BACKOFF_AMOUNT
   BACKOFF_AMOUNT=$(echo "$BACKOFF_AMOUNT * 2" | bc)
done
