#!/usr/bin/env python

import numpy as np
import os
import json
import sys
from glob import glob
import gzip

ranks = {}

for path in glob(os.path.join(sys.argv[1], "*json.gz")):
    with gzip.open(path) as handle:
        for line in handle:
            data = json.loads(line)
            methods, scores = zip(*data["weights"].items())
            r = np.array(scores).argsort().argsort()
            for k, v in zip(methods, r):
                if k in ranks:
                    ranks[k].append(float(v))
                else:
                    ranks[k] = [float(v)]

for k, v in ranks.items():
    print("%s %f (%f)" % (k, np.mean(v), np.std(v)))
