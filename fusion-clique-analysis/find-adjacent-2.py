import argparse
from collections import defaultdict, namedtuple, Counter
from glob import glob
import itertools
import os

# Note, when thinking about positions in this code, keep in mind that BEDPE has a weird
# backwards-half-open notion of positions, where start1 is actually the zero-based start
# of the feature MINUS 1. Also, the end position is 1-based, because things weren't already
# confusing enough.

Fusion = namedtuple("Fusion", "entry sim lineno chrom1 start1 end1 chrom2 start2 end2 name score strand1 strand2")

valid_chroms = """
1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 x y
""".strip().split()

# Return a key (string) for a Fusion record, `entry-sim-lineno`
def fusion_key(f):
    return f.entry + "-" + f.sim + "-" + str(f.lineno)

method_meta = [l.strip().split("\t") for l in open("data/ref/fusion_metadata.tsv")]
method_meta = dict((r[0], r[-1]) for r in method_meta)

class Row:
    def __init__(self, chrom1, start1, end1, chrom2, start2, end2, name, score, strand1, strand2, entry, sim, lineno):
        self.chrom1 = chrom1
        self.start1 = start1
        self.end1 = end1
        self.chrom2 = chrom2
        self.start2 = start2
        self.end2 = end2
        self.name = name
        self.score = score
        self.strand1 = strand1
        self.strand2 = strand2
        self.entry = entry
        self.sim = sim
        self.lineno = lineno
        self.group1 = []
        self.group2 = []
        self.truth = False
        self.filepath = ""
        self.raw = ""
        self.method = ""

    def set_group1(self, g1):
        self.group1 = g1

    def set_group2(self, g2):
        self.group2 = g2


# This code expects the data to be in a specific directory tree format:
# "./downloaded-data/fusion/{entry_ID}/{tumor_ID}/*.bedpe"
rows = []
breakpoints = []

eval_files = glob("data/downloaded/fusion/*/*/*.bedpe")
truth_files = glob("./*_truth.bedpe")

"""
Load bedpe files
"""

#for l in eval_files + truth_files:
for l in eval_files:
    entry = ""
    sim = ""
    method = ""
    truth = False

#    if "truth" in l:
#        if os.path.basename(l) not in truth_file_filter:
#            continue
#        truth = True
#        entry = l
#        sim = l
#    else:
    fsp = l.split("/")
    _, _, _, entry, sim, _ = fsp
    method = method_meta[entry]

    for lineno, m in enumerate(open(l).read().splitlines()):
        sp = m.split("\t")
        #print l, lineno, sp
        chrom1, start1, end1, chrom2, start2, end2, name, score, strand1, strand2 = sp[:10]

        try:
            start1 = int(start1)
            end1 = int(end1)
            start2 = int(start2)
            end2 = int(end2)
        except ValueError:
            continue

        if start1 < 0 or end1 < 0 or start2 < 0 or end2 < 0:
            raise "unknown position"

        try:
            # simplifying assumption: each feature is a single base.
            assert end1 - start1 == 1
            assert end2 - start2 == 1
            # simplifying assumption: start is less than end.
            assert start1 < end1
            assert start2 < end2
        except AssertionError:
            continue

        chrom1 = chrom1.lower()
        chrom2 = chrom2.lower()

        # Drop unknown chromosome names
        if chrom1 not in valid_chroms or chrom2 not in valid_chroms:
            continue

        # More readable chromosome names
        chrom1 = "chr" + chrom1
        chrom2 = "chr" + chrom2
        row = Row(chrom1, start1, end1, chrom2, start2, end2, name, score, strand1, strand2, entry, sim, lineno)
        row.truth = truth
        row.filepath = l
        row.raw = m
        row.method = method
        rows.append(row)

        breakpoints.append((strand1, chrom1, start1, row.set_group1, row))
        breakpoints.append((strand2, chrom2, start2, row.set_group2, row))


#print "total breakpoints", len(breakpoints)
#print "uniq breakpoints", len(set((x[0], x[1], x[2]) for x in breakpoints))
breakpoints = sorted(breakpoints)

