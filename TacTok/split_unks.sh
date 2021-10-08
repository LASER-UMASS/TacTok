#!/bin/bash

cd names

function split_unk_thresh {
  python ../split_unk.py names.pickle --threshold $1
  python ../split_unk.py locals.pickle --threshold $1
  mv names-known.pickle names-known-$1.pickle
  mv names-unknown.pickle names-unknown-$1.pickle
  mv locals-known.pickle locals-known-$1.pickle
  mv locals-unknown.pickle locals-unknown-$1.pickle
}

threshold=1000
while [ $threshold -ge 10 ]
do
  split_unk_thresh $threshold
  ((threshold-=20))
done

cd ..
