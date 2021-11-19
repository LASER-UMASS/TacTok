#!/usr/bin/env bash

TT_DIR=$HOME/work/TacTok
REMOTE_TT_DIR=gypsum.cs.umass.edu:TacTok

FLAGS_DEFAULT="--no-locals-file --bpe-merges=4096"

run-experiment () (
    EVAL_ID=$1
    shift 1
    rsync -avzz ${REMOTE_TT_DIR}/TacTok/runs/checkpoints/${EVAL_ID} \
          ${TT_DIR}/TacTok/runs/checkpoints/
    ${TT_DIR}/swarm/evaluate-test.sh ${EVAL_ID} ${FLAGS_DEFAULT} "$@"
)

## MAIN EXPERIMENT ##

# ASTactic + I
run-experiment paper-as+i --no_prev_tactics

# Tac + I
run-experiment paper-tac+i \
       --tac_vocab_file=tac_vocab_no_unk.pickle \
       --cutoff_len=3

# Tok + I
run-experiment paper-tok+i


## TECHNIQUES EXPERIMENT ##

# Tok + Paths
run-experiment paper-tok+paths \
               --max-ident-chunks=0 --no_defs --no_locals --no_constructors

# Tok + Constructors
run-experiment paper-tok+cons \
               --max-ident-chunks=0 --no_defs --no_locals --no_paths

# Tok + Globals
run-experiment paper-tok+globals \
               --max-ident-chunks=0 --no_locals --no_paths --no_constructors

# Tok + Locals
run-experiment paper-tok+locals \
               --max-ident-chunks=0 --no_defs --no_paths --no_constructors

## BPE EXPERIMENT ##

# Tok + Paths + BPE
run-experiment paper-tok+paths+bpe \
               --no_defs --no_locals --no_constructors

# Tok + Constructors + BPE
run-experiment paper-tok+cons+bpe \
               --max-ident-chunks=0 --no_defs --no_locals --no_paths

# Tok + Globals
run-experiment paper-tok+globals+bpe \
               --no_locals --no_paths --no_constructors

# Tok + Locals
run-experiment paper-tok+locals+bpe \
               --no_defs --no_paths --no_constructors


## MERGED IDENTS ##
run-experiment paper-merged \
               --merge_vocab

## GLOBAL VOCAB SIZE ##
for vocab_size in {20..900..10}; do
    run-experiment paper-globals-vsize-${vocab_size} \
                   --def_vocab_file='./names/names-known-${vocab_size}.pickle'
done

## LOCAL VOCAB SIZE ##
for vocab_size in {20..900..10}; do
    run-experiment paper-locals-vsize-${vocab_size} \
                   --local_vocab_file='./names/locals-known-${vocab_size}.pickle'
done

## PATH VOCAB SIZE ##
for vocab_size in {20..900..10}; do
    run-experiment paper-paths-vsize-${vocab_size} \
                   --path_vocab_file='./names/paths-known-${vocab_size}.pickle'
done

## CONSTRUCTOR VOCAB SIZE ##
for vocab_size in {20..900..10}; do
    run-experiment paper-cons-vsize-${vocab_size} \
                   --constructor_vocab_file='./names/constructors-known-${vocab_size}.pickle'
done

## BPE MERGES ##
for bpe_merges in 256 512 1024 2048 4096 8192 16384; do
    run-experiment paper-bpe-merges-${bpe_merges} \
                   --bpe-merges=${bpe_merges}
done
