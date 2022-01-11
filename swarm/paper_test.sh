#!/usr/bin/env bash

TT_DIR=$HOME/work/TacTok
REMOTE_TT_DIR=talia@gypsum.cs.umass.edu:work/TacTok

FLAGS_DEFAULT="--no-locals-file --local_vocab_file=./names/locals-known-200.pickle --bpe-merges=4096"

run-experiment () (
    EVAL_ID=$1
    shift 1
    rsync -avzz ${REMOTE_TT_DIR}/TacTok/runs/${EVAL_ID}-2f27749 \
          ${TT_DIR}/TacTok/runs/
    ${TT_DIR}/swarm/evaluate-test.sh ${EVAL_ID}-2f27749 ${FLAGS_DEFAULT} --path=./runs/${EVAL_ID}-2f27749/checkpoints/model_000.pth "$@"
)

rerun-experiment () (
    EVAL_ID=$1
    shift 1
    ${TT_DIR}/swarm/rerun-missing-proofs.sh ${EVAL_ID}-2f27749 ${FLAGS_DEFAULT} --path=./runs/${EVAL_ID}-2f27749/checkpoints/model_000.pth "$@"
)

## MAIN EXPERIMENT ##

# ASTactic + I
#run-experiment paper-as+i --no_prev_tactics

# Tac + I
#run-experiment paper-tac+i \
#       --tac_vocab_file=tac_vocab_no_unk.pickle \
#       --cutoff_len=3

# Tok + All
#run-experiment paper-tok+all
run-experiment paper-tok+all+bpe

## TECHNIQUES EXPERIMENT ##

# Tok + Paths
#run-experiment paper-tok+paths \
#               --max-ident-chunks=0 --no_defs --no_locals --no_constructors

# Tok + Constructors
#run-experiment paper-tok+cons \
#               --max-ident-chunks=0 --no_defs --no_locals --no_paths

# Tok + Globals
#rerun-experiment paper-tok+globals \
#               --max-ident-chunks=0 --no_locals --no_paths --no_constructors

# Tok + Locals
#run-experiment paper-tok+locals \
#              --max-ident-chunks=0 --no_defs --no_paths --no_constructors

## BPE EXPERIMENT ##

# Tok + Paths + BPE
#rerun-experiment paper-tok+paths+bpe \
#              --no_defs --no_locals --no_constructors

# Tok + Constructors + BPE
#rerun-experiment paper-tok+cons+bpe \
#               --no_defs --no_locals --no_paths

# Tok + Globals + BPE
#rerun-experiment paper-tok+globals+bpe \
#               --no_locals --no_paths --no_constructors

# Tok + Locals + BPE
#rerun-experiment paper-tok+locals+bpe \
#               --no_defs --no_paths --no_constructors

## MERGED IDENTS ##
#run-experiment paper-tok+merged \
#               --merge_vocab

## GLOBAL VOCAB SIZE ##
#for vocab_size in {20..900..10}; do
#    run-experiment paper-globals-vsize-${vocab_size} \
#                   --def_vocab_file='./names/names-known-${vocab_size}.pickle'
#done

## LOCAL VOCAB SIZE ##
#for vocab_size in {20..900..10}; do
#    run-experiment paper-locals-vsize-${vocab_size} \
#                   --local_vocab_file='./names/locals-known-${vocab_size}.pickle'
#done

## PATH VOCAB SIZE ##
#for vocab_size in {20..900..10}; do
#    run-experiment paper-paths-vsize-${vocab_size} \
#                   --path_vocab_file='./names/paths-known-${vocab_size}.pickle'
#done

## CONSTRUCTOR VOCAB SIZE ##
#for vocab_size in {80..80..20}; do
#    rerun-experiment paper-cons-vsize-${vocab_size} \
#                   --constructor_vocab_file="./names/constructors-known-${vocab_size}.pickle"
#done

## BPE MERGES ##
#for bpe_merges in 256 512 1024 2048 4096 8192 16384; do
#    run-experiment paper-bpe-merges-${bpe_merges} \
#                   --bpe-merges=${bpe_merges}
#done
