#!/usr/bin/env python

import os
import argparse
import json

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("challenge")   
    parser.add_argument("entry_id")
    parser.add_argument("input_json")
    parser.add_argument("task_json")

    args = parser.parse_args()
   
    if args.challenge == 'isoform':
        challenge = 'IsoformQuantification'
    elif args.challenge == 'fusion':
        challenge = 'FusionDetection'

    with open (args.input_json) as f:
        job = json.load(f)
    
    with open (args.task_json) as t:
        task = json.load(t)

    d = {}   
    for key, value in task['inputs'].iteritems():
        path = "/".join(["gs://smc-rna-eval/entries", challenge, args.entry_id,value['name']])
        d[key] = {'path': path, 'class': 'File'}


    d.update(job)
    print json.dumps(d)
