import argparse
import json
import sys
import os

sys.path.append(os.path.sep.join(__file__.split(os.path.sep)[:-2]))
from utils import log


class ConfigParser(argparse.ArgumentParser):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_argument('--export_config', type=str, default=None)
        self.add_argument('--config', type=str, default=None)

    def parse_args(self, *args, **kwargs):
        opts = super().parse_args(*args, **kwargs)

        is_parallel = "parallel" in opts and opts.parallel

        # if we are parallelizing over projects, only export args for the first project
        if opts.config is not None and (not is_parallel or opts.proj_idx == 0):
            with open(opts.config) as f:
                loaded = json.load(f)
                if not set(loaded).issubset(opts.__dict__):
                    raise ValueError(
                        'Invalid argument found in config. Did you pass the right file?')
                opts.__dict__.update(**loaded)

        if opts.export_config is not None:
            with open(opts.export_config, 'w') as f:
                opts_dict = vars(opts)
                opts_dict.pop('export_config')
                opts_dict.pop('config')
                json.dump(opts_dict, f, separators=(',\n', ':'))

        log(opts)

        return opts

    def add_common_args(self):
        parser = super()
        parser.add_argument('--tac_grammar', type=str, default='tactics.ebnf')

        # global options
        parser.add_argument('--no_defs', action='store_false', dest='include_defs',
                            help='do not include the names of definitions and theorems in the model')
        parser.add_argument('--no_locals', action='store_false', dest='include_locals',
                            help='do not include the names of local variables in the model')
        parser.add_argument('--no_paths', action='store_false', dest='include_paths',
                            help='do not include fully qualified paths in the model')
        parser.add_argument('--no_constructors', action='store_false',
                            dest='include_constructor_names',
                            help='do not include constructor names in the model')
        parser.add_argument('--training', action='store_false', dest='include_serapi',
                            help='training (so do not initialize serapi)')
        parser.add_argument('--parallel', action='store_true',
                            help='whether the computation is being parallelized over projects')
        # term encoder
        parser.add_argument('--term_embedding_dim', type=int, default=128)
        parser.add_argument('--num_tactics', type=int, default=15025)
        parser.add_argument('--tac_vocab_file', type=str, default='token_vocab.pickle')
        parser.add_argument('--def_vocab_file', type=str, default='./names/names-known-200.pickle')
        parser.add_argument('--local_vocab_file', type=str,
                            default='./names/locals-known-200.pickle')
        parser.add_argument('--path_vocab_file', type=str,
                            default='./names/paths-known-200.pickle')
        parser.add_argument('--constructor_vocab_file', type=str,
                            default='./names/constructors-known-100.pickle')
        parser.add_argument('--cutoff_len', type=int, default=30)
        parser.add_argument('--merge_vocab', action='store_true',
                            help='Merge all identifier vocabularies, with a single unknown')

        parser.add_argument('--tac_embedding', type=int, default=256,
                            help='dimension of the tactic encoder embedding')
        parser.add_argument('--tac_layers', type=int, default=1,
                            help='number of layers in the tactic LSTM')

        parser.add_argument('--no_prev_tactics', action='store_false', dest='include_prev_tactics',
                            help='do not encode prev tactics (become ASTactic)')

        # Subwords options
        parser.add_argument('--merged-file', type=str, default='./names/merged.pickle')
        parser.add_argument('--globals-file', type=str, default='./names/names.pickle')
        parser.add_argument('--locals-file', type=str, default='./names/locals.pickle')
        parser.add_argument('--paths-file', type=str, default='./names/paths.pickle')
        parser.add_argument('--no-locals-file', action='store_false', dest='use_locals_file')
        parser.add_argument('--bpe-merges', type=int, default=4096)
        parser.add_argument('--ident-vec-size', type=int, default=32)
        parser.add_argument('--max-ident-chunks', type=int, default=8)
        parser.add_argument('--include-unks', action='store_true')
        parser.add_argument('--save-subwords', type=str, default="names/subwords.json")
        parser.add_argument('--load-subwords', type=str, default="names/subwords.json")
        parser.add_argument('--case-insensitive-idents', action='store_true')

        # tactic decoder
        parser.add_argument('--size_limit', type=int, default=50)
        parser.add_argument('--embedding_dim', type=int, default=128,
                            help='dimension of the grammar embeddings')
        parser.add_argument('--symbol_dim', type=int, default=128,
                            help='dimension of the terminal/nonterminal symbol embeddings')
        parser.add_argument('--hidden_dim', type=int, default=128,
                            help='dimension of the LSTM controller')

        parser.add_argument('--teacher_forcing', type=float, default=1.0)

        parser.add_argument('--debug', action='store_true')
