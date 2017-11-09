import argparse
from collections import defaultdict, namedtuple, Counter
from glob import glob

from interval.closed import Interval, Tree

# Note, when thinking about positions in this code, keep in mind that BEDPE has a weird
# backwards-half-open notion of positions, where start1 is actually the zero-based start
# of the feature MINUS 1. Also, the end position is 1-based, because things weren't already
# confusing enough.

Fusion = namedtuple("Fusion", "entry sim lineno chrom1 start1 end1 chrom2 start2 end2 name score strand1 strand2")

valid_chroms = """
1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 x y
""".strip().split()

fusions = {}
trees_by_chrom = defaultdict(Tree)

# Return a key (string) for a Fusion record, `entry-sim-lineno`
def fusion_key(f):
    return f.entry + "-" + f.sim + "-" + str(f.lineno)

# This code expects the data to be in a specific directory tree format:
# "./downloaded-data/fusion/{entry_ID}/{tumor_ID}/*.bedpe"
for l in glob("./downloaded-data/fusion/*/*/*.bedpe"):
    fsp = l.split("/")
    _, _, _, entry, sim, _ = fsp
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

        f = Fusion(
            entry, sim, lineno,
            chrom1, start1, end1,
            chrom2, start2, end2, name,
            score,
            strand1, strand2
        )
        key = fusion_key(f)
        fusions[key] = f
        chrom1_tree = trees_by_chrom[chrom1]
        chrom2_tree = trees_by_chrom[chrom2]
        chrom1_tree.insert(start1, end1, f)
        chrom2_tree.insert(start2, end2, f)

# Require that both donor and acceptor match
def full_match(leeway):
    def _match(a, b):
        # Note, I'm ignoring the end position because I expect all these fusions
        # are only a single position.
        if a.chrom1 != b.chrom1:
            return False
        if a.chrom2 != b.chrom1:
            return False
        if abs(a.start1 - b.start1) > leeway:
            return False
        if abs(a.start2 - b.start2) > leeway:
            return False
        return True
    return _match

# Only require one of either donor or acceptor to match
def partial_match(leeway):
    def _match(a, b):
        if a.chrom1 != b.chrom1 and a.chrom2 != b.chrom1:
            return False
        if abs(a.start1 - b.start1) > leeway and abs(a.start2 - b.start2) > leeway:
            return False
        return True
    return _match


# Given a fusion call "f", find overlapping and matching (using "match" function) fusions.
# "leeway" is the genomic distance used to find "overlapping" fusions.
def find_matches(f, match, leeway):
    # Get interval trees for the chromosomes of the donor/acceptor of this fusion.
    chrom1_tree = trees_by_chrom[f.chrom1]
    chrom2_tree = trees_by_chrom[f.chrom2]

    # Find other fusions overlapping the interval of both donor and acceptor.
    match1 = chrom1_tree.find(f.start1 - leeway, f.end1 + leeway)
    match2 = chrom2_tree.find(f.start2 - leeway, f.end2 + leeway)

    # Filter candidates from both tree queries to get only fusions that match.
    filtered = set()
    for c in match1 + match2:
        if match(c, f):
            filtered.add(c)

    return filtered

    ## old code which counted the number of overlapping fusions
    #counts = Counter()
        #key = len(filtered)
        #counts[key] += 1
    #return counts
        #if len(filtered) > 0:
            #print "\t".join(str(x) for x in [
                #f.entry, f.sim, f.chrom1, f.start1, f.chrom2, f.start2, len(filtered),
            #])
        #for m in list(filtered)[:10]:
            #print "entry:%s\tsim:%s\tline:%d\tpos1:%s:%d\tpos2:%s:%d" % (
                #m.entry, m.sim, m.lineno, m.chrom1, m.start1, m.chrom2, m.start2,
            #)
        #print



for fkey, f in fusions.items():
    for g in find_matches(f, full_match(10), 10):
        print fkey, fusion_key(g)
    #partial_10 = find_matches(f, partial_match(10), 10)
    #full_150 = find_matches(f, full_match(150), 150)
    #partial_150 = find_matches(f, partial_match(150), 150)
    #full_300 = find_matches(f, full_match(300), 300)
    #partial_300 = find_matches(f, partial_match(300), 300)

'''
z = max(
    max(full_10.keys()),
    max(partial_10.keys()),
    max(full_150.keys()), 
    max(partial_150.keys()), 
    max(full_300.keys()), 
    max(partial_300.keys()),
)
for x in range(z+1):
    print "\t".join(str(i) for i in [
        x,
        full_10[x],
        partial_10[x],
        full_150[x],
        partial_150[x],
        full_300[x],
        partial_300[x],
    ])
'''
