#!/usr/bin/env python3

import argparse
import json
import sys
import subprocess
import os.path
import fcntl
import time
from os import environ
from typing import List

tt_dir = os.path.expandvars("$HOME/work/TacTok")

def main():
    argparser = argparse.ArgumentParser()
    argparser.add_argument("eval_id")
    argparser.add_argument("--workerid", type=int, default=None)
    argparser.add_argument("--jobsfile", default="jobs.txt")
    argparser.add_argument("--takenfile", default="taken.txt")
    argparser.add_argument("--donefile", default="done.txt")
    argparser.add_argument("--crashedfile", default="crashed.txt")
    args, rest_args = argparser.parse_known_args()
    if args.workerid == None:
         if 'SLURM_ARRAY_TASK_ID' in environ:
             args.workerid = int(environ['SLURM_ARRAY_TASK_ID'])
         else:
             print("Must pass --worker option unless SLURM_ARRAY_TASK_ID is set; exiting...", 
                   sys.stderr)
             sys.exit(1)
    run_worker(args, rest_args)

def verbose_json_loads(line_num: int, line: str):
    try:
        return json.loads(line)
    except json.decoder.JSONDecodeError:
        print(f"Error decoding json {line} at line {line_num}", file=sys.stderr)
        raise

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

def run_worker(args: argparse.Namespace, rest_args: List[str]):
    dest_dir = os.path.join(tt_dir, "TacTok/evaluation/", args.eval_id)
    with open(os.path.join(dest_dir, "workers_scheduled.txt"), 'a') as f, FileLock(f):
        print(args.workerid, file=f)
    with open(os.path.join(dest_dir, args.jobsfile), 'r') as f, FileLock(f):
        all_jobs = [json.loads(line) for line in f]
    
    if os.path.exists(os.path.join(dest_dir, args.takenfile)):
        with open(os.path.join(dest_dir, args.takenfile), 'r+') as f, FileLock(f):
            taken_jobs = [verbose_json_loads(line_num, line) for line_num, line in enumerate(f)]
            remaining_jobs = [job for job in all_jobs if job not in taken_jobs]
            starting_job = remaining_jobs[args.workerid % len(remaining_jobs)]
            print(json.dumps(starting_job), file=f)
    else:
        with open(os.path.join(dest_dir, args.takenfile), 'a') as f, FileLock(f):
            remaining_jobs = all_jobs
            starting_job = rmaining_jobs[args.workerid % len(remaining_jobs)]
            print(json.dumps(starting_job), file=f)
    
    current_job = starting_job
    while len(remaining_jobs) > 0:
        success = run_job(args.eval_id, dest_dir, current_job, rest_args)
        if success:
            with open(os.path.join(dest_dir, args.donefile), 'a') as f, FileLock(f):
                print(json.dumps(current_job), file=f)
        else:
            with open(os.path.join(dest_dir, args.crashedfile), 'a') as f, FileLock(f):
                print(json.dumps(current_job), file=f)
        with open(os.path.join(dest_dir, args.takenfile), 'r+') as f, FileLock(f):
            taken_jobs = [verbose_json_loads(line_num, line) for line_num, line in enumerate(f)]
            remaining_jobs = [job for job in all_jobs if job not in taken_jobs]
            if len(remaining_jobs) > 0:
                current_job = remaining_jobs[0]
            print(json.dumps(starting_job), file=f)

def run_job(eval_id: str, dest_dir: str, job: List[str], rest_args: List[str]) -> bool:
    if len(job) == 3:
        proj_idx, file_idx, proof_name = job
        proof_args = ["--proof", proof_name]
        task_spec = f"{proj_idx}_{file_idx}_{proof_name}"
    else:
        proj_idx, file_idx = job
        proof_args = []
        task_spec = f"{proj_idx}_{file_idx}"
 
    command = [f"{tt_dir}/swarm/evaluate-proj.sh",
               eval_id,
               f"--proj_idx={proj_idx}",
               f"--file_idx={file_idx}"] + proof_args + rest_args
    print("Running: ", command, flush=True)

    log_dir = os.path.join(tt_dir, "output/evaluate", eval_id)
    os.makedirs(log_dir, exist_ok=True)
    with open(os.path.join(log_dir, f"evaluate_proj_{task_spec}.out"), 'w') as f:
        result = subprocess.run(command, stderr=subprocess.STDOUT, stdout=f)

    expected_out_file = os.path.join(dest_dir, f"results_{task_spec}.json")
    
    return os.path.exists(expected_out_file)

if __name__ == '__main__':
    main()
