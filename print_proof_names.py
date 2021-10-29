import argparse
import functools
import os
import json
from glob import glob
from utils import iter_proofs, iter_proofs_in_file

def print_proof(args: argparse.Namespace, filename: str, proof_data) -> None:
    print(proof_data['name'])

if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser(description='Print the names of all proofs')
    arg_parser.add_argument('--data_root', type=str, default='data',
                                help='The folder for CoqGym')
    arg_parser.add_argument('--proj', type=str)
    arg_parser.add_argument('--file_idx', type=int)
    args = arg_parser.parse_args()

    assert os.path.exists(args.data_root), f"Couldn't find a directory at {args.data_root}"

    if args.proj is not None:
        proof_root = args.data_root + "/" + args.proj
    else:
        proof_root = args.data_root

    if args.file_idx is not None:
        all_files = glob(os.path.join(proof_root, '**/*.json'), recursive=True)
        target_file = all_files[args.file_idx]
        iter_proofs_in_file(functools.partial(print_proof, args),
                            target_file, json.load(open(target_file)))
    else:
        iter_proofs(proof_root, functools.partial(print_proof, args),
                    include_synthetic=False, show_progress=False)
