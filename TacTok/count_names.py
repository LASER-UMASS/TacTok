import os
import json
import sys
sys.setrecursionlimit(100000)
sys.path.append(os.path.normpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../')))
from gallina import GallinaTermParser, traverse_postorder
from lark.exceptions import UnexpectedCharacters, ParseError
import argparse
from utils import iter_proofs, SexpCache
from lark.tree import Tree

# Count occurrences of named datatypes and constants in the training data.
# Based heavily on extract_proof_steps for the boilerplate.

projs_split = json.load(open('../projs_split.json'))

# For now we are naive and lump everything into one bucket,
# whether it's the name of a module, datatype, or constant.
# The AST orders these meaningfully, so hopefully the model reflects the meaning in the end.
# If not, there are simple changes we can make later to reflect that.
idents = {}

term_parser = GallinaTermParser(caching=True)
sexp_cache = SexpCache('../sexp_cache', readonly=True)

def parse_goal(g):
    return term_parser.parse(sexp_cache[g['sexp']])

def incr_ident(ident):
    if ident not in idents:
        idents[ident] = 1
    else:
        idents[ident] += 1

def count(filename, proof_data):
    #TODO add back after testing
    #proj = filename.split(os.path.sep)[2]
    #if not proj in projs_split['projs_train']:
        #return

    proof_start = proof_data['steps'][0]
    goal_id = proof_start['goal_ids']['fg'][0]
    goal_ast = parse_goal(proof_data['goals'][str(goal_id)])

    # count occurrences within a goal
    def count_in_goal(node):
        if node.data == 'constructor_mutind' or node.data == 'constructor_constant':
            dirpath = node.children[0].children[0]
            for c in dirpath.children:
                ident = c.children[0].data
                incr_ident(ident)
            ident = node.children[2].children[0].children[0].data
            incr_ident(ident)
        else:
            children = []
            for c in node.children:
                if isinstance(c, Tree):
                    node.height = max(node.height, c.height + 1)
                    children.append(c)
            node.children = children

    traverse_postorder(goal_ast, count_in_goal)

if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser(description='Count occurrences of named datatypes and constants in the data')
    arg_parser.add_argument('--data_root', type=str, default='../data',
                                help='The folder for CoqGym')
    arg_parser.add_argument('--output', type=str, default='./names/',
                                help='The output file')
    args = arg_parser.parse_args()
    print(args)

    iter_proofs(args.data_root, count, include_synthetic=False, show_progress=True)

    print(idents)

    #for split in ['train', 'valid']:
        #for i, step in enumerate(proof_steps[split]):
            #dirname = os.path.join(args.output, split)
            #if not os.path.exists(dirname):
                #os.makedirs(dirname)
            #if args.filter:
                #pickle.dump(step, open(os.path.join(dirname, '%s-%08d.pickle' % (args.filter, i)), 'wb'))
            #else:
                #pickle.dump(step, open(os.path.join(dirname, '%08d.pickle' % i), 'wb'))

    #print('output saved to ', args.output)