groups = []
group = []
last = None
window = 300

"""
Group nearby breakpoints
"""

for bp in breakpoints:
    strand, chrom, pos, set_group, row = bp

    if last is None:
        group = [row]
        groups.append(group)
        set_group(group)
        last = bp
        continue

    lstrand, lchrom, lpos, lset_group, lrow = last
    if chrom != lchrom or strand != lstrand:
        group = [row]
        groups.append(group)
        set_group(group)
        last = bp
        continue

    if pos > lpos + window:
        group = [row]
        groups.append(group)
        set_group(group)
        last = bp
        continue

    group.append(row)
    set_group(group)
    last = bp


#print "groups by window", len(groups)

# assert that we didn't miss/add any breakpoints in the groups
assert len(breakpoints) == sum(len(g) for g in groups)


def group_interval_length(g):
    return g[-1][2] - g[0][2]

# Sort by number of breakpoints in each group
#largest_groups = list(sorted(groups, key=lambda g: len(g), reverse=True))
#print "breakpoint counts for largest 10 groups", [len(g) for g in largest_groups[:10]]

#print "interval length for largest 10 groups", [group_interval_length(g) for g in largest_groups[:10]]

# Sort by interval length of each group
#longest_groups = list(sorted(groups, key=group_interval_length, reverse=True))
#print "longest intervals", [group_interval_length(g) for g in longest_groups[:100]]


"""
from decimal import Decimal
from histo import histogram, HistogramOptions, DataPoint

hist_data = []
hist_opts = HistogramOptions()
hist_opts.custbuckets = '300,800,1200,1500'
hist_opts.custbuckets = '10,50,100,150,200,300,400,500,600,700,800,1200,1500'

for g in longest_groups:
    l = group_interval_length(g)
    d = Decimal(l)
    dp = DataPoint(d, 1)
    hist_data.append(dp)

histogram(hist_data, hist_opts)
"""


fusions = set()
entries = set()
adj = set()


for row in rows:
    g1, g2 = sorted([row.group1, row.group2])
    print row.entry, row.sim, g1[0].chrom1, str(g1[0].start1), g2[0].chrom2, str(g2[0].start2)
    #print row.entry, row.chrom1, row.start1, row.chrom2, row.start2
    #entries.add(row.entry)
    #fusions.add(f)
    #adj.add((row.entry, f))

#entries = sorted(entries)
#fusions = sorted(fusions)

"""
rows = []
header = ["entry"] + list(fusions)
rows.append(header)

for entry in entries:
    row = [entry]
    rows.append(row)
    for fus in fusions:
        if (entry, fus) in adj:
            row.append("1")
        else:
            row.append("0")

for r in rows:
    print ",".join(r)

"""
"""
class Match(object):
    def __init__(self, r):
        self.r = r

    def _key(self):
        return self.r.chrom1, self.r.start1, self.r.chrom2, self.r.start2, self.r.strand1, self.r.strand2

matches = []

for r in rows:
    if r.sim not in truth_library_filter:
        continue

    g1_has_truth = any(x.truth for x in r.group1)
    g2_has_truth = any(x.truth for x in r.group2)

    if not g1_has_truth and not g2_has_truth:
        #print r.chrom1, r.start1, r.chrom2, r.start2, r.entry, r.sim, r.lineno, r.filepath
        #print r.raw
        matches.append(Match(r))
        #for x in g1 + g2:
            #_, _, _, _, r = x
            #print r.chrom1, r.start1, r.chrom2, r.start2, r.entry, r.sim, r.lineno, r.filepath

matches = sorted(matches, key=lambda r: r._key())

grouped = list((key, list(group)) for key, group in itertools.groupby(matches, lambda r: r._key()))
grouped = sorted(grouped, key=lambda x: (len(x[1]), len(set(y.r.method for y in x[1]))))

for key, group in grouped:
    r = group[0].r
    print len(group), Counter(x.r.method for x in group).most_common(), r.raw
    #print r.raw
"""
