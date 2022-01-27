# Utilities for reconstructing Gallina terms from their serialized S-expressions in CoqGym
from io import StringIO
from vernac_types import Constr__constr
from lark import Lark, Transformer, Visitor, Discard
from lark.lexer import Token
from lark.tree import Tree
from serutils import SerAPIWrapper
import logging
logging.basicConfig(level=logging.DEBUG)
from collections import defaultdict
from syntax import SyntaxConfig
import re
import pdb
from utils import log


def traverse_postorder(node, callback, parent_info=None, get_parent_info=None):
    old_parent_info = parent_info
    if get_parent_info is not None:
        parent_info = get_parent_info(node, parent_info)
    for c in node.children:
        if isinstance(c, Tree):
            traverse_postorder(c, callback, parent_info, get_parent_info)
    if get_parent_info is not None:
        callback(node, old_parent_info)
    else:
        callback(node)


class GallinaTermParser:
    def __init__(self, coq_projects_path, syntax_config, caching=True, use_serapi=True):
        self.caching = caching
        self.syntax_config = syntax_config
        t = Constr__constr()
        self.grammar = t.to_ebnf(recursive=True) + '''
        %import common.STRING_INNER
        %import common.ESCAPED_STRING
        %import common.SIGNED_INT
        %import common.WS
        %ignore WS
        '''
        self.parser = Lark(StringIO(self.grammar), start='constr__constr', parser='lalr')
        if caching:
            self.cache = {}
        self.serapi = None
        if use_serapi:
            self.serapi = SerAPIWrapper(coq_projects_path, timeout=30)

    def load_project(self, proj):
        self.serapi.load_project(proj)

    def parse_no_cache(self, term_str):
        syn_conf = self.syntax_config
        ast = self.parser.parse(term_str)

        ast.quantified_idents = set()

        def get_quantified_idents(node):
            if node.data == 'constructor_prod' and node.children != [] and SyntaxConfig.is_name(node.children[0]):
                ident = node.children[0].children[0].value
                if ident.startswith('"') and ident.endswith('"'):
                    ident = ident[1:-1]
                ast.quantified_idents.add(ident)

        traverse_postorder(ast, get_quantified_idents)
        ast.quantified_idents = list(ast.quantified_idents)

        # Postprocess: compute height, remove some tokens, make identifiers explicit
        # Make everything nonterminal for compatibility
        def postprocess(node, is_construct_child):
            children = []
            node.height = 0
            for c in node.children:
                if isinstance(c, Tree):
                    node.height = max(node.height, c.height + 1)
                    children.append(c)
                # Don't erase fully-qualified definition & theorem names
                elif (((syn_conf.include_defs or is_construct_child) and SyntaxConfig.is_label(node)) or
                ((syn_conf.include_paths or is_construct_child) and SyntaxConfig.is_path(node)) or
                (syn_conf.merge_vocab and syn_conf.include_locals and SyntaxConfig.is_local(node))):
                    ident_wrapper = SyntaxConfig.singleton_ident(c.value)
                    node.height = 2
                    children.append(ident_wrapper)
                # Don't erase local variable names
                elif ((syn_conf.include_locals or is_construct_child) and SyntaxConfig.is_local(node)):
                    var_value = SyntaxConfig.nonterminal_value(c.value)
                    node.height = 1
                    children.append(var_value)
                elif is_construct_child:
                    children.append(c)

             # Recover constructor names
            if syn_conf.include_constructor_names and SyntaxConfig.is_constructor(node):
                constructor_name = self.serapi.get_constr_name(node)
                if not syn_conf.include_paths:
                    for path_node in node.find_data('constructor_dirpath'):
                        path_node.children = []
                if not syn_conf.include_defs:
                    def_node = next(node.find_data('names__label__t'))
                    def_node.children = []
                if constructor_name:
                    children.append(SyntaxConfig.singleton_ident(constructor_name))
            if SyntaxConfig.is_constructor(node):
                for parent in node.iter_subtrees():
                    parent.children = [c for c in parent.children if not isinstance(c, Token)]

            node.children = children

        def get_is_construct_child(node, is_construct_child):
            return is_construct_child or SyntaxConfig.is_constructor(node)

        traverse_postorder(ast, postprocess, False, get_is_construct_child)
        return ast


    def parse(self, term_str):
        if self.caching:
            if term_str not in self.cache:
                self.cache[term_str] = self.parse_no_cache(term_str)
            return self.cache[term_str]
        else:
            return self.parse_no_cache(term_str)


    def print_grammar(self):
        print(self.grammar)


class Counter(Visitor):

    def __init__(self):
        super().__init__()
        self.counts_nonterminal = defaultdict(int)
        self.counts_terminal = defaultdict(int)

    def __default__(self, tree):
         self.counts_nonterminal[tree.data] += 1
         for c in tree.children:
             if isinstance(c, Token):
                 self.counts_terminal[c.value] += 1


class TreeHeight(Transformer):

    def __default__(self, symbol, children, meta):
        return 1 + max([0 if isinstance(c, Token) else c for c in children] + [-1])


class TreeNumTokens(Transformer):

    def __default__(self, symbol, children, meta):
        return sum([1 if isinstance(c, Token) else c for c in children])
