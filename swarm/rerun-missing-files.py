#!/usr/bin/env python3

import subprocess
import argparse
import csv
import sys
from os.path import expandvars
from typing import List, Dict

parser = argparse.ArgumentParser()
parser.add_argument("eval_id")
args, rest_args = parser.parse_known_args()
tt_dir = expandvars("$HOME/work/TacTok")

def submit_array(proj_idx: int, file_idxs: List[int]):
    result = subprocess.run([f"{tt_dir}/swarm/sbatch-retry.sh",
                             "-J", f"{args.eval_id}-evaluate-file",
                             "-p", "defq",
                             "--comment", f"{proj_idx}",
                             f"--output={tt_dir}/output/evaluate/{args.eval_id}/evaluate_proj_{proj_idx}_%a.out",
                             f"--array={','.join(file_idxs)}",
                             f"{tt_dir}/swarm/evaluate-proj-array-item.sbatch",
                             args.eval_id, proj_idx] + rest_args)

result = subprocess.Popen([f"{tt_dir}/swarm/find-missing-outputs-csv.sh",
                           f"{tt_dir}/TacTok/evaluation/{args.eval_id}"],
                          stdout=subprocess.PIPE, text=True)

csvreader = csv.reader(result.stdout)
proj_files: Dict[int, List[int]] = {}
last_proj_idx = None
files_submitted = 0
for row in csvreader:
    proj_idx, proj_name, file_idx, file_name, proof_idx, proof_name = row
    if proof_idx != "":
        continue
    if last_proj_idx and proj_idx != last_proj_idx:
        submit_array(last_proj_idx, proj_files[last_proj_idx])
        files_submitted += len(proj_files[last_proj_idx])
    last_proj_idx = proj_idx
    if proj_idx not in proj_files:
        proj_files[proj_idx] = []
    proj_files[proj_idx].append(file_idx)

if last_proj_idx:
    submit_array(last_proj_idx, proj_files[last_proj_idx])
    files_submitted += len(proj_files[last_proj_idx])
print(f"Submitted {files_submitted} files")
