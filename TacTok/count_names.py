import os
import json
import pickle
import sys
sys.setrecursionlimit(100000)
sys.path.append(os.path.normpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../')))
from syntax import SyntaxConfig
from gallina import GallinaTermParser
from lark.exceptions import UnexpectedCharacters, ParseError
import argparse
from utils import iter_proofs, SexpCache
from lark.tree import Tree

# Count occurrences of names in the training data.
# Based heavily on extract_proof_steps for the boilerplate.

projs_split = json.load(open('../projs_split.json'))

defs = {}
local_defs = {}
paths = {}
merged = {}

syn_conf = SyntaxConfig(include_locals=True, include_defs=True, include_paths=True)
term_parser = GallinaTermParser(syn_conf, caching=True)
sexp_cache = SexpCache('../sexp_cache', readonly=True)

# Preorder traversal makes it easier
def traverse_preorder(node, callback):
    callback(node)
    for c in node.children:
        if isinstance(c, Tree):
            traverse_preorder(c, callback)

def parse_goal(g):
    return term_parser.parse(sexp_cache[g['sexp']])

def incr_ident(ident, idents):
    if ident not in idents:
        idents[ident] = 1
    else:
        idents[ident] += 1

def count(filename, proof_data):
    proj = filename.split(os.path.sep)[2]
    if not proj in projs_split['projs_train']:
        return

    proof_start = proof_data['steps'][0]
    goal_id = proof_start['goal_ids']['fg'][0]
    goal_ast = parse_goal(proof_data['goals'][str(goal_id)])

    # count occurrences within a goal
    def count_in_goal(node):
        if SyntaxConfig.is_path(node):
            # paths
            if syn_conf.include_paths:
                for c in node.children:
                    ident = c.children[0].data
                    incr_ident(ident, paths)
                    incr_ident(ident, merged)
            node.children = [] # don't treat these like global definitions
        elif syn_conf.include_defs and SyntaxConfig.is_ident(node):
            # global definitions and theorems
            ident = node.children[0].data
            incr_ident(ident, defs)
            incr_ident(ident, merged)
        elif syn_conf.include_locals and SyntaxConfig.is_local(node):
            # local variables
            ident = node.children[0].data
            incr_ident(ident, local_defs)
            incr_ident(ident, merged)

    traverse_preorder(goal_ast, count_in_goal)

def dump(dirname, filename, idents):
    names_file = open(os.path.join(dirname, filename), 'wb')
    pickle.dump(idents, names_file)
    names_file.close()

def dump_idents(dirname):
    if not os.path.exists(dirname):
        os.makedirs(dirname)

    if syn_conf.include_defs:
        dump(dirname, 'names.pickle', defs)

    if syn_conf.include_locals:
        dump(dirname, 'locals.pickle', local_defs)

    if syn_conf.include_paths:
        dump(dirname, 'paths.pickle', paths)

    dump(dirname, 'merged.pickle', merged)

    print('output saved to ', dirname)

if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser(description='Count occurrences of named datatypes and constants in the data')
    arg_parser.add_argument('--data_root', type=str, default='../data',
                                help='The folder for CoqGym')
    arg_parser.add_argument('--output', type=str, default='./names/',
                                help='The output file')
    arg_parser.add_argument('--no_defs', action='store_false', dest='include_defs', help='do not include the names of definitions and theorems in the model')
    arg_parser.add_argument('--no_locals', action='store_false', dest='include_locals', help='do not include the names of local variables in the model')
    arg_parser.add_argument('--no_paths', action='store_false', dest='include_paths', help='do not include the paths of definitions and theorems in the model')
    args = arg_parser.parse_args()
    print(args)
    
    syntax_config = SyntaxConfig(args.include_locals, args.include_defs, args.include_paths)
    term_parser = GallinaTermParser(syn_conf, caching=True)

    iter_proofs(args.data_root, count, include_synthetic=False, show_progress=True)

    dump_idents(args.output)

