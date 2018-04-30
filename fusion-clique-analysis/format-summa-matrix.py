from collections import defaultdict, namedtuple

Data = namedtuple("Data", "entry sample sample_name method user chrom1 start1 strand1 chrom2 start2 strand2 score")

fusion_key = lambda r: (r.chrom1, r.start1, r.strand1, r.chrom2, r.start2, r.strand2)

#spikein_key = lambda r: ("spikein", r.chrom1, r.start1, r.strand1, r.chrom2, r.start2, r.strand2)
#spikeins = set()

fusions = set()
entries = set()

# rows are fusions, columns are entries
# cells are binary 1/0 for whether that entry called that fusion
table = defaultdict(dict)

for l in open("data/generated/combined-fusion-data.tsv"):
    sp = l.strip().split("\t")
    d = Data(*sp)

    # Skip samples that are not simulated data
    if d.sample.startswith("sim"):
        continue

    #score = 1 if d.entry == "truth" else d.score

    fk = fusion_key(d)
    #if d.entry == "truth":
        #spikeins.add(fk)

    fusions.add(fk)
    entries.add(d.entry)
    table[fk][d.entry] = 1 #score

headers = ["fusion"] + sorted(entries)
rows = []

for fk in sorted(fusions):
    row = ["_".join(fk)]
    rows.append(row)

    for entry in sorted(entries):
        called = table[fk].get(entry, 0)
        row.append(called)

print "\t".join(headers)
print "\n".join("\t".join(str(x) for x in r) for r in rows)
