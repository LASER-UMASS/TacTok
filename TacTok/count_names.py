import os
import json
import pickle
import sys
import functools
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
constructor_names = {}

sexp_cache = SexpCache('../sexp_cache', readonly=True)

def parse_goal(g):
    return term_parser.parse(sexp_cache[g['sexp']])

def incr_ident(ident, idents):
    if ident not in idents:
        idents[ident] = 1
    else:
        idents[ident] += 1

def count(args, term_parser, filename, proof_data):
    proj = filename.split(os.path.sep)[2]
    if not proj in projs_split['projs_train']:
        return

    proof_start = proof_data['steps'][0]
    goal_id = proof_start['goal_ids']['fg'][0]
    goal_ast = parse_goal(proof_data['goals'][str(goal_id)])

    # count occurrences within a goal
    def count_in_goal(node):
    
        def count_children(node):
            for c in node.children:
                if isinstance(c, Tree):
                    count_in_goal(c)
    
        if SyntaxConfig.is_path(node) and node.children:
            # paths
            if args.include_paths:
                for c in node.children:
                    if c.children:
                        ident = c.children[0].data
                        incr_ident(ident, paths)
                        incr_ident(ident, merged)
            if args.paths_in_defs:
                # include paths in global definitions, too
                count_children(node)
        elif args.include_defs and SyntaxConfig.is_ident(node) and node.children:
            # global definitions and theorems
            ident = node.children[0].data
            incr_ident(ident, defs)
            incr_ident(ident, merged)
            count_children(node)
        elif args.include_locals and SyntaxConfig.is_local(node) and node.children:
            # local variables
            ident = node.children[0].data
            incr_ident(ident, local_defs)
            incr_ident(ident, merged)
            count_children(node)
        elif args.include_constructor_names and SyntaxConfig.is_constructor(node) and node.children:
            # constructors
            child = node.children.pop()
            if SyntaxConfig.is_ident(child) and child.children:
                ident = child.children[0].data
                incr_ident(ident, constructor_names)
                incr_ident(ident, merged)
            count_children(node)
        else:
            # recurse
            count_children(node)

    count_in_goal(goal_ast)

def dump(dirname, filename, idents):
    names_file = open(os.path.join(dirname, filename), 'wb')
    pickle.dump(idents, names_file)
    names_file.close()

def dump_idents(args, dirname):
    if not os.path.exists(dirname):
        os.makedirs(dirname)

    if args.include_defs:
        dump(dirname, 'names.pickle', defs)

    if args.include_locals:
        dump(dirname, 'locals.pickle', local_defs)

    if args.include_constructor_names:
        dump(dirname, 'constructors.pickle', constructor_names)

    if args.include_paths:
        dump(dirname, 'paths.pickle', paths)

    dump(dirname, 'merged.pickle', merged)

    print('output saved to ', dirname)

if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser(description='Count occurrences of named datatypes and constants in the data')
    arg_parser.add_argument('--data_root', type=str, default='../data',
                                help='The folder for CoqGym')
    arg_parser.add_argument('--coq_projects', type=str, default='../coq_projects',
                                help='The folder for the coq projects')
    arg_parser.add_argument('--output', type=str, default='./names/',
                                help='The output file')
    arg_parser.add_argument('--no_defs', action='store_false', dest='include_defs', help='do not include the names of definitions and theorems in the model')
    arg_parser.add_argument('--no_locals', action='store_false', dest='include_locals', help='do not include the names of local variables in the model')
    arg_parser.add_argument('--no_constructors', action='store_false', dest='include_constructor_names', help='do not include constructor names in the model')
    arg_parser.add_argument('--no_paths', action='store_false', dest='include_paths', help='do not include the paths of definitions and theorems in the model')
    arg_parser.add_argument('--paths_in_defs', action='store_true', help='include path components in the global definitions vocabulary')
    args = arg_parser.parse_args()
    print(args)
    
    syn_conf = SyntaxConfig(args.include_locals, args.include_defs, args.include_paths, args.include_constructor_names)
    term_parser = GallinaTermParser(args.coq_projects, syn_conf, caching=True)

    iter_proofs(args.data_root, functools.partial(count, args, term_parser), include_synthetic=False, show_progress=True, proj_callback=term_parser.load_project)

    dump_idents(args, args.output)

