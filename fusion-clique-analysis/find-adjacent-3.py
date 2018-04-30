import argparse
from collections import defaultdict, namedtuple, Counter
from glob import glob
import itertools
import os

# Note, when thinking about positions in this code, keep in mind that BEDPE has a weird
# backwards-half-open notion of positions, where start1 is actually the zero-based start
# of the feature MINUS 1.

Row = namedtuple("Row", "entry sample sample_name method user chrom1 start1 strand1 chrom2 start2 strand2 score")

class RowGrouper:
    def __init__(self, row):
        self.row = row

    def set_group1(self, g1):
        self.group1 = g1

    def set_group2(self, g2):
        self.group2 = g2


groupers = []
breakpoints = []

for l in open("data/generated/combined-fusion-data.tsv"):
    sp = l.strip().split("\t")
    row = Row(*sp)

    start1 = int(row.start1)
    start2 = int(row.start2)
    grouper = RowGrouper(row)
    groupers.append(grouper)

    breakpoints.append((row.strand1, row.chrom1, start1, grouper.set_group1, row))
    breakpoints.append((row.strand2, row.chrom2, start2, grouper.set_group2, row))


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

    assert pos >= lpos

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


#fusions = set()
#entries = set()
#adj = set()

for g in groupers:
    g1 = g.group1
    g2 = g.group2
    g1key = g1[0].chrom1, g1[0].strand1, g1[0].start1, g1[-1].chrom1, g1[-1].strand1, g1[-1].start1
    g2key = g2[0].chrom2, g2[0].strand2, g2[0].start2, g2[-1].chrom2, g2[-1].strand2, g2[-1].start2

    cols = list(g.row)
    cols.extend(g1key)
    cols.extend(g2key)

    if int(g1[-1].start1) - int(g1[0].start1) > 2 or int(g2[-1].start1) - int(g2[0].start1) > 2:
        print "\t".join(cols)

#entries = sorted(entries)
#fusions = sorted(fusions)


#def group_interval_length(g):
#    return g[-1][2] - g[0][2]

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
