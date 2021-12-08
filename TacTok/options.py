import os
from datetime import datetime
import argparse
import torch
import numpy as np
import random
import json
import sys
sys.path.append(os.path.sep.join(__file__.split(os.path.sep)[:-2]))
from utils import log
import pdb
import pickle
import common_args

def parse_args():
    parser = argparse.ArgumentParser()

    common_args.add_common_args(parser)

    # experimental setup
    parser.add_argument('--include_synthetic', action='store_true')
    parser.add_argument('--exp_id', type=str)
    parser.add_argument('--datapath', type=str, default='processed/proof_steps')
    parser.add_argument('--projs_split', type=str, default='../projs_split.json')
    parser.add_argument('--num_epochs', type=int, default=4)
    parser.add_argument('--resume', type=str, help='the model checkpoint to resume')
    parser.add_argument('--no_validation', action='store_true', help='no validation is performed')
    parser.add_argument('--save_model_epochs', type=int, default=1, help='the number of epochs between model savings')
    parser.add_argument('--num_workers', type=int, default=4, help='the number of data-loading threads')
    parser.add_argument('--smoke', action='store_true')
    parser.add_argument('--seed', type=int, default=0)
    parser.add_argument('--filter', type=str)

    # optimization
    parser.add_argument('--optimizer', type=str, default='RMSprop')
    parser.add_argument('--learning_rate', type=float, default=3e-5)
    parser.add_argument('--momentum', type=float, default=0.9)
    parser.add_argument('--batchsize', type=int, default=128)
    parser.add_argument('--l2', type=float, default=1e-6)
    parser.add_argument('--lr_reduce_patience', type=int, default=3)
    parser.add_argument('--lr_reduce_steps', default=3, type=int, help='the number of steps before reducing the learning rate \
                                                             (only applicable when no_validation == True)')

    opts = parser.parse_args()

    torch.manual_seed(opts.seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False
    np.random.seed(opts.seed)
    random.seed(opts.seed)

    if opts.include_synthetic:
        opts.datapath = opts.datapath.replace('/human', '/*')

    # The identifier vocabulary
    vocab = []
    if opts.include_defs:
        vocab += list(pickle.load(open(opts.def_vocab_file, 'rb')).keys())
        vocab += ['<unk-ident>']

    # The local variable vocabulary
    if opts.include_locals:
        vocab += list(pickle.load(open(opts.local_vocab_file, 'rb')).keys())
        vocab += ['<unk-local>']

    if opts.include_paths:
        vocab += list(pickle.load(open(opts.path_vocab_file, 'rb')).keys())
        vocab += ['<unk-path>']

    opts.vocab = vocab

    if opts.exp_id is None:
        opts.exp_id = str(datetime.now())[:-7].replace(' ', '-')
    opts.log_dir = os.path.join('./runs', opts.exp_id)
    opts.checkpoint_dir = os.path.join(opts.log_dir, 'checkpoints')
    if not os.path.exists(opts.log_dir):
        os.makedirs(opts.log_dir)
        os.makedirs(os.path.join(opts.log_dir, 'predictions'))
        os.makedirs(opts.checkpoint_dir)

    opts.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    if opts.device.type == 'cpu':
        log('using CPU', 'WARNING')

    if (not opts.no_validation) and (opts.lr_reduce_steps is not None):
        log('--lr_reduce_steps is applicable only when no_validation == True', 'ERROR')

    log(opts)
    return opts


if __name__ == '__main__':
  opts = parse_args()
