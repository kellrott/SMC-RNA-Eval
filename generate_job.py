#!/usr/bin/env python

import os
import yaml
import argparse
import json
import csv

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--test-bucket", default="gs://smc-rna-eval/tumors")
    parser.add_argument("--syn-table")
    parser.add_argument("test")
    parser.add_argument("workflow")
    parser.add_argument("tumor", nargs="+")
    
    args = parser.parse_args()
    
    synTable = {}
    with open(args.syn_table) as handle:
        reader = csv.reader(handle, delimiter="\t")
        for row in reader:
            synTable[row[0]] = row[1]

    for tumor in args.tumor:
        job = {
            "TUMOR_FASTQ_1" : {
                "class" : "File",
                "path" : "%s/%s_mergeSort_1.fq.gz" % (args.test_bucket, tumor)
            },
            "TUMOR_FASTQ_2" : {
                "class" : "File",
                "path" : "%s/%s_mergeSort_2.fq.gz" % (args.test_bucket, tumor)
            },
            "REFERENCE_GENOME" : {
                "class" : "File",
                "path" : "gs://smc-rna-eval/Homo_sapiens.GRCh37.75.dna_sm.primary_assembly.fa"
            },
            "REFERENCE_GTF" : {
                "class" : "File",
                "path" : "gs://smc-rna-eval/Homo_sapiens.GRCh37.75.gtf"
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
        for i in workflow.get("hints", []):
            if os.path.basename(i['class']) == 'synData':
                user_inputs[i['input']] = i['entity']
        
        for k, v in user_inputs.items():
            job[k] = { 
                "class" : "File",
                "path" : synTable[v]
            }

        print json.dumps(job)
                
            