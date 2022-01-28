#!/usr/bin/env python3

import argparse
import glob
import os.path
import os
import pickle
import multiprocessing
import json
import functools 
from pathlib import Path
from tqdm import tqdm
import fcntl
import time
from lark import Tree

class LarkEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Tree):
            return {"__is_tree__": True,
                    "data": obj.data,
                    "children": [self.default(child) for child in obj.children]}
        return json.JSONEncoder.default(self, obj) 

class FileLock:
    def __init__(self, file_handle):
        self.file_handle = file_handle

    def __enter__(self):
        while True:
            try:
                fcntl.flock(self.file_handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except OSError:
               time.sleep(0.01)
        return self

    def __exit__(self, type, value, traceback):
        fcntl.flock(self.file_handle, fcntl.LOCK_UN)

def get_local_path(file):
    parts = Path(file).parts
    i = parts.index('data')
    return os.path.join(*parts[i + 1:])

def to_file(args: argparse.Namespace, filename: str) -> None:
    with open(filename, 'rb') as f:
        step = pickle.load(f)
    local_path = get_local_path(step['file'])
    outpath = os.path.join(args.outdir, local_path)
    os.makedirs(os.path.dirname(outpath), exist_ok=True)
    with open(outpath, 'a') as f, FileLock(f):
        print(json.dumps(step, cls=LarkEncoder), file=f)

parser = argparse.ArgumentParser()
parser.add_argument("stepsdir")
parser.add_argument("outdir")
parser.add_argument("-j", "--num-threads", default=4)
args = parser.parse_args()

with multiprocessing.Pool(args.num_threads) as pool:
    paths = glob.glob(os.path.join(args.stepsdir, "**/*"))
    res = list(tqdm(pool.imap(functools.partial(to_file, args), paths), total=len(paths)))
  
