#!/usr/bin/env python3

import argparse
from .evaluate-test-worker import show_progress

tt_dir = os.path.expandvars("$HOME/work/TacTok")

def main() -> None:
    argparser = argparse.ArgumentParser()
    argparser.add_argument("eval_id")
    argparser.add_argument("--num-workers", type=int, default=32)
    argparser.add_argument("--jobsfile", default="jobs.txt")
    argparser.add_argument("--takenfile", default="taken.txt")
    argparser.add_argument("--donefile", default="done.txt")
    argparser.add_argument("--crashedfile", default="crashed.txt")
    argparser.add_argument("--projs-split", default="projs_split.json")
    args, rest_args = argparser.parse_known_args()
    dest_dir = os.path.join(tt_dir, "TacTok/evaluation", args.eval_id)

    show_progress(args, dest_dir)

if __name__ == '__main__':
    main()
