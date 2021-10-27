#!/usr/bin/env bash

TT_DIR=$HOME/work/TacTok
PROJ=$(jq -r ".projs_test[]" ${TT_DIR}/projs_split.json | awk "NR==($1+1)")
NUM_FILES=$(find ${TT_DIR}/data/${PROJ} -name "*.json" | wc -l)

for file_idx in $(eval echo "{1..$NUM_FILES}"); do
  sbatch -p longq --output=output/evaluate/evaluate_proj_${1}_${file_idx}.out --mem=5G \
    jobs/evaluate_proj_tactok.sh --proj_idx $1 --file_idx ${file_idx} --output_dir=bpe_evaluation
done
