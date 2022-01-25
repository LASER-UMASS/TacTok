import os
import json
import pickle
from hashlib import sha256
from tac_grammar import CFG, TreeBuilder, NonterminalNode, TerminalNode
import sys
sys.setrecursionlimit(100000)
sys.path.append(os.path.normpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../')))
from functools import partial
from syntax import SyntaxConfig
from gallina import GallinaTermParser
from lark.exceptions import UnexpectedCharacters, ParseError
from utils import iter_proofs, iter_file_proofs, SexpCache, get_proj
from args import ConfigParser
import argparse
from hashlib import md5
from agent import filter_env

sexp_cache = SexpCache('../sexp_cache', readonly=True)

def parse_goal(term_parser, g):
    goal = {'id': g['id'], 'text': g['type'], 'ast': term_parser.parse(sexp_cache[g['sexp']])}
    local_context = []
    for i, h in enumerate(g['hypotheses']):
        for ident in h['idents']:
            local_context.append({'ident': ident, 'text': h['type'], 'ast': term_parser.parse(sexp_cache[h['sexp']])})
    return local_context, goal


grammar = CFG('tactics.ebnf', 'tactic_expr')
tree_builder = TreeBuilder(grammar)

def tactic2actions(tac_str):
    tree = tree_builder.transform(grammar.parser.parse(tac_str))
    assert tac_str.replace(' ', '') == tree.to_tokens().replace(' ', '')
    actions = []
    def gather_actions(node):
        if isinstance(node, NonterminalNode):
            actions.append(grammar.production_rules.index(node.action))
        else:
            assert isinstance(node, TerminalNode)
            actions.append(node.token)
    tree.traverse_pre(gather_actions)
    return actions

projs_split = json.load(open('../projs_split.json'))
proof_steps = {'train': [], 'valid': [], 'test': []}

num_discarded = 0
num_no_parse = 0
num_empty_goal = 0

def process_proof(term_parser, filename, proof_data):
    if 'entry_cmds' in proof_data:
        is_synthetic = True
    else:
        is_synthetic = False
    global num_discarded
    global num_no_parse
    global num_empty_goal

    if args.filter and not md5(filename.encode()).hexdigest().startswith(args.filter):
        return

    proj = get_proj(filename)
    if proj in projs_split['projs_train']:
        split = 'train'
    elif proj in projs_split['projs_valid']:
        split = 'valid'
        if is_synthetic:
            return
    else:
        split = 'test'
        if is_synthetic:
            return

    for i, step in enumerate(proof_data['steps']):
        # consider only tactics
        if step['command'][1] in ['VernacEndProof', 'VernacBullet', 'VernacSubproof', 'VernacEndSubproof']:
            continue
        assert step['command'][1] == 'VernacExtend'
        assert step['command'][0].endswith('.')
        # environment
        env = filter_env(term_parser, proof_data['env'])
        # local context & goal
        if step['goal_ids']['fg'] == []:
            num_discarded += 1
            num_empty_goal += 1
            continue
        goal_id = step['goal_ids']['fg'][0]
        local_context, goal = parse_goal(term_parser, proof_data['goals'][str(goal_id)])
        # tactic
        tac_str = step['command'][0][:-1]
        try:
            actions = tactic2actions(tac_str)
        except (UnexpectedCharacters, ParseError) as ex:
            num_discarded += 1
            num_no_parse += 1
            continue
        proof_steps[split].append({'file': filename, 
                                   'proof_name': proof_data['name'],
                                   'n_step': i,
                                   'env': env,
                                   'local_context': local_context, 
                                   'goal': goal,
                                   'tactic': {'text': tac_str, 'actions': actions},})
        if is_synthetic:
            proof_steps[split][-1]['is_synthetic'] = True
            proof_steps[split][-1]['goal_id'] = proof_data['goal_id']
            proof_steps[split][-1]['length'] = proof_data['length']
        else:
            proof_steps[split][-1]['is_synthetic'] = False
       

if __name__ == '__main__':
    arg_parser = ConfigParser(description='Extract the proof steps from CoqGym for trainig ASTactic via supervised learning')
    arg_parser.add_argument('--no_defs', action='store_false', dest='include_defs', help='do not include the names of definitions and theorems in the model')
    arg_parser.add_argument('--no_locals', action='store_false', dest='include_locals', help='do not include the names of local variables in the model')
    arg_parser.add_argument('--no_constructors', action='store_false', dest='include_constructor_names',
                        help='do not include constructor names in the model')
    arg_parser.add_argument('--no_paths', action='store_false', dest='include_paths', help='do not include the paths of definitions and theorems in the model')
    arg_parser.add_argument('--data_root', type=str, default='../data',
                                help='The folder for CoqGym')
    arg_parser.add_argument('--file', type=str, default=None,
                            help='The file to extract')
    arg_parser.add_argument('--coq_projects', type=str, default='../coq_projects',
                                help='The folder for the coq projects')
    arg_parser.add_argument('--output', type=str, default='./proof_steps/',
                                help='The output file')
    arg_parser.add_argument('--filter', type=str, help='filter the proofs')
    args = arg_parser.parse_args()
    print(args)
    
    syn_conf = SyntaxConfig(args.include_locals, args.include_defs, args.include_paths, args.include_constructor_names)
    term_parser = GallinaTermParser(args.coq_projects, syn_conf, caching=True, use_serapi=True)

    if args.file:
        iter_file_proofs(args.file, partial(process_proof, term_parser), include_synthetic=False,
                         proj_callback=term_parser.load_project)
    else:
        iter_proofs(args.data_root, partial(process_proof, term_parser), include_synthetic=False,
                    show_progress=True, proj_callback=term_parser.load_project)
    print(f"{num_empty_goal} proof steps discarded because of an empty goal")
    print(f"{num_no_parse} proof steps discarded because of parsing issues")
    print(f"{num_discarded} proof steps discarded total")

    for split in ['train', 'valid']:
        for step in proof_steps[split]:
            dirname = os.path.join(args.output, split)
            if not os.path.exists(dirname):
                os.makedirs(dirname)
            step_hash = sha256(repr(step).encode('utf-8')).hexdigest()
            if args.filter:
                outpath = os.path.join(dirname, f"{args.filter}-{step_hash}.pickle")
            else:
                outpath = os.path.join(dirname, f"{step_hash}.pickle")
            if os.path.exists(outpath):
                print("WARNING: step file already exists with hash {step_hash}, overwriting...", file=sys.stderr)
            pickle.dump(step, open(outpath, 'wb'))

    print('output saved to ', args.output)
