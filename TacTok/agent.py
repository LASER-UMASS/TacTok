import torch
import torch.nn.functional as F
import os
from gallina import GallinaTermParser
from utils import SexpCache, log
from eval_env import FileEnv
import re
import pickle
from progressbar import ProgressBar
from glob import glob
import json
from random import random
import pdb
from hashlib import sha1
import gc
import sys
from syntax import SyntaxConfig
from copy import deepcopy
from time import time
import numpy as np
import string

def action_seq_loss(logits_batch, actions_batch, opts):
    assert len(logits_batch) == len(actions_batch)
    loss = 0
    for logits, actions in zip(logits_batch, actions_batch):
        length = min(logits.shape[0], actions.shape[0])
        loss += F.cross_entropy(logits[:length], actions[:length].to(opts.device))
    loss /= len(logits_batch)
    return loss


# merge this with extract_proof_steps.py
sexp_cache = SexpCache('../sexp_cache', readonly=True)

def filter_env(term_parser, env):
    filtered_env = []
    for const in [const for const in env['constants'] if const['qualid'].startswith('SerTop')][-10:]:
        ast = sexp_cache[const['sexp']]
        filtered_env.append({'qualid': const['qualid'], 'ast': term_parser.parse(ast)})
    return filtered_env


def parse_goal(term_parser, g):
    goal = {'id': g['id'], 'text': g['type'], 'ast': term_parser.parse(g['sexp'])}
    local_context = []
    for i, h in enumerate(g['hypotheses']):
        for ident in h['idents']:
            local_context.append({'ident': ident, 'text': h['type'], 'ast': term_parser.parse(h['sexp'])})
    return local_context, goal['ast']

rem_punc = string.punctuation.replace('\'','').replace('_', '')
table = str.maketrans('', '', rem_punc)

def tokenize_text(raw_text):
    without_punc = raw_text.translate(table)
    words = without_punc.split()
    return words

def parse_script(script):
    prev_seq = []
    for tac in script:
        tac_words = tokenize_text(tac)
        prev_seq += tac_words

    return prev_seq

def print_single_goal(g):
    for h in g['hypotheses']:
        for ident in h['idents']:
            print('\t%s: %s' % (ident, h['type']))
    print('---------------')
    print('\t%s' % g['type'])
    print('##########')


def print_goals(obs):
    if 'fg_goals' not in obs:
        print('##########')
        return
    print('########## fg_goals ##########')
    for g in obs['fg_goals']:
        print_single_goal(g)
    print('########## bg_goals ##########')
    for g in obs['bg_goals']:
        print_single_goal(g)
    print('########## shelved_goals ##########')
    for g in obs['shelved_goals']:
        print_single_goal(g)
    print('########## given_up_goals ##########')
    for g in obs['given_up_goals']:
        print_single_goal(g)


def get_goal_signature(goal):
    sexp = goal['sexp'] + ''.join([h['sexp'] for h in goal['hypotheses']])
    return sha1(sexp.encode('utf-8')).hexdigest()


