#!/usr/bin/env python

import os
import argparse
import json

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("entry_id")
    parser.add_argument("input_json")
    
    args = parser.parse_args()

   synTable = {
        '8645203': 'gs://smc-rna-eval/entries/FusionDetection/8645203/star_index.tar.gz',
        '8645601': 'gs://smc-rna-eval/entries/FusionDetection/8645601/star_index.tar.gz',
        '8645625': 'gs://smc-rna-eval/entries/FusionDetection/8645625/star_index.tar.gz'
    }

    with open (args.input_json) as f:
        job = json.load(f)
   
    job["index"] = {
        "class": "File",
        "path": synTable[args.entry_id]
    }

    print json.dumps(job)
