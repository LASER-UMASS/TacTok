#!/usr/bin/env bash

TT_DIR=$HOME/TacTok

FLAGS_DEFAULT="--num-epochs=3 --no-locals-file --max-ident-chunks=4 --bpe-merges=4096"

train-experiment () (
    QUEUE=$1
    EVAL_ID=$2
    shift 2
    sbatch -p $QUEUE --gres=gpu:1 --mem=8000 --output=$TT_DIR/output/paper-train/$EVAL_ID \
           -J $EVAL_ID $TT_DIR/swarm/basic_train.sh \
           --exp_id=$EVAL_ID ${FLAGS_DEFAULT} "$@"
)

## MAIN EXPERIMENT ##

# ASTactic + I
train-experiment titanx-long paper-as+i \
       --no_prev_tactics

# Tac + I
train-experiment titanx-long paper-tac+i \
       --tac_vocab_file=tac_vocab_no_unk.pickle \
       --cutoff_len=3

# Tok + I
train-experiment titanx-longn paper-tok+i

## TECHNIQUES EXPERIMENT ##

# Tok + Paths
train-experiment titanx-long paper-tok+paths \
       --max-ident-chunks=0 --no_defs --no_locals --no_constructors

# Tok + Constructors
train-experiment titanx-long paper-tok+cons \
      --max-ident-chunks=0 --no_defs --no_locals --no_paths

# Tok + Globals
train-experiment titanx-long paper-tok+globals \
       --max-ident-chunks=0 --no_locals --no_paths --no_constructors

# Tok + Locals
train-experiment titanx-long paper-tok+locals \
       --max-ident-chunks=0 --no_defs --no_paths --no_constructors

## BPE EXPERIMENT ##

# Tok + Paths + BPE
train-experiment titanx-long paper-tok+paths+bpe \
       --no_defs --no_locals --no_constructors

# Tok + Constructors + BPE
train-experiment titanx-long paper-tok+cons+bpe \
      --max-ident-chunks=0 --no_defs --no_locals --no_paths

# Tok + Globals
train-experiment titanx-long paper-tok+globals+bpe \
       --no_locals --no_paths --no_constructors

# Tok + Locals
train-experiment titanx-long paper-tok+locals+bpe \
       --no_defs --no_paths --no_constructors


## MERGED IDENTS ##
train-experiment titanx-long paper-tok+merged \
       --merge_vocab

## GLOBAL VOCAB SIZE ##
for vocab_size in {20..900..10}; do
    train-experiment 1080ti-long paper-globals-vsize-${vocab_size} \
           --def_vocab_file='./names/names-known-${vocab_size}.pickle'
done

## LOCAL VOCAB SIZE ##
for vocab_size in {20..900..10}; do
    train-experiment 1080ti-long paper-locals-vsize-${vocab_size} \
           --local_vocab_file='./names/locals-known-${vocab_size}.pickle'
done

## PATH VOCAB SIZE ##
for vocab_size in {20..900..10}; do
    train-experiment 2080ti-long paper-paths-vsize-${vocab_size}
           --path_vocab_file='./names/paths-known-${vocab_size}.pickle'
done

## CONSTRUCTOR VOCAB SIZE ##
for vocab_size in {20..900..10}; do
    train-experiment m40-long paper-cons-vsize-${vocab_size} \
           --constructor_vocab_file='./names/constructors-known-${vocab_size}.pickle'
done

## BPE MERGES ##
for bpe_merges in 256 512 1024 2048 4096 8192 16384; do
    train-experiment rtx8000-long paper-bpe-merges-${bpe_merges} \
           --bpe-merges=${bpe_merges}
done
