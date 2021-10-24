from serapi import SerAPI


CONSTRUCTOR_NONTERMINALS = {
    'constructor_construct': '(Construct ({} {}))',
    'constructor_ulevel':  '(ULevel {})',
    'names__label__t': '{}',
    'names__constructor': '({} {})',
    'names__inductive': '({} {})',
    'constructor_mutind': '(Mutind {} {} {})',
    'constructor_mpfile': '(MPfile {})',
    'constructor_mpbound': '(MPbound {})',
    'constructor_mpdot': '(MPdot {} {})',
    'constructor_mbid': '(Mbid {} {})'
}


def unparse(node):
    """
    takes a tree and converts it back to a string representation of an s-expression, to be fed
    into serapi
    """
    if node.data == 'int':
        return node.children[0].value
    elif node.data == 'names__id__t':
        return '(Id {})'.format(node.children[0].data)
    elif node.data == 'constructor_dirpath':
        s_expr_path = ' '.join(map(unparse, node.children))
        # if node.children and node.children[-1].children:
        #     coq_path = '.'.join(node.children[-1].children) + '.'
        #     # builtin
        #     if node.children[-1].children[0].data == "Coq":
        #         self.loaded_builtins

        return '(DirPath ({}))'.format(s_expr_path)
    elif node.data == 'constructor_instance':
        return '(Instance ({}))'.format(' '.join(map(unparse, node.children)))
    else:
        return CONSTRUCTOR_NONTERMINALS[node.data].format(*map(unparse, node.children))
