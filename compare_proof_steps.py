#!/usr/bin/env python3

import argparse
import glob
import os.path
import json
import multiprocessing
from pathlib import Path
from tqdm import tqdm

parser = argparse.ArgumentParser()
parser.add_argument("stepsdir_a")
parser.add_argument("stepsdir_b")
parser.add_argument("-j", "--num-threads", default=4)
args = parser.parse_args()

def check_file(filename) -> None:
    parts = Path(filename).parts
    i = parts.index(Path(args.stepsdir_a).parts[-1])
    localpath = os.path.join(*parts[i + 1:])
    steps_a_dict = {}
    with open(filename, 'r') as fa:
        for line in fa:
            step = json.loads(line)
            steps_a_dict[(step['proof_name'], step['n_step'])] = step
    with open(os.path.join(args.stepsdir_b, localpath), 'r') as fb:
        for line in fb:
            step = json.loads(line)
            matching_step = steps_a_dict[(step['proof_name'], step['n_step'])] 
            assert matching_step == step, (matching_step, step)

with multiprocessing.Pool(args.num_threads) as pool:
    files = glob.glob(os.path.join(args.stepsdir_a, "**/*.json"))
    res = list(tqdm(pool.imap(check_file, files),
                    desc="Checking files",
                    total=len(files)))

# steps_a = [json.load(open(f, 'rb')) for f in
#            tqdm(glob.glob(os.path.join(args.stepsdir_a, "train/*")) +
#                 glob.glob(os.path.join(args.stepsdir_a, "valid/*")),
#                 desc=f"Loading steps from {args.stepsdir_a}")]
# steps_b = [json.load(open(f, 'rb')) for f in
#            tqdm(glob.glob(os.path.join(args.stepsdir_b, "train/*")) +
#                 glob.glob(os.path.join(args.stepsdir_b, "valid/*")),
#                 desc=f"Loading steps from {args.stepsdir_b}")]
# steps_b_dict = {}
# for step in tqdm(steps_b, desc="Indexing steps"):
#     steps_b_dict[(step['file'], step['proof_name'], step['n_step'])] = step
# 
# for step in tqdm(steps_a, desc="Checking steps"):
#     matching_step = steps_b_dict[(step['file'], step['proof_name'], step['n_step'])] 
#     assert matching_step == step, (matching_step, step)