class Agent:

    def __init__(self, model, optimizer, dataloader, opts):
      self.model = model
      self.optimizer = optimizer
      self.dataloader = dataloader
      self.opts = opts
      self.syn_conf = SyntaxConfig(opts.include_locals, opts.include_defs, opts.include_paths,
                                   opts.include_constructor_names, opts.merge_vocab)
      self.term_parser = GallinaTermParser(opts.coq_projects, self.syn_conf, caching=True, use_serapi=opts.include_serapi)
      self.projs_split = json.load(open(opts.projs_split))


    def train(self, n_epoch):
        self.model.train()
        lr = self.optimizer.param_groups[0]['lr']
        log(f'training with teacher forcing {self.opts.teacher_forcing}, learning rate {lr}..')

        bar = ProgressBar(max_value=len(self.dataloader['train']))
        total_epoch_loss = 0.0
        loss_since_print = 0.0
        for i, data_batch in enumerate(self.dataloader['train']):
            use_teacher_forcing = random() < self.opts.teacher_forcing
            asts, loss = self.model(data_batch['env'], data_batch['local_context'], 
                                    data_batch['goal'], data_batch['tactic_actions'], use_teacher_forcing, data_batch['prev_tokens'])
            # log('\nteacher forcing = %s, loss = %f' % (str(use_teacher_forcing), loss.item()))
            self.optimizer.zero_grad()
            loss.backward()
            self.optimizer.step() 
            gc.collect()
            bar.update(i)
            if self.opts.smoke and i == 11:
                break
            total_epoch_loss += loss.item()
            if self.opts.print_loss_every is not None:
                loss_since_print += loss.item()
                if (i + 1) % self.opts.print_loss_every == 0:
                    avg_loss_since_print = loss_since_print / self.opts.print_loss_every
                    loss_since_print = 0.0
                    print(f"loss: {avg_loss_since_print}", file=sys.stderr)
                    sys.stderr.flush()

        log('\nAverage training loss: %f' % (total_epoch_loss / len(self.dataloader['train'])))


    def valid(self, n_epoch):
        self.model.eval()
        log('validating..')
        loss_avg = 0
        predictions = []
        num_correct = 0
        bar = ProgressBar(max_value=len(self.dataloader['valid']))


        for i, data_batch in enumerate(self.dataloader['valid']):
            asts, loss = self.model(data_batch['env'], data_batch['local_context'],
                                    data_batch['goal'], data_batch['tactic_actions'], False, data_batch['prev_tokens'])
            loss_avg += loss.item()

            for n in range(len(data_batch['file'])):
                 tac_gt = data_batch['tactic_str'][n]
                 tac_pred = asts[n].to_tokens()
                 if tac_gt.replace(' ', '') == tac_pred.replace(' ', ''):
                     num_correct += 1
                 predictions.append({'file_name': data_batch['file'][n], 
                                     'proof_name': data_batch['proof_name'][n], 
                                     'n_step': data_batch['n_step'][n],
                                     'tac_gt': tac_gt, 
                                     'tac_pred': tac_pred})
            gc.collect()
            bar.update(i)
            if self.opts.smoke and i == 11:
                break

        pickle.dump(predictions, open(os.path.join(self.opts.log_dir, 'predictions/pred_%03d.pickle' % n_epoch), 'wb'))

        loss_avg /= len(self.dataloader['valid'])
        log('\nvalidation losses: %f' % loss_avg)
        acc = num_correct / len(predictions)
        log('validation accuracy: %f' % acc)
        return loss_avg


    def evaluate(self, filename, proof_name=None):
        if self.model is not None:
            self.model.eval()

        if 'hammer' in self.opts.method:
            for atp in ['Vampire', 'Z3', 'CVC4', 'Eprover']:
                if ('hammer_' + atp) in self.opts.method:
                    with_hammer = atp
                    self.opts.method = self.opts.method.replace('hammer_' + atp, 'hammer')
                    break
            else:
                with_hammer = 'All'
        else:
            with_hammer = None
        assert 'hammer_' not in self.opts.method
        hammer_timeout = self.opts.hammer_timeout if 'ours' in self.opts.method else self.opts.timeout

        with FileEnv(filename, self.opts.max_num_tactics, self.opts.timeout, debug=self.opts.debug, with_hammer=with_hammer, hammer_timeout=hammer_timeout) as file_env:
            results = []
            for proof_env in file_env:  # start a proof
                if proof_name is not None and proof_env.proof['name'] != proof_name:
                    continue
                print('proof: ', proof_env.proof['name'])
                #print('cuda memory allocated before proof: ', torch.cuda.memory_allocated(self.opts.device), file=sys.stderr)
                success, proof_pred, time, num_tactics = self.prove(proof_env)
                results.append({
                    'filename': filename, 'proof_name': proof_env.proof['name'], 'success': success,
                    'proof_gt': [step['command'][0] for step in proof_env.proof['steps'] if step['command'][1] != 'VernacEndProof'],
                    'proof_pred': proof_pred,
                    'time': time,
                    'num_tactics': num_tactics,})
                if proof_name is not None:
                    break
        return results


    def prove_one_tactic(self, proof_env, tac):
        obs = proof_env.init()
        print_goals(obs)
        obs = proof_env.step(tac + '.') 
        print(obs['result'])
        print_goals(obs)
        time = self.opts.timeout - obs['time_left']
        if obs['result'] == 'SUCCESS':
            return True, [tac], time, 1
        else:
            return False, [tac], time, 1


    def prove(self, proof_env):
        'prove a theorem interactively'
        if 'greedy' in self.opts.method or 'weighed' in self.opts.method:
            tac_template = '%s.'
            return self.prove_DFS(proof_env, tac_template)
        if 'ours' not in self.opts.method:  # auto, hammer, etc.
            return self.prove_one_tactic(proof_env, self.opts.method)

        m = re.fullmatch(r'ours\+(?P<auto_tac>\w+)', self.opts.method)  # ours+auto/hammer/etc.
        if m is not None:
            tac_template = m['auto_tac'] + '; %s.'
        else:
            tac_template = '%s.'

        return self.prove_DFS(proof_env, tac_template)


    def prove_DFS(self, proof_env, tac_template):
        obs = proof_env.init()
        env = filter_env(self.term_parser, obs['env'])
        first_goal_signatures = {get_goal_signature(obs['fg_goals'][0])}

        # initialize the stack
        local_context, goal = parse_goal(self.term_parser, obs['fg_goals'][0])

        f_top = open("baselines/top.pickle", 'rb')
        f_tac = open("baselines/tactic_list.pickle", 'rb')
        f_prob = open("baselines/tactic_probs.pickle", 'rb')
        top = pickle.load(f_top)
        tactic_list = pickle.load(f_tac)
        tactic_probs = pickle.load(f_prob)
        f_top.close()
        f_tac.close()
        f_prob.close() 

        tactics = []
        stack = [[]]
        if 'greedy' in self.opts.method:
            # choose from top
            tactics = top 
            stack = [[tac_template % tac for tac in tactics[::-1]]]
        elif 'weighed' in self.opts.method:
            # choose from distribution
            tactics = np.random.choice(tactic_list,size=20,replace=False, p=tactic_probs)
            stack = [[tac_template % tac for tac in tactics[::-1]]]
        else:
            tactics = self.model.beam_search(env, local_context, goal, [])
            stack = [[tac_template % tac.to_tokens() for tac in tactics[::-1]]]
        
        script = []

        # depth-first search starting from the trace
        while stack != [[]]:
            #print('stack: ', stack)
            # pick a tactic
            if stack[-1] == []:  # all candidate have been tried, backtrack
                stack.pop()
                script.pop()
                proof_env.step('Undo.')
                continue
            else:
                tac = stack[-1].pop()

            obs = proof_env.step(tac)
            print(obs['result'])
            print_goals(obs)

            if obs['result'] == 'SUCCESS':
                script.append(tac)
                time = self.opts.timeout - obs['time_left']
                num_tactics = self.opts.max_num_tactics - obs['num_tactics_left']
                return True, script, time, num_tactics
            elif obs['result'] in ['MAX_NUM_TACTICS_REACHED', 'MAX_TIME_REACHED']:
                time = self.opts.timeout - obs['time_left']
                num_tactics = self.opts.max_num_tactics - obs['num_tactics_left']
                return False, script, time, num_tactics
            elif obs['result'] in ['ERROR']:
                continue
            else:
                assert obs['result'] == 'PROVING'
                script.append(tac)
                sig = get_goal_signature(obs['fg_goals'][0])
                if sig in first_goal_signatures or len(script) >= self.opts.depth_limit:
                    proof_env.step('Undo.')
                    script.pop()
                    continue
                first_goal_signatures.add(sig)
                local_context, goal = parse_goal(self.term_parser, obs['fg_goals'][0])
                tactics = []
                if 'greedy' in self.opts.method:
                    # choose from top
                    tactics = top 
                    stack.append([tac_template % tac for tac in tactics[::-1]])
                elif 'weighed' in self.opts.method:
                    # choose from distribution
                    tactics = np.random.choice(tactic_list,size=20,replace=False, p=tactic_probs)
                    stack.append([tac_template % tac for tac in tactics[::-1]])
                else:
                    prev_seq = parse_script(script)
                    tactics = self.model.beam_search(env, local_context, goal, prev_seq)
                    stack.append([tac_template % tac.to_tokens() for tac in tactics[::-1]])
                

        obs = proof_env.step('Admitted.')
        print(obs['result'])
        time = self.opts.timeout - obs['time_left']
        num_tactics = self.opts.max_num_tactics - obs['num_tactics_left']
        return False, script, time, num_tactics


    def prove_IDDFS(self, proof_env, tac_template):
        obs = proof_env.init()
        env = filter_env(self.term_parser, obs['env'])
        first_goal_signatures = {get_goal_signature(obs['fg_goals'][0])}
        depth_limit = self.opts.depth_limit
        traces = [[]]

        # iterative deepening depth-first search
        while traces != []:
            # depth-first search with depth_limit
            new_traces = []  # the newly-discovered truncated proofs
            for script in traces:
                # execute the tactics in the trace
                for tac in script:
                    obs = proof_env.step(tac)
                print(obs['result'])
                print_goals(obs)
                if obs['result'] != 'PROVING':
                    assert obs['result'] in ['MAX_NUM_TACTICS_REACHED', 'MAX_TIME_REACHED']
                    time = self.opts.timeout - obs['time_left']
                    num_tactics = self.opts.max_num_tactics - obs['num_tactics_left']
                    return False, script, time, num_tactics
                # initialize the stack
                local_context, goal = parse_goal(self.term_parser, obs['fg_goals'][0])
                prev_seq = parse_script(script)    
                tactics = self.model.beam_search(env, local_context, goal, prev_seq)
                stack = [[tac_template % tac.to_tokens() for tac in tactics[::-1]]]

                # depth-first search starting from the trace
                while stack != [[]]:
                    print('stack: ', stack)
                    # pick a tactic
                    if stack[-1] == []:  # all candidate have been tried, backtrack
                        stack.pop()
                        script.pop()
                        proof_env.step('Undo.')
                        continue
                    else:
                        tac = stack[-1].pop()

                    obs = proof_env.step(tac)
                    print(obs['result'])
                    print_goals(obs)
                     
                    if obs['result'] == 'SUCCESS':
                        script.append(tac)
                        time = self.opts.timeout - obs['time_left']
                        num_tactics = self.opts.max_num_tactics - obs['num_tactics_left']
                        return True, script, time, num_tactics
                    elif obs['result'] in ['MAX_NUM_TACTICS_REACHED', 'MAX_TIME_REACHED']:
                        time = self.opts.timeout - obs['time_left']
                        num_tactics = self.opts.max_num_tactics - obs['num_tactics_left']
                        return False, script, time, num_tactics
                    elif obs['result'] in ['ERROR']:
                        continue
                    else:
                        assert obs['result'] == 'PROVING'
                        script.append(tac)
                        sig = get_goal_signature(obs['fg_goals'][0])
                        if sig in first_goal_signatures or len(script) >= depth_limit:
                            if len(script) >= depth_limit and sig not in first_goal_signatures:
                                new_traces.append(deepcopy(script))
                            proof_env.step('Undo.')
                            script.pop()
                            continue
                        first_goal_signatures.add(sig)
                        local_context, goal = parse_goal(self.term_parser, obs['fg_goals'][0])
                        prev_seq = parse_script(script)
                        tactics = self.model.beam_search(env, local_context, goal, prev_seq)
                        stack.append([tac_template % tac.to_tokens() for tac in tactics[::-1]])

                proof_env.step('Restart.')
                gc.collect()

            depth_limit *= 2
            traces = new_traces

        obs = proof_env.step('Admitted.')
        print(obs['result'])
        time = self.opts.timeout - obs['time_left']
        num_tactics = self.opts.max_num_tactics - obs['num_tactics_left']
        return False, script, time, num_tactics
         

    def save(self, n_epoch, dirname):
        torch.save({'state_dict': self.model.state_dict(), 'n_epoch': n_epoch,
                    'optimizer': self.optimizer.state_dict()}, os.path.join(dirname, 'model_%03d.pth' % n_epoch))
