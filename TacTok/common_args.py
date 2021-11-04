#!/usr/bin/env python3
import argparse

def add_common_args(parser: argparse.ArgumentParser):

    parser.add_argument('--tac_grammar', type=str, default='tactics.ebnf')
    
    # global options
    parser.add_argument('--no_defs', action='store_false', dest='include_defs', help='do not include the names of definitions and theorems in the model')
    parser.add_argument('--no_locals', action='store_false', dest='include_locals', help='do not include the names of local variables in the model')

    # term encoder
    parser.add_argument('--term_embedding_dim', type=int, default=128)
    parser.add_argument('--num_tactics', type=int, default=15025)
    parser.add_argument('--tac_vocab_file', type=str, default='token_vocab.pickle')
    parser.add_argument('--def_vocab_file', type=str, default='./names/names-known-200.pickle')
    parser.add_argument('--local_vocab_file', type=str, default='./names/locals-known-40.pickle')
    parser.add_argument('--cutoff_len', type=int, default=30)

    # Subwords options
    parser.add_argument('--globals-file', type=str, default='./names/names.pickle')
    parser.add_argument('--locals-file', type=str, default='./names/locals.pickle')
    parser.add_argument('--no-locals-file', action='store_false', dest='use_locals_file')
    parser.add_argument('--bpe-merges', type=int, default=1024)
    parser.add_argument('--ident-vec-size', type=int, default=32)
    parser.add_argument('--max-ident-chunks', type=int, default=8)
    parser.add_argument('--include-unks', action='store_true')
    parser.add_argument('--dump-subwords', type=str, default=None)
    parser.add_argument('--case-insensitive-idents', action='store_true')

    # tactic decoder
    parser.add_argument('--size_limit', type=int, default=50)
    parser.add_argument('--embedding_dim', type=int, default=128, help='dimension of the grammar embeddings')
    parser.add_argument('--symbol_dim', type=int, default=128, help='dimension of the terminal/nonterminal symbol embeddings')
    parser.add_argument('--hidden_dim', type=int, default=128, help='dimension of the LSTM controller')

    parser.add_argument('--teacher_forcing', type=float, default=1.0)

    parser.add_argument('--debug', action='store_true')
