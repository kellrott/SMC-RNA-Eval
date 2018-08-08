#!/usr/bin/env python3

import sys
import summa
import pandas
import random
import json
import numpy as np

INPUT_PATH=sys.argv[1]
RANDOM_SEED=int(sys.argv[2])
OUTPUT_PATH=sys.argv[3]


def compute_scores(data, weights):
    s = 0
    for j in range(len(weights)):
          s+= weights[j] * data[j, :]
    return s

random.seed(RANDOM_SEED)

SAMPLE_SIZE=0.5
SAMPLE_COUNT=1000

fusions=pandas.read_csv(INPUT_PATH, index_col=0, sep="\t").transpose()

entries = fusions[fusions.index != "truth"]
truth = fusions[fusions.index == "truth"]

handle = open(OUTPUT_PATH, "w")
for i in range(SAMPLE_COUNT):
    curSet = random.sample(range(entries.shape[0]), int(entries.shape[0]*SAMPLE_SIZE))
    curEntries=entries.iloc[curSet,:]
    scl = summa.summa(curEntries.values, sample_names=curEntries.columns, bc_names=curEntries.index, tensor=False)
    weights = dict(zip(curEntries.index, scl.get_weights()))
    #inference = pandas.Series(dict(zip(curEntries.columns, scl.inference(curEntries.values, 0.1))))
    #posCount = sum(inference==1.0)
    #negCount = sum(inference==0.0)
    #print( ((entries == inference) & (inference==1.0)).sum(axis=1) )

    scores = compute_scores(curEntries.values, scl.get_weights())
    thresholds = np.unique(scores)
    tp_matrix = []
    fp_matrix = []
    tn_matrix = []
    fn_matrix = []

    posCount_out = []
    negCount_out = []

    for threshold in thresholds:
        inference = scores > threshold
        posCount = int(sum(scores >= threshold))
        negCount = int(sum(scores < threshold))

        tp = ((entries == inference) & (inference == True)).sum(axis=1)
        fp = ((entries != inference) & (inference == False)).sum(axis=1)
        tn = ((entries == inference) & (inference == False)).sum(axis=1)
        fn = ((entries != inference) & (inference == True)).sum(axis=1)

        tp_matrix.append(tp)
        fp_matrix.append(fp)
        tn_matrix.append(tn)
        fn_matrix.append(fn)

        posCount_out.append(posCount)
        negCount_out.append(negCount)

    tp_out = dict(list( (i, list(k)) for i, k in pandas.DataFrame(tp_matrix).transpose().iterrows()))
    fp_out = dict(list( (i, list(k)) for i, k in pandas.DataFrame(fp_matrix).transpose().iterrows()))
    tn_out = dict(list( (i, list(k)) for i, k in pandas.DataFrame(tn_matrix).transpose().iterrows()))
    fn_out = dict(list( (i, list(k)) for i, k in pandas.DataFrame(fn_matrix).transpose().iterrows()))

    report = {
        "weights" : weights,
        "thresholds" : list(thresholds),
        "posCount":posCount_out,
        "negCount":negCount_out,
        "tp" : tp_out,
        "fp" : fp_out,
        "tn" : tn_out,
        "fn" : fn_out
    }

    handle.write(json.dumps( report ))
    handle.write("\n")
handle.close()
