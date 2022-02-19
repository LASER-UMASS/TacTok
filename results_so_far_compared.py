import json
import argparse
import os.path
import re
from glob import glob
from typing import Dict, Tuple

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

def main() -> None:
  parser = argparse.ArgumentParser()
  parser.add_argument("results_dir")
  parser.add_argument("reference_results_dir")
  parser.add_argument("-q", "--quiet", action="store_true")
  parser.add_argument("--no-skip-15", action="store_false", dest="skip_15")
  args = parser.parse_args()
  results = get_results(args, args.results_dir)
  ref_results = get_results(args, args.reference_results_dir)
  ref_results_matching = {}
  for key in results:
    if key not in ref_results:
      if not args.quiet:
        print(f"Warning: ref results missing {key}")
      continue
    ref_results_matching[key] = ref_results[key]
  ref_succ_ratio = get_succ_ratio(ref_results_matching)
  result_succ_ratio = get_succ_ratio({key: success for key, success in results.items() if key in ref_results})
  print((f"{(result_succ_ratio - ref_succ_ratio)*100:+.2f} "
         f"({result_succ_ratio*100:.2f}% vs {ref_succ_ratio*100:.2f}%)"))


if __name__ == '__main__':
  main()
