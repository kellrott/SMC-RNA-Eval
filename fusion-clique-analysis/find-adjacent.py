from collections import defaultdict, namedtuple
from interval.closed import Interval, Tree

# Note, when thinking about positions in this code, keep in mind that BEDPE has a weird
# backwards-half-open notion of positions, where start1 is actually the zero-based start
# of the feature MINUS 1. Also, the end position is 1-based, because things weren't already
# confusing enough.

Fusion = namedtuple("Fusion", "entry sim lineno chrom1 start1 end1 chrom2 start2 end2 name score strand1 strand2")

valid_chroms = """
1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 x y
""".strip().split()

fusions = []
trees_by_chrom = defaultdict(Tree)

for l in open("output.files.txt").read().splitlines():
    fsp = l.split("/")
    _, _, entry, sim, _ = fsp
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
        fusions.append(f)
        chrom1_tree = trees_by_chrom[chrom1]
        chrom2_tree = trees_by_chrom[chrom2]
        chrom1_tree.insert(start1, end1, f)
        chrom2_tree.insert(start2, end2, f)

leeway = 10

def full_match(a, b):
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

def partial_match(a, b):
    if a.chrom1 != b.chrom1 and a.chrom2 != b.chrom1:
        return False
    if abs(a.start1 - b.start1) > leeway and abs(a.start2 - b.start2) > leeway:
        return False
    return True

for f in fusions:
    chrom1_tree = trees_by_chrom[f.chrom1]
    chrom2_tree = trees_by_chrom[f.chrom2]

    close1 = chrom1_tree.find(f.start1 - leeway, f.end1 + leeway)
    close2 = chrom2_tree.find(f.start2 - leeway, f.end2 + leeway)

    # Filter candidates from both tree queries to get only fusions that match.
    filtered = set()
    for c in close1 + close2:
        if partial_match(c, f):
            filtered.add(c)

    print "entry:%s\tsim:%s\tline:%d\tchrom1:%s\tpos1:%d\tchrom2:%s\tpos2:%d\tnum adjacent:%d" % (
        f.entry, f.sim, f.lineno, f.chrom1, f.start1, f.chrom2, f.start2, len(filtered),
    )
    for m in list(filtered)[:10]:
        print "entry:%s\tsim:%s\tline:%d\tchrom1:%s\tpos1:%d\tchrom2:%s\tpos2:%d" % (
            m.entry, m.sim, m.lineno, m.chrom1, m.start1, m.chrom2, m.start2,
        )
    print

