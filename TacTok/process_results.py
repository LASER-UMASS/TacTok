import json
import os
import sys
from glob import glob
import numpy as np
import pickle
import random
import itertools 

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

results_dict, num_theorems = get_results_dict("bpe_evaluation/tactok_results") #replace with dirname
results_set = combine(results_dict)
success_rate = get_success_rate(results_set, num_theorems) 
print(f"{len(results_set)}/{num_theorems} ({success_rate:.2f}%)")
