import torch
import torch.nn as nn
import torch.nn.functional as F
import math
from collections import defaultdict, Counter
from time import time
from itertools import chain
from lark.tree import Tree
import os
from syntax import SyntaxConfig
from gallina import traverse_postorder
import pdb
import pickle
import json
from .bpe import LongestMatchTokenizer, get_bpe_vocab
from utils import log
import sys
import hashlib

nonterminals = [
    'constr__constr',
    'constructor_rel',
    'constructor_var',
    'constructor_meta',
    'constructor_evar',
    'constructor_sort',
    'constructor_cast',
    'constructor_prod',
    'constructor_lambda',
    'constructor_letin',
    'constructor_app',
    'constructor_const',
    'constructor_ind',
    'constructor_construct',
    'constructor_case',
    'constructor_fix',
    'constructor_cofix',
    'constructor_proj',
    'constructor_ser_evar',
    'constructor_prop',
    'constructor_set',
    'constructor_type',
    'constructor_ulevel',
    'constructor_vmcast',
    'constructor_nativecast',
    'constructor_defaultcast',
    'constructor_revertcast',
    'constructor_anonymous',
    'constructor_name',
    'constructor_constant',
    'constructor_mpfile',
    'constructor_mpbound',
    'constructor_mpdot',
    'constructor_dirpath',
    'constructor_mbid',
    'constructor_instance',
    'constructor_mutind',
    'constructor_letstyle',
    'constructor_ifstyle',
    'constructor_letpatternstyle',
    'constructor_matchstyle',
    'constructor_regularstyle',
    'constructor_projection',
    'bool',
    'int',
    'names__label__t',
    'constr__case_printing',
    'univ__universe__t',
    'constr__pexistential___constr__constr',
    'names__inductive',
    'constr__case_info',
    'names__constructor',
    'constr__prec_declaration___constr__constr____constr__constr',
    'constr__pfixpoint___constr__constr____constr__constr',
    'constr__pcofixpoint___constr__constr____constr__constr',
    'names__id__t'
]

class InputOutputUpdateGate(nn.Module):

    def __init__(self, hidden_dim, vocab, opts, nonlinear):
        super().__init__()
        self.nonlinear = nonlinear
        self.vocab = vocab
        k = 1. / math.sqrt(hidden_dim)
        self.W = nn.Parameter(torch.Tensor(hidden_dim,
                                           len(vocab) + opts.ident_vec_size
                                           + hidden_dim))
        nn.init.uniform_(self.W, -k, k)
        self.b = nn.Parameter(torch.Tensor(hidden_dim))
        nn.init.uniform_(self.b, -k, k)
     

    def forward(self, xh):
        return self.nonlinear(F.linear(xh, self.W, self.b))


class ForgetGates(nn.Module):

    def __init__(self, hidden_dim, vocab, opts):
        super().__init__()
        self.hidden_dim = hidden_dim
        self.opts = opts
        k = 1. / math.sqrt(hidden_dim)
        # the weight for the input
        self.W_if = nn.Parameter(torch.Tensor(hidden_dim, len(vocab) + opts.ident_vec_size))
        nn.init.uniform_(self.W_if, -k, k)
        # the weight for the hidden
        self.W_hf = nn.Parameter(torch.Tensor(hidden_dim, hidden_dim))
        nn.init.uniform_(self.W_hf, -k, k)
        # the bias
        self.b_f = nn.Parameter(torch.Tensor(hidden_dim))
        nn.init.uniform_(self.b_f, -k, k)


    def forward(self, x, h_children, c_children):
        c_remain = torch.zeros(x.size(0), self.hidden_dim).to(self.opts.device)

        Wx = F.linear(x, self.W_if)
        all_h = list(chain(*h_children))
        if all_h == []:
            return c_remain
        Uh = F.linear(torch.stack(all_h), self.W_hf, self.b_f)
        i = 0
        for j, h in enumerate(h_children):
            if h == []:
                continue
            f_gates = torch.sigmoid(Wx[j] + Uh[i : i + len(h)])
            i += len(h)
            c_remain[j] = (f_gates * torch.stack(c_children[j])).sum(dim=0)
       
        return c_remain


