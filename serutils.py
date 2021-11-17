import os.path
import re
from lark import Token
from pathlib import Path
from serapi import SerAPI
from syntax import SyntaxConfig
from utils import log

CONSTRUCTOR_NONTERMINALS = {
    'constructor_construct': '(Construct ({} {}))',
    'constructor_ulevel': '(ULevel {})',
    'names__label__t': '{}',
    'names__constructor': '({} {})',
    'names__inductive': '({} {})',
    'constructor_mutind': '(Mutind {} {} {})',
    'constructor_mpfile': '(MPfile {})',
    'constructor_mpbound': '(MPbound {})',
    'constructor_mpdot': '(MPdot {} {})',
    'constructor_mbid': '(Mbid (Id {}) {})'
}


def unparse(node):
    """
    takes a tree and converts it back to a string representation of an s-expression, to be fed
    into serapi
    """
    if isinstance(node, Token):
        return node.value
    elif node.data == 'int':
        return node.children[0].value
    elif node.data == 'names__id__t':
        return '(Id {})'.format(node.children[0].data)
    elif node.data == 'constructor_dirpath':
        s_expr_path = ' '.join(map(unparse, node.children))
        return '(DirPath ({}))'.format(s_expr_path)
    elif node.data == 'constructor_instance':
        return '(Instance ({}))'.format(' '.join(map(unparse, node.children)))
    else:
        return CONSTRUCTOR_NONTERMINALS[node.data].format(*map(unparse, node.children))


class SerAPIWrapper:
    def __init__(self, coq_projects_path, timeout=6):
        self.timeout = timeout
        self.serapi = SerAPI(timeout)
        self.coq_projects_path = os.path.abspath(coq_projects_path)
        self.added_paths = {'SerTop'}

    def load_project(self, project_name):
        project = Path(self.coq_projects_path, project_name)
        coq_project_files = set(project.glob('**/_CoqProject'))
        make_files = set(project.glob('**/Make'))
        config_files = coq_project_files.union(make_files)
        for config_file in config_files:
            self.exec_includes(config_file)

    # based on code from https://github.com/HazardousPeach/coq_serapy/
    def exec_includes(self, config_file):
        with open(str(config_file)) as f:
            config = f.read()
        for lib_match in re.finditer(r'-[RQ]\s*(\S*)\s*(\S*)\s*', config):
            path_suffix, name = lib_match.groups()
            if name == '""':
                name = config_file.parent.name
            path = os.path.join(config_file.parent, path_suffix)
            self.serapi.send_add('Add Rec LoadPath "{}" as {}.'.format(path, name), False)
        for ml_match in re.finditer(r'-I\s*(\S*)', config):
            path = os.path.join(config_file.parent, ml_match.group(1))
            self.serapi.send_add('Add ML Path "{}".'.format(path), False)

    def get_constr_name(self, construct_node):
        unparsed = unparse(construct_node)
        dir_path = next(construct_node.find_data('constructor_dirpath'))
        path = '.'.join(child.children[0].data for child in reversed(dir_path.children))
        if path not in self.added_paths:
            self.added_paths.add(path)
            cmd = 'Require {}.'.format(path)
            try:
                self.serapi.send_add(cmd, False)
            except Exception as e:
                print('failed to import path {}'.format(path))
                print('error: {}\n'.format(e))
                print('original command: {}'.format('"{}"'.format(cmd)))
        try:
            name = self.serapi.print_constr(unparsed)
        except Exception as e:
            print('print_constr failed for sexpr {}'.format(unparsed))
            print('error: {}\n'.format(e))
            return
        if name and name.startswith('@'):
            name = name[1:]
        return name
