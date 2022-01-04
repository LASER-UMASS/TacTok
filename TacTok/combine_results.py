# A script to combine TacTok results

# Call this with python combine_results.py --results_dir_list <dir strings separated by spaces>

# Where --results_dir_list is a list of the directories where the results were put (usually
# TacTok/evaluation/<exp-id>)

# It will print the resulting percentage, and the successful and total proof
# counts.

import json
import os
import sys
from glob import glob
import numpy as np
import pickle
import random
import itertools 
import argparse

projs = [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,16,17,18,19,20,21,22,23,24,25,26]


def get_results_dict(dirname):
	results_dict = {}
	num_theorems = 0
	for i in projs:
		proved = []
		files = glob(dirname + '/results_' + str(i) + '.json') + \
			glob(dirname + '/results_' + str(i) + '_*.json')
		for f in files:
			with open(f, "rb") as json_file:
				res = json.load(json_file)["results"]
				for r in res:
					num_theorems += 1
					if r["success"] == True:
						proved.append((r["filename"],r["proof_name"]))
		results_dict[i] = proved
	assert num_theorems > 0
	return results_dict, num_theorems

def combine(results_dict):
	c_list = []
	for p in results_dict:
		c_list += results_dict[p]
	return set(c_list)

def get_success_rate(results_set, num_theorems):
	return (float(len(results_set))/float(num_theorems))*100

def combine_results(results_sets_dict):
	s_union = set()
	for res in results_sets_dict:
		s_union = set().union(s_union, results_sets_dict[res])
	return s_union

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--results_dir_list', nargs="*", type=str, default=['evaluation/<exp-id>'])
    args = parser.parse_args()
    results_sets_dict = {}
    num_theorems_list = []
    for d in args.results_dir_list:
    	results_dict, n_theorems = get_results_dict(d)
    	results_sets_dict[d] = combine(results_dict)
    	num_theorems_list.append(n_theorems)
    assert len(set(num_theorems_list)) <= 1 # all the same number of theorems
    num_theorems = num_theorems_list[0]
    results_set = combine_results(results_sets_dict)
    success_rate = get_success_rate(results_set, num_theorems)
    print(f"{len(results_set)}/{num_theorems} ({success_rate:.2f}%)")