class TermEncoder(nn.Module):

    def __init__(self, opts):
        super().__init__()
        self.opts = opts
        self.syn_conf = SyntaxConfig(opts.include_locals, opts.include_defs, opts.include_paths,
                                     opts.include_constructor_names, opts.merge_vocab)
        self.vocab = opts.vocab + nonterminals
        self.input_gate = InputOutputUpdateGate(opts.term_embedding_dim, self.vocab, opts,
                                                nonlinear=torch.sigmoid)
        self.forget_gates = ForgetGates(opts.term_embedding_dim, self.vocab, opts)
        self.output_gate = InputOutputUpdateGate(opts.term_embedding_dim, self.vocab, opts,
                                                 nonlinear=torch.sigmoid)
        self.update_cell = InputOutputUpdateGate(opts.term_embedding_dim, self.vocab, opts,
                                                 nonlinear=torch.tanh)
        # By default, load the vocabulary passed in --globals-file; this defaults to the
        # globals vocabulary but can be set to any other by command line.
        occurances = pickle.load(open(opts.globals_file, 'rb'))
        
        # Non-default vocabularies
        if opts.merge_vocab:
            # If passed --merge_vocab, use the merged vocabulary instead
            occurances = pickle.load(open(opts.merged_file, 'rb'))
        elif opts.use_locals_file:
            # Otherwise, if not passed --no-locals, merge in the locals vocabulary.
            occurances.update(
              pickle.load(open(opts.locals_file, 'rb')))
        occurances.update(pickle.load(open(opts.paths_file, 'rb')))
        if opts.case_insensitive_idents:
            occurances = Counter({word.lower(): count for (word,count) in occurances.items()})

        vocab = None
        occurances_hash = hashlib.sha256(json.dumps(occurances, sort_keys=True).encode()).hexdigest()
        if opts.load_subwords and os.path.exists(opts.load_subwords):
            with open(opts.load_subwords, 'r') as f:
                stamp, num_merges, vocab = json.load(f)
            if stamp != occurances_hash:
                log("Warning: Loaded subwords don't match the occurances we loaded, regenerating")
                vocab = None
            if num_merges != opts.bpe_merges:
                log("Warning: Loaded subwords don't match the num merges we loaded, regenerating")
                vocab = None
        if vocab == None:
            vocab = get_bpe_vocab(occurances, opts.bpe_merges)
            if opts.save_subwords:
                with open(opts.save_subwords, 'w') as f:
                    json.dump((occurances_hash, num_merges, vocab), f)
        self.name_tokenizer = \
            LongestMatchTokenizer(vocab,
                                  include_unks=opts.include_unks)

        self.name_encoder = nn.RNN(self.name_tokenizer.vocab_size + 1,
                                   opts.ident_vec_size, batch_first=True)

    def get_vocab_idx(self, node, localnodes, paths, cnames):
        data = node.data
        vocab = self.vocab
        merge_vocab = self.opts.merge_vocab
        if data in vocab:
            return vocab.index(data)
        elif (node in localnodes) and not merge_vocab:
            return vocab.index('<unk-local>')
        elif (node in paths) and not merge_vocab:
            return vocab.index('<unk-path>')
        elif (node in cnames) and not merge_vocab:
            return vocab.index('<unk-constructor>')
        else:
            return vocab.index('<unk-ident>')

    def normalize_length(self, length, pad, seq):
        if len(seq) > length:
            return seq[:length]
        elif len(seq) < length:
            return seq + [pad] * (length - len(seq))
        else:
            return seq

    def should_bpe_encode(self, node):
        if SyntaxConfig.is_local(node) and self.opts.include_locals:
            return True
        if SyntaxConfig.is_ident(node) and self.opts.include_defs:
            return True
        if SyntaxConfig.is_constructor(node) and self.opts.include_constructor_names:
            return True
        return False

    def encode_identifiers(self, nodes):
        encoder_initial_hidden = torch.zeros(1, len(nodes),
                                             self.opts.ident_vec_size,
                                             device=self.opts.device)
        if self.opts.max_ident_chunks == 0:
            return encoder_initial_hidden[0]
        node_identifier_chunks = \
          torch.tensor([self.normalize_length(
                          self.opts.max_ident_chunks,
                          0,
                          # Add 1 here to account for the padding value of zero
                          [tok + 1 for tok in
                           self.name_tokenizer.tokenize_to_idx(
                             node.children[-1].data.lower() if self.opts.case_insensitive_idents
                             else node.children[-1].data)]
                          # This checks to see if the node is some sort of identifier,
                          # including an identifier that makes up part of a path
                           if self.should_bpe_encode(node) else
                           [])
                        for node in nodes],
                       device=self.opts.device)
        one_hot_chunks = \
          torch.zeros(len(nodes), self.opts.max_ident_chunks,
                      self.name_tokenizer.vocab_size + 1,
                      device=self.opts.device)\
               .scatter_(2,
                         node_identifier_chunks.unsqueeze(2),
                         1.0)

        output, final_hidden = self.name_encoder(one_hot_chunks,
                                                 encoder_initial_hidden)
        return final_hidden[0]

    def forward(self, term_asts):
        # the height of a node determines when it can be processed
        height2nodes = defaultdict(set)
        localnodes = set()
        paths = set()
        cnames = set()
        
        def get_metadata(node):
            height2nodes[node.height].add(node)
            if self.syn_conf.include_paths and SyntaxConfig.is_path(node):
                for c in node.children:
                    assert len(c.children) > 0
                    paths.update(c.children)
            if self.syn_conf.include_locals and SyntaxConfig.is_local(node):
                assert len(node.children) > 0
                localnodes.update(node.children)
            if self.syn_conf.include_constructor_names and SyntaxConfig.is_constructor(node):
                child = node.children[-1]
                if SyntaxConfig.is_ident(child):
                    cnames.add(child.children[0])

        for ast in term_asts:
            traverse_postorder(ast, get_metadata)

        memory_cells = {} # node -> memory cell
        hidden_states = {} # node -> hidden state
        #return torch.zeros(len(term_asts), self.opts.term_embedding_dim).to(self.opts.device)

        # compute the embedding for each node
        for height in sorted(height2nodes.keys()):
            nodes_at_height = list(height2nodes[height])
            # sum up the hidden states of the children
            h_sum = []
            c_remains = []
            x0 = torch.zeros(len(nodes_at_height), len(self.vocab),
                             device=self.opts.device) \
                      .scatter_(1, torch.tensor([self.get_vocab_idx(node, localnodes, paths, cnames) for node in nodes_at_height],
                                                device=self.opts.device).unsqueeze(1), 1.0)

            x1 = self.encode_identifiers(nodes_at_height)
            x = torch.cat((x0, x1), dim=1)


            h_sum = torch.zeros(len(nodes_at_height), self.opts.term_embedding_dim).to(self.opts.device)
            h_children = []
            c_children = []
            for j, node in enumerate(nodes_at_height):
                h_children.append([])
                c_children.append([])
                for c in node.children:
                    h = hidden_states[c]
                    h_sum[j] += h
                    h_children[-1].append(h)
                    c_children[-1].append(memory_cells[c])
            c_remains = self.forget_gates(x, h_children, c_children)

            # gates
            xh = torch.cat([x, h_sum], dim=1)
            i_gate = self.input_gate(xh)
            o_gate = self.output_gate(xh)
            u = self.update_cell(xh)
            cells = i_gate * u + c_remains
            hiddens = o_gate * torch.tanh(cells)


            for i, node in enumerate(nodes_at_height):
                memory_cells[node] = cells[i]
                hidden_states[node] = hiddens[i]

        return torch.stack([hidden_states[ast] for ast in term_asts])
