#!/usr/bin/env python3

import argparse
import glob
import os.path
import json
import multiprocessing
import difflib
from pathlib import Path
from tqdm import tqdm
from lark import Tree

parser = argparse.ArgumentParser()
parser.add_argument("stepsdir_a")
parser.add_argument("stepsdir_b")
parser.add_argument("-j", "--num-threads", default=4, type=int)
parser.add_argument("-v", "--verbose", action="count", default=0)
args = parser.parse_args()

def lark_decoder(dct):
     if "__is_tree__" in dct:
         return Tree(dct["data"], dct["children"])
     return dct

def compare_context(context1, context2):
    for item1, item2 in zip(context1, context2):
        if item1 == item2:
            print(f"{item1['ident']} matches")
        else:
           if item1['ident'] != item2['ident']:
               print(f"Identifiers don't match: {item1['ident']} vs {item2['ident']}")
           if item1['text'] != item2['text']:
               print(f"Text of {item1['ident']} doesn't match: {item1['text']} vs {item2['text']}")
           else:
               print(f"AST for {item1['ident']} doesn't match")
               print(f"Text: {item1['text']}")
               diff = difflib.context_diff(item1["ast"]
                                           .pretty().splitlines(),
                                           item2["ast"]
                                           .pretty().splitlines())
               for line in diff:
                   print(line)

def check_file(filename) -> None:
    parts = Path(filename).parts
    i = parts.index(Path(args.stepsdir_a).parts[-1])
    localpath = os.path.join(*parts[i + 1:])
    steps_a_dict = {}
    with open(filename, 'r') as fa:
        for line in fa:
            step = json.loads(line, object_hook=lark_decoder)
            steps_a_dict[(step['proof_name'], step['n_step'])] = step
    with open(os.path.join(args.stepsdir_b, localpath), 'r') as fb:
        for line in fb:
            step = json.loads(line, object_hook=lark_decoder)
            matching_step = steps_a_dict[(step['proof_name'], step['n_step'])] 
            assert step.keys() == matching_step.keys(), (step.keys(), matching_step.keys())
            matches = True
            for key in step.keys():
                # Filenames may not always match for steps coming from
                # different installations, but the important parts of them do
                # by construction here.
                if key == 'file':
                    continue
                if step[key] != matching_step[key]:
                    if key == "goal":
                        if step["goal"]['text'] != matching_step["goal"]["text"]:
                            print("Goal text doesn't match")
                            if args.verbose > 0:
                                print(matching_step["goal"]["text"])
                                print("=====VS=====")
                                print(step["goal"]["text"])
                        elif step["goal"]["ast"] != matching_step["goal"]["ast"]:
                            print("Goal text matches, but ast doesn't")
                            if args.verbose > 0:
                                print(step["goal"]["text"])
                                diff = difflib.context_diff(matching_step["goal"]["ast"]
                                                            .pretty().splitlines(),
                                                            step["goal"]["ast"]
                                                            .pretty().splitlines())
                                for line in diff:
                                    print(line)
                        else:
                            print("Something about goals doesn't match!")
                    elif key == "local_context":
                        print(f"Key {key} doesn't match.")
                        compare_context(matching_step["local_context"], step["local_context"])
                    else:
                        print(f"Key {key} doesn't match: {matching_step[key]} vs {step[key]}")
                    matches = False
            if not matches:
                print(localpath, step['proof_name'], step['n_step'], step['tactic']['text'])

with multiprocessing.Pool(args.num_threads) as pool:
    files = glob.glob(os.path.join(args.stepsdir_a, "**/*.json"), recursive=True)
    res = list(tqdm(pool.imap(check_file, files),
                    desc="Checking files",
                    total=len(files)))
