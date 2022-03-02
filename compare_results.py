#!/usr/bin/env python3
import json
import argparse
import os.path
import re
from pathlib import Path
from glob import glob
from typing import Dict, Tuple

def main() -> None:
  parser = argparse.ArgumentParser()
  parser.add_argument("results_a")
  parser.add_argument("results_b")
  parser.add_argument("-v", "--verbose", action="count", default=0)
  parser.add_argument("--no-skip-15", action="store_false", dest="skip_15")
  args = parser.parse_args()
  results_a = get_results(args, args.results_a)
  results_b = get_results(args, args.results_b)

  succ_ratio_a = get_succ_ratio(results_a)
  succ_ratio_b = get_succ_ratio(results_b)

  print(f"{succ_ratio_a*100:.2f}% vs {succ_ratio_b*100:.2f}%")
  successful_a = [proof for proof, succ in results_a.items() if succ]
  successful_b = [proof for proof, succ in results_b.items() if succ]
  a_but_not_b = [proof for proof in successful_a if proof not in successful_b]
  b_but_not_a = [proof for proof in successful_b if proof not in successful_a]
  print(f"First result proved {len(a_but_not_b)} proofs that second result didn't")
  print(f"Second results proved {len(b_but_not_a)} proofs that first result didn't")

  if args.verbose >= 1:
    print(f"Projects where first result proved things second result didn't:")
    print(sorted(list({get_proj(filename) for filename, proofname in a_but_not_b})))
    print(f"Projects where second result proved things first result didn't:")
    print(sorted(list({get_proj(filename) for filename, proofname in b_but_not_a})))
  if args.verbose >= 2:
    print(f"Files where first result proved things second result didn't:")
    for filename in {filename for filename, proofname in a_but_not_b}:
        print(filename)
    print(f"Files where second result proved things first result didn't:")
    for filename in {filename for filename, proofname in b_but_not_a}:
        print(filename)
  

def get_results(args: argparse.Namespace, results_dir: str) -> Dict[Tuple[str, str], bool]:
  results_dict = {}
  result_files = glob(os.path.join(results_dir, "results*.json"))
  for result_file in result_files:
    if re.match(".*results_15_.*\.json", result_file) and args.skip_15:
        continue
    with open(result_file, "rb") as f:
      try:
        results = json.load(f)["results"]
      except json.decoder.JSONDecodeError:
        print(f"Failed to decode file {f}")
        raise
      for result in results:
        results_dict[(result["filename"],result["proof_name"])] = result["success"]
  return results_dict

def get_succ_ratio(results_dict: Dict[Tuple[str, str], bool]) -> float:
  num_total = len(results_dict)
  num_successful = len([success for _, success in results_dict.items() if success])
  return num_successful / num_total

def get_proj(filename):
    parts = Path(filename).parts
    i = parts.index('data')
    return parts[i+1]

if __name__ == '__main__':
  main()
