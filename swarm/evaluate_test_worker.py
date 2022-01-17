#!/usr/bin/env python3

import argparse
import json
import subprocess
import os.path
import os
import shutil
import glob
import time
import sys
from tqdm import tqdm
from typing import List

tt_dir = os.path.expandvars("$HOME/work/TacTok")

def is_yes(response: str) -> bool:
    return response in ["yes", "Yes", "YES", "y", "Y"]

def main() -> None:
    argparser = argparse.ArgumentParser()
    argparser.add_argument("eval_id")
    argparser.add_argument("--mode", choices=["file", "proof"], default="file")
    argparser.add_argument("--num-workers", type=int, default=128)
    argparser.add_argument("--worker-timeout", default="4:00:00")
    argparser.add_argument("--jobsfile", default="jobs.txt")
    argparser.add_argument("--takenfile", default="taken.txt")
    argparser.add_argument("--donefile", default="done.txt")
    argparser.add_argument("--crashedfile", default="crashed.txt")
    argparser.add_argument("--projs-split", default="projs_split.json")
    args, rest_args = argparser.parse_known_args()

    dest_dir = os.path.join(tt_dir, "TacTok/evaluation", args.eval_id)
    if os.path.exists(dest_dir):
        response = input(f"Destination directory {dest_dir} exists. Remove it? [y/N] ")
        if is_yes(response):
             shutil.rmtree(dest_dir)
             setup_jobs(args, dest_dir)
        else:
             response = input(f"Continue from existing run? [y/N] ")
             reset_unfinished_jobs(args, dest_dir)
             possibly_expand_jobs(args, dest_dir)
             if not is_yes(response):
                 sys.exit(1)
    else:
        setup_jobs(args, dest_dir)
    dispatch_workers(args, rest_args)
    show_progress(args, dest_dir)

def verbose_json_loads(line_num: int, line: str):
    try:
        return json.loads(line)
    except json.decoder.JSONDecodeError:
        print(f"Error decoding json {line} at line {line_num}", file=sys.stderr)
        raise

def reset_unfinished_jobs(args: argparse.Namespace, dest_dir: str) -> None:
    with open(os.path.join(dest_dir, args.takenfile), 'r') as f:
         taken_jobs = [verbose_json_loads(line_num, line) for line_num, line in enumerate(f)]
    with open(os.path.join(dest_dir, args.donefile), 'r') as f:
         done_jobs = [json.loads(line) for line in f]
    finished_jobs = [job for job in taken_jobs if job in done_jobs]
    with open(os.path.join(dest_dir, args.takenfile), 'w') as f:
         for job in finished_jobs:
             print(json.dumps(job), file=f)

def possibly_expand_jobs(args: argparse.Namespace, dest_dir: str) -> None:
    if args.mode == "file":
        return
    with open(os.path.join(dest_dir, args.jobsfile), 'r') as f:
        existing_jobs = [json.loads(line) for line in f]
    with open(os.path.join(dest_dir, args.donefile), 'r') as f:
        done_jobs = [json.loads(line) for line in f]
    with open(os.path.join(tt_dir, args.projs_split), 'r') as f:
        projs_split = json.load(f)
    with open(os.path.join(dest_dir, args.jobsfile), 'w') as f:
        for job in existing_jobs:
            if len(job) == 3 or job in done_jobs:
                print(json.dumps(job), file=f)
                continue
            assert len(job) == 2
            proj_idx, file_idx = job
            proj_name = projs_split['projs_test'][proj_idx]
            result = subprocess.run(["python3",
                                     f"{tt_dir}/print_proof_names.py",
                                     "--proj", proj_name,
                                     "--file_idx", str(file_idx)], text=True, stdout=subprocess.PIPE)
            for proof_name in result.stdout.splitlines():
                print(json.dumps([proj_idx, file_idx, proof_name]), file=f)
    pass

