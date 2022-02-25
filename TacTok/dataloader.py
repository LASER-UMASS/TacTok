import torch
from torch.utils.data import Dataset, DataLoader
from training_options import parse_args
import random
from progressbar import ProgressBar
import os
import os.path
import sys
sys.setrecursionlimit(100000)
import pickle
from collections import defaultdict
import numpy as np
from glob import glob
import json
import pdb
from pathlib import Path


class ProofStepsData(Dataset):

    def __init__(self, split, opts):
        super().__init__()
        self.opts = opts

        if split in ['train', 'valid']:
            self.proof_steps = glob(os.path.join(opts.datapath, split, '*.pickle'))
        elif split == 'train_valid':
            self.proof_steps = glob(os.path.join(opts.datapath, 'train/*.pickle')) + \
                               glob(os.path.join(opts.datapath, 'valid/*.pickle'))
        if opts.max_tuples is not None:
            self.proof_steps = self.proof_steps[:opts.max_tuples]
        if opts.import_ordering and split == 'train_valid':
            with open(opts.import_ordering, 'r') as f:
                ordering = [path.strip() for path in f]
            for path in ordering:
                fullpath = os.path.join(opts.datapath, path)
                assert os.path.exists(fullpath), f"File in ordering isn't present in data! {fullpath}"
            assert len(ordering) > 0
            self.proof_steps = [os.path.join(opts.datapath, step_path) for step_path in ordering]
        else:
            random.shuffle(self.proof_steps)
        if opts.export_ordering and split == 'train_valid':
            with open(opts.export_ordering, 'w') as f:
                for filename in self.proof_steps:
                    parts = Path(filename).parts
                    print(os.path.join(*parts[-2:]), file=f)
        print('%d proof steps in %s' % (len(self), split))


    def __len__(self):
        return len(self.proof_steps)


    def __getitem__(self, idx):
        '''
        step = {
            'file': STR,
            'proof_name': STR,
            'n_step': INT,
            'env': [{
                'qualid': STR,
                'ast': LARK.TREE.TREE,
            }]
            'local_context': [{
                'ident': STR,
                'ast': LARK.TREE.TREE,
            }],
            'goal': LARK.TREE.TREE,
            'tactic_actions':  [INT|STR],
            'tactic_str': STR,
        }
        '''
        proof_step = pickle.load(open(self.proof_steps[idx], 'rb'))
        proof_step['goal'] = proof_step['goal']['ast']
        proof_step['tactic_actions'] = proof_step['tactic']['actions']
        proof_step['tactic_str'] = proof_step['tactic']['text']
        del proof_step['tactic']

        return proof_step


def create_dataloader(split, opts):
    def merge(batch):
        fields = ['file', 'proof_name', 'n_step', 'env', 'local_context', 'goal', 'is_synthetic', 'tactic_actions', 'tactic_str', 'prev_tokens']
        data_batch = {key: [] for key in fields}
        for example in batch:
            for key, value in example.items():
                if key not in fields:
                     continue
                data_batch[key].append(value)
        return data_batch

    ds = ProofStepsData(split, opts)
    return DataLoader(ds, opts.batchsize, shuffle=split.startswith('train'), collate_fn=merge,
                      num_workers=opts.num_workers)


if __name__ == '__main__':
    opts = parse_args()
    loader = create_dataloader('train', opts)
    bar = ProgressBar(max_value=len(loader))
    for i, data_batch in enumerate(loader):
        if i == 0:
            print(data_batch)
        bar.update(i)
