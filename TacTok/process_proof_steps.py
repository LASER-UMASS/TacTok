import torch
from torch.utils.data import Dataset, DataLoader
from options import parse_args
import random
from progressbar import ProgressBar
import os
import sys
sys.setrecursionlimit(100000)
import pickle
from collections import defaultdict
import numpy as np
from glob import glob
import json
import pdb
import string

rem_punc = string.punctuation.replace('\'','').replace('_', '')
table = str.maketrans('', '', rem_punc)

def tokenize_text(raw_text):
	without_punc = raw_text.translate(table)
	words = without_punc.split()
	return words


proof_steps = glob(os.path.join('proof_steps', 'train/*.pickle')) + \
                               glob(os.path.join('proof_steps', 'valid/*.pickle'))

proofs = {}

print(len(proof_steps))
print("Collecting proofs from steps")
for idx in range(len(proof_steps)):
	f = open(proof_steps[idx], 'rb')
	proof_step = pickle.load(f)
	f.close()
	key = (proof_step['file'], proof_step['proof_name'])
	n_step = proof_step['n_step']
	if key not in proofs:
		proofs[key] = {}
	proofs[key][n_step] = idx


print("Generating new proof steps")
for p_key in proofs:
	seq_raw = [] # list of strings, each string is a command
	seq_proc_separated = [] # list of lists of strings, each string is a token
	seq_proc_complete = [] # list of strings, each string is a token
	proof = proofs[p_key] # dictionary

	for n_key in sorted(proof.keys()):

		idx = proof[n_key]
		f = open(proof_steps[idx], 'rb')
		proof_step = pickle.load(f)
		f.close()
		proof_step['prev_strings'] = seq_raw
		proof_step['prev_tactic_list'] = seq_proc_separated
		proof_step['prev_tokens'] = seq_proc_complete
		new_file_name = os.path.join('processed', proof_steps[idx])
		new_f = open(new_file_name, 'wb')
		pickle.dump(proof_step, new_f)
		new_f.close()
		raw_text = proof_step['tactic']['text']
		text_words = tokenize_text(raw_text)
		seq_raw.append(raw_text) 
		seq_proc_separated.append(text_words)
		seq_proc_complete += text_words
