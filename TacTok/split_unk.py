import os
import json
import pickle
import sys
sys.setrecursionlimit(100000)
sys.path.append(os.path.normpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../')))
import argparse

# Split a dictionary into known and unknown dictionaries.
# Sadly, I was so excited to write this simple script that I broke my toe.
# Was it worth it? It's not even that interesting. I just want to see results.
# Machine learning is clearly dangerous.

# Split a dictionary along some boolean function
def split_dict(d, f):
    f_true = {}
    f_false = {}

    for (k, v) in d.items():
        if f(d, k):
            f_true[k] = v
        else:
            f_false[k] = v

    return f_true, f_false

# Split the inputs into known and unknown dictionaries along a threshold
def split_inputs(inputs, threshold):
    def is_known(d, k):
        return (d[k] >= threshold)

    return split_dict(inputs, is_known)

# Split the inputs along the threshold, then dump to files
if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser(description='Split a dictionary into known and unknown dictionaries')
    arg_parser.add_argument('input', metavar='<input>.pickle', type=str,
                                help='pickle file for input dictionary')
    arg_parser.add_argument('--threshold', type=int, default=100,
                                help='threshold below which to consider unknown')
    args = arg_parser.parse_args()
    print(args)

    input_f = open(args.input, 'rb')
    inputs = pickle.load(input_f)
    input_f.close()

    known, unknown = split_inputs(inputs, args.threshold)
    output_prefix = os.path.splitext(args.input)[0]

    def dump_outputs(outputs, output_suffix):
        output = output_prefix + '-' + output_suffix + '.pickle'
        output_f = open(output, 'wb')
        pickle.dump(outputs, output_f)
        output_f.close()
        print(len(outputs), 'keys and values saved to', output)

    dump_outputs(known, 'known')
    dump_outputs(unknown, 'unknown')


