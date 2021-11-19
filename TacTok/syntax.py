# Help dealing with syntax options, without clutter

from lark.tree import Tree

class SyntaxConfig:

    def __init__(self, include_locals=True, include_defs=True, include_paths=True,
                 include_constructor_names=True, merge_vocab=False):
        self.include_locals = include_locals
        self.include_defs = include_defs
        self.include_paths = include_paths
        self.include_constructor_names = include_constructor_names
        self.merge_vocab = merge_vocab

    # The node is an identifier
    @staticmethod
    def is_ident(node):
        return (node.data == 'names__id__t')

    # The node is a variable
    @staticmethod
    def is_var(node):
        return (node.data == 'constructor_var')

    # The node is a name
    @staticmethod
    def is_name(node):
        return (node.data == 'constructor_name')
    
    # The node is a local variable (for now, whenever it is a variable or a name)
    @staticmethod
    def is_local(node):
        return SyntaxConfig.is_var(node) or SyntaxConfig.is_name(node)

    # The node is a path
    @staticmethod
    def is_path(node):
        return (node.data == 'constructor_dirpath')

    # The node is a label
    @staticmethod
    def is_label(node):
        return (node.data == 'names__label__t')

    # The node is a constructor
    @staticmethod
    def is_constructor(node):
        return (node.data == 'constructor_construct')

    # Make a new value as a nonterminal with an empty list of terminals
    @staticmethod
    def nonterminal_value(value):
        value_tree = Tree(value, [])
        value_tree.height = 0
        return value_tree

    # Make a new ident
    @staticmethod
    def singleton_ident(value):
        value_tree = SyntaxConfig.nonterminal_value(value)
        ident_wrapper = Tree('names__id__t', [value_tree])
        ident_wrapper.height = 1
        return ident_wrapper
