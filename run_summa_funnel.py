#!/usr/bin/env python

import sys
import string

tDoc = """
{
  "name": "SUMMA",
  "inputs": [
    {
      "name": "src",
      "url": "${INPUT}",
      "path": "/data/matrix.tsv"
    }
  ],
  "outputs": [
    {
      "url": "${OUTPUT}-${SEED}.json.gz",
      "path": "/data/outfile-${SEED}.json.gz"
    }
  ],
  "executors": [
    {
      "image": "docker.compbio.ohsu.edu/summa:latest",
      "command": [
        "/opt/summa/script/run_summa_rna.py",
        "/data/matrix.tsv",
        "${SEED}",
        "/data/outfile-${SEED}.json"
      ]
    },{
      "image": "docker.compbio.ohsu.edu/summa:latest",
      "command": [
        "gzip",
        "/data/outfile-${SEED}.json"
      ]
    }
  ]
}
"""

template = string.Template(tDoc)

#INPUT
#swift://smc-rna-analysis/summa-matrix-v3-real-data-binary.tsv

INPUT=sys.argv[1]
SEED=sys.argv[2]
OUTPUT=sys.argv[3]

doc = template.substitute(INPUT=INPUT,SEED=SEED,OUTPUT=OUTPUT)

print(doc)