def setup_jobs(args: argparse.Namespace, dest_dir: str) -> None:
    subprocess.run([f"{tt_dir}/swarm/save-run.sh", args.eval_id] + sys.argv[1:])
    with open(os.path.join(tt_dir, args.projs_split), 'r') as f:
        projs_split = json.load(f)
    with open(os.path.join(dest_dir, args.jobsfile), 'w') as f:
        for proj_idx, proj_name in enumerate(projs_split["projs_test"]):
            num_files = len(glob.glob(f"{tt_dir}/data/{proj_name}/**/*.json", recursive=True))
            for file_idx in range(num_files):
                if args.mode == "file":
                    print(json.dumps([proj_idx, file_idx]), file=f)
                else:
                    result = subprocess.run(["python",
                                             f"{tt_dir}/print_proof_names.py",
                                             "--proj", proj_name,
                                             "--file_idx", str(file_idx)], text=True, stdout=subprocess.PIPE)
                    for proof_name in result.stdout:
                        print(json.dumps([proj_idx, file_idx, proof_name]), file=f)

def dispatch_workers(args: argparse.Namespace, rest_args: List[str]) -> None:
    os.makedirs(f"{tt_dir}/output/workers/", exist_ok=True)
    dest_dir = os.path.join(tt_dir, "TacTok/evaluation", args.eval_id)
    with open(os.path.join(dest_dir, "num_workers_dispatched.txt"), 'w') as f:
        print(args.num_workers, file=f)
    with open(os.path.join(dest_dir, "workers_scheduled.txt"), 'w') as f:
        pass
    with open(os.path.join(dest_dir, "taken.txt"), 'w') as f:
        pass
    subprocess.run([f"{tt_dir}/swarm/sbatch-retry.sh",
                    "-J", f"{args.eval_id}-worker",
                    "-p", "defq",
                    "-t", args.worker_timeout,
                    f"--output={tt_dir}/output/workers/worker-%a.out",
                    f"--array=0-{args.num_workers-1}",
                    f"{tt_dir}/swarm/evaluation-worker.py",
                    args.eval_id] + rest_args)

def get_done_jobs(args: argparse.Namespace, dest_dir: str) -> int:
    donepath = os.path.join(dest_dir, args.donefile)
    crashpath = os.path.join(dest_dir, args.crashedfile)
    if os.path.exists(donepath):
        with open(donepath, 'r') as f:
            num_successful_jobs = len(set([line for line in f]))
    else:
        num_successful_jobs = 0
    if os.path.exists(crashpath):
        with open(crashpath, 'r') as f:
            num_crashed_jobs = len([line for line in f])
    else:
        num_crashed_jobs = 0
    return num_successful_jobs + num_crashed_jobs

def get_workers_scheduled(dest_dir: str) -> int:
    try:
        with open(os.path.join(dest_dir, "workers_scheduled.txt"), 'r') as f:
            return len([line for line in f])
    except FileNotFoundError:
        return 0

def show_progress(args: argparse.Namespace, dest_dir: str) -> None:
    with open(os.path.join(dest_dir, args.jobsfile), 'r') as f:
         num_jobs_total = len([line for line in f])
    done_jobs = get_done_jobs(args, dest_dir)
    workers_scheduled = get_workers_scheduled(dest_dir)
    with open(os.path.join(dest_dir, "num_workers_dispatched.txt"), 'r') as f:
        num_workers_total = int(f.read())
    with tqdm(desc="Jobs finished",
              total=num_jobs_total, initial=done_jobs, dynamic_ncols=True) as bar, \
         tqdm(desc="Workers scheduled",
              total=num_workers_total, initial=workers_scheduled, dynamic_ncols=True) as wbar:
        while done_jobs < num_jobs_total:
            new_done_jobs = get_done_jobs(args, dest_dir)
            # if new_done_jobs > done_jobs:
            bar.update(new_done_jobs - done_jobs)
            done_jobs = new_done_jobs
            new_workers_scheduled = get_workers_scheduled(dest_dir)
            # if new_workers_scheduled > workers_scheduled:
            wbar.update(new_workers_scheduled - workers_scheduled)
            workers_scheduled = new_workers_scheduled
            time.sleep(0.1)

if __name__ == '__main__':
    main()
