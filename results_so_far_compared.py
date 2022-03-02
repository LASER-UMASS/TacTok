#!/usr/bin/env python3
import json
import argparse
import os.path
import re
from compare_results import get_results, get_succ_ratio
from glob import glob
from typing import Dict, Tuple

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
