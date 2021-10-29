#!/usr/bin/env bash
set -e

[[ "$#" -ne 1 ]] && echo "Wrong number of parameters! This script takes one argument, a directory to search" && exit 1

TT_DIR=$HOME/work/TacTok 

$TT_DIR/jobs/find_missing_outputs_csv.sh $@ |
while IFS=, read -r proj_idx proj_name file_idx file_name proof_idx proof_name; do
  sbatch -p longq --output=output/evaluate/evaluate_proj_${proj_idx}_${file_idx}.out \
    jobs/evaluate_proj.sh --proj_idx ${proj_idx} --file_idx ${file_idx} --output_dir=bpe_evaluation
done
