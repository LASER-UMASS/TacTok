import torch
import torch.nn as nn
from tac_grammar import CFG
from .tactic_decoder import TacticDecoder
from .term_encoder import TermEncoder
import pdb
import os
from itertools import chain
import sys
sys.path.append(os.path.abspath('.'))
from time import time
from torch.nn import Embedding, LSTM
import pickle

class Prover(nn.Module):

    def __init__(self, opts):
        super().__init__()
        self.opts = opts
        self.tactic_decoder = TacticDecoder(CFG(opts.tac_grammar, 'tactic_expr'), opts)
        self.term_encoder = TermEncoder(opts)
        self.tactic_embedding = Embedding(opts.num_tactics, 256, padding_idx=0)
        self.tactic_LSTM = LSTM(256, 256, 1, batch_first=True, bidirectional=True)
        self.tac_vocab = pickle.load(open(opts.tac_vocab_file, 'rb'))
        self.cutoff_len = opts.cutoff_len
        
    def create_tactic_batch(self, tok_seq):
        mod_tok_seq = []
        if '<unk>' in self.tac_vocab:
            for item in tok_seq:
                mod_item = [self.tac_vocab[i] if i in self.tac_vocab else self.tac_vocab['<unk>'] for i in item]
                mod_tok_seq.append(mod_item)
        else:
            for item in tok_seq:
                mod_item = [self.tac_vocab[i] for i in item if i in self.tac_vocab]
                mod_tok_seq.append(mod_item)

        max_len = min(max([len(item) for item in mod_tok_seq]), self.cutoff_len)
        batch = []
        lens = []
        for item in mod_tok_seq:
            idx = self.cutoff_len - 1 # ex: 29, for len 30
            lens.append(len(item[-idx:]) + 1)
            new_item = [self.tac_vocab['<start>']] + item[-idx:] + [self.tac_vocab['<pad>']]*(max_len-len(item[-idx:])-1)
            batch.append(new_item)

        return torch.tensor(batch, device=self.opts.device), lens

    def embed_terms(self, environment, local_context, goal, tok_seq=None):
        all_asts = list(chain([env['ast'] for env in chain(*environment)], [context['ast'] for context in chain(*local_context)], goal))
        all_embeddings = self.term_encoder(all_asts)

        batchsize = len(environment)
        environment_embeddings = []
        j = 0
        for n in range(batchsize):
            size = len(environment[n])
            environment_embeddings.append(torch.cat([torch.zeros(size, 3, device=self.opts.device), 
                                                     all_embeddings[j : j + size]], dim=1))
            environment_embeddings[-1][:, 0] = 1.0
            j += size

        context_embeddings = []
        for n in range(batchsize):
            size = len(local_context[n])
            context_embeddings.append(torch.cat([torch.zeros(size, 3, device=self.opts.device), 
                                                 all_embeddings[j : j + size]], dim=1))
            context_embeddings[-1][:, 1] = 1.0
            j += size

        goal_embeddings = []
        for n in range(batchsize):
            goal_embeddings.append(torch.cat([torch.zeros(3, device=self.opts.device), all_embeddings[j]], dim=0))
            goal_embeddings[-1][2] = 1.0
            j += 1
        goal_embeddings = torch.stack(goal_embeddings)

        if tok_seq:
            tactic_batch, lens = self.create_tactic_batch(tok_seq)
            tactic_embeddings = self.tactic_embedding(tactic_batch)
            X = torch.nn.utils.rnn.pack_padded_sequence(tactic_embeddings, lens, batch_first=True, enforce_sorted=False)
            tactic_seq_embeddings, _ = self.tactic_LSTM(X)
            tactic_seq_embeddings, _ = torch.nn.utils.rnn.pad_packed_sequence(tactic_seq_embeddings, batch_first=True)
            tactic_seq_embeddings = tactic_seq_embeddings[:, -1, :]
            return environment_embeddings, context_embeddings, goal_embeddings, tactic_seq_embeddings


        return environment_embeddings, context_embeddings, goal_embeddings


    def forward(self, environment, local_context, goal, actions, teacher_forcing, tok_seq=None):
        environment_embeddings, context_embeddings, goal_embeddings, seq_embeddings = \
          self.embed_terms(environment, local_context, goal, tok_seq)
        environment = [{'idents': [v['qualid'] for v in env], 
                        'embeddings': environment_embeddings[i], 
                        'quantified_idents': [v['ast'].quantified_idents for v in env]}
                          for i, env in enumerate(environment)]
        local_context = [{'idents': [v['ident'] for v in context], 
                          'embeddings': context_embeddings[i],
                          'quantified_idents': [v['ast'].quantified_idents for v in context]}
                            for i, context in enumerate(local_context)]
        goal = {'embeddings': goal_embeddings, 'quantified_idents': [g.quantified_idents for g in goal]}
        asts, loss = self.tactic_decoder(environment, local_context, goal, actions, teacher_forcing, seq_embeddings)
        return asts, loss


    def beam_search(self, environment, local_context, goal, tok_seq=None):
        environment_embeddings, context_embeddings, goal_embeddings, seq_embeddings = \
          self.embed_terms([environment], [local_context], [goal], [tok_seq])
        environment = {'idents': [v['qualid'] for v in environment],
                       'embeddings': environment_embeddings[0],
                       'quantified_idents': [v['ast'].quantified_idents for v in environment]}
        local_context = {'idents': [v['ident'] for v in local_context],
                         'embeddings': context_embeddings[0],
                         'quantified_idents': [v['ast'].quantified_idents for v in local_context]}
        goal = {'embeddings': goal_embeddings, 'quantified_idents': goal.quantified_idents}
        asts = self.tactic_decoder.beam_search(environment, local_context, goal, seq_embeddings)
        return asts
