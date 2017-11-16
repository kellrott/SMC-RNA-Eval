#!/usr/bin/env python

import os
import yaml
import argparse
import json
import csv
import sys

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--bucket", default="gs://smc-rna-eval")
    parser.add_argument("--data", default="tumors")
    parser.add_argument("--syn-table")
    parser.add_argument("test")
    parser.add_argument("workflow")
    parser.add_argument("tumor", nargs="+")
    
    args = parser.parse_args()
    
    synTable = {}
    with open(args.syn_table) as handle:
        reader = csv.reader(handle, delimiter="\t")
        for row in reader:
            synTable[row[0]] = "%s/%s" % (args.bucket, row[1])

    for tumor in args.tumor:
        job = {
            "TUMOR_FASTQ_1" : {
                "class" : "File",
                "path" : "%s/%s/%s_R2_001.fastq.gz" % (args.bucket, args.data, tumor)
            },
            "TUMOR_FASTQ_2" : {
                "class" : "File",
                "path" : "%s/%s/%s_R1_001.fastq.gz" % (args.bucket, args.data, tumor)
            },
            "REFERENCE_GENOME" : {
                "class" : "File",
                "path" : "%s/Homo_sapiens.GRCh37.75.dna_sm.primary_assembly.fa" % (args.bucket)
            },
            "REFERENCE_GTF" : {
                "class" : "File",
                "path" : "%s/Homo_sapiens.GRCh37.75.gtf" % (args.bucket)
            }
        }
        
        
        with open(args.workflow) as handle:
            doc = yaml.load(handle.read())
        
        workflow = None
        
        if "$graph" in doc:
            for d in doc["$graph"]:
                if d['id'] == "#main":
                    workflow = d
        user_inputs = {}
        try:
            for i in workflow.get("hints", []):
                if os.path.basename(i['class']) == 'synData':
                    user_inputs[i['input']] = i['entity']
        except AttributeError:
            sys.stderr.write("No hints found\n")
            pass

        for k, v in user_inputs.items():
            job[k] = { 
                "class" : "File",
                "path" : synTable[v]
            }

        print json.dumps(job)
