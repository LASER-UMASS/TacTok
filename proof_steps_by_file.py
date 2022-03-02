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
from typing import Any, Dict, List
from hashlib import sha256

class LarkEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Tree):
            return {"__is_tree__": True,
                    "data": obj.data,
                    "children": [self.default(child) for child in obj.children]}
        return json.JSONEncoder.default(self, obj) 

def lark_decoder(dct):
     if "__is_tree__" in dct:
         return Tree(dct["data"], dct["children"])
     return dct

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

def get_local_path(filename):
    parts = Path(filename).parts
    i = parts.index('data')
    return os.path.join(*parts[i + 1:])

def get_proj(filename):
    parts = Path(filename).parts
    i = parts.index('data')
    return parts[i+1]

def to_file(args: argparse.Namespace, filename: str) -> None:
    with open(filename, 'rb') as f:
        step = pickle.load(f)
    local_path = get_local_path(step['file'])
    outpath = os.path.join(args.outdir, local_path)
    os.makedirs(os.path.dirname(outpath), exist_ok=True)
    with open(outpath, 'a') as f, FileLock(f):
        print(json.dumps(step, cls=LarkEncoder), file=f)

def to_hashes(args: argparse.Namespace, projs_split: Dict[str, List[str]], filename: str) -> None:
    with open(filename, 'r') as f:
        for line in f:
            step = json.loads(line, object_hook=lark_decoder)
            step_hash = sha256(repr(step).encode('utf-8')).hexdigest()
            if get_proj(step["file"]) in projs_split["projs_train"]:
                outpath = os.path.join(args.outdir, "train", f"{stephash}.pickle")
            else:
                assert get_proj(step["file"]) in projs_split("projs_valid"), get_proj(step["file"])
                outpath = os.path.join(args.outdir, "valid", f"{stephash}.pickle")

            os.makedirs(os.path.dirname(outpath), exist_ok=True)
            with open(outpath, 'w') as f:
                pickle.dump(step, outpath)

parser = argparse.ArgumentParser()
parser.add_argument("indir")
parser.add_argument("outdir")
parser.add_argument("-j", "--num-threads", default=4)
parser.add_argument("--to-hashes", action="store_true")
parser.add_argument("--projs_split", default="projs_split.json")
args = parser.parse_args()

with multiprocessing.Pool(args.num_threads) as pool:
    if args.to_hashes:
        paths = glob.glob(os.path.join(args.indir, "**/*.json"), recursive=True)
        projs_split = json.load(open(args.projs_split))
        res = list(tqdm(pool.imap(functools.partial(to_hashes, args, projs_split), paths), 
                        total=len(paths)))
    else:
        paths = glob.glob(os.path.join(args.indir, "**/*.pickle"), recursive=True)
        res = list(tqdm(pool.imap(functools.partial(to_file, args), paths), total=len(paths)))
  
