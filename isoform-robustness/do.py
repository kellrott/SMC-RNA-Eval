from __future__ import print_function
from collections import defaultdict
from glob import glob

#truth_by_sample = {}
entries_by_sample = defaultdict(dict)
samples = set()


transcript_list = '''
ENST00000270310
ENST00000588265
ENST00000586063
ENST00000380346
ENST00000380347
ENST00000375825
ENST00000375824
ENST00000479334
ENST00000373083
ENST00000373086
ENST00000373089
ENST00000053243
ENST00000562385
ENST00000396495
ENST00000373161
ENST00000470917
ENST00000373158
'''.strip().split()


def max_normalize(row):
    mx = max(row)
    if mx == 0.0:
        return row
    return [x / mx for x in row]


for f in glob("*_expression.tsv"):

    # Split file name into ID, sample
    g = f.replace("_expression.tsv", "")
    i = g.index("_")
    ID, sample = g[:i], g[i+1:]
    
    # Load data table, split rows, header
    lines = open(f).read().splitlines()
    rows = [l.split("\t") for l in lines]
    header = rows[0]
    # extract transcripts from first column
    transcripts = [row[0] for row in rows[1:]]
    
    # ensure that all data has the same transcript order
    assert transcripts == transcript_list
    
    # get values, convert to float
    data = [[float(x) for x in row[1:]] for row in rows[1:]]
    # normalize all values by max value in row
    normalized = [max_normalize(row) for row in data]
    # keep a set of all samples
    samples.add(sample)
    
    rec = {
        "ID": ID,
        "sample": sample,
        "header": header,
        "transcripts": transcripts,
        "data": data,
        "normalized": normalized,            
    }

    #if ID == "truth":
     #   truth_by_sample[sample] = rec
    #else:
    entries_by_sample[sample][ID] = rec

import itertools
import random
from collections import defaultdict
from scipy import stats

# There are 17 transcripts.
# Get all possible combinations of "N choose K" transcripts.
# Values are 0-17, which refer to row indicies for each data table.
total_number_of_transcripts = 17 
def combinations(number_to_choose):
    N = total_number_of_transcripts
    K = number_to_choose
    combinations = list(itertools.combinations(range(N), K))

    # randomize combinations
    random.shuffle(combinations)
    return combinations

def sample_with_replacement(number_to_choose, number_of_combos):
    combos = []
    i = range(total_number_of_transcripts)
    for y in range(number_of_combos):
        combo = []
        combos.append(combo)
        for x in range(number_to_choose):
            combo.append(random.choice(i))
    return combos

# get spearmean correlation for every combination of transcripts
# generated above, for a single entry, compared against the "truth"
# data.
#
# Return a list of spearman correlations, one for each combination.
def correlate_all_combinations(combos, entry, truth):
    res = []
    for combo in combos:
        # get entry rows for each transcript in the combination
        erows = [entry["normalized"][i] for i in combo]
        # get rows from the truth data
        trows = [truth["normalized"][i] for i in combo]
        # flatten the rows for input to the correlation function
        eflat = [x for row in erows for x in row]
        tflat = [x for row in trows for x in row]
        # calculate correlation and store result
        corr, p_value = stats.spearmanr(tflat, eflat)
        combo_str = ','.join([str(i) for i in combo])
        res.append((combo_str, corr, p_value))
    return res
        


# For each entry in each sample, calculate a list of correlations
# with the truth data for each combination.
print("sample", "entry", "K", "combo", "correlation", "p_value")
for K in [17]:
    #combos = combinations(K)
    combos = sample_with_replacement(K, 100)
    for sample in entries_by_sample.keys():
        truth = entries_by_sample[sample]["truth"]
        for entry_ID, rec in entries_by_sample[sample].items():
            if entry_ID == "truth":
                    continue
            for v in correlate_all_combinations(combos, rec, truth):
                combo_str, corr, p_value = v
                print(sample, entry_ID, K, combo_str, corr, p_value, sep="\t")
