import argparse
import json
import sys
import os
sys.path.append(os.path.sep.join(__file__.split(os.path.sep)[:-2]))
from utils import log


class ConfigParser(argparse.ArgumentParser):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_argument('--export_config', type=str, default=None)
        self.add_argument('--config', type=str, default=None)

    def parse_args(self, *args, **kwargs):
        opts = super().parse_args(*args, **kwargs)

        if opts.config is not None:
            with open(opts.config) as f:
                opts.__dict__.update(**json.load(f))

        if opts.export_config is not None:
            with open(opts.export_config, 'w') as f:
                opts_dict = vars(opts)
                opts_dict.pop('export_config')
                opts_dict.pop('config')
                json.dump(opts_dict, f, separators=(',\n', ':'))

        log(opts)

        return opts
