from collections import defaultdict, namedtuple

Data = namedtuple("Data", """
    entry sample sample_name method user chrom1 start1 strand1 chrom2 start2 strand2 score
    g1_chrom1
    g1_start1
    g1_strand1
    g1_chrom2
    g1_start2
    g1_strand2
    g2_chrom1
    g2_start1
    g2_strand1
    g2_chrom2
    g2_start2
    g2_strand2
""")

fusion_key = lambda r: (r.g1_chrom1, r.g1_start1, r.g1_strand1, r.g2_chrom2, r.g2_start2, r.g2_strand2)

#spikein_key = lambda r: ("spikein", r.chrom1, r.start1, r.strand1, r.chrom2, r.start2, r.strand2)
#spikeins = set()

fusions = set()
entries = set()
truth_groups = set()
# rows are fusions, columns are entries
table = defaultdict(dict)
entry_methods = {}
entry_users = {}

for l in open("data/generated/combined-with-groups.tsv"):
    sp = l.strip().split("\t")
    d = Data(*sp)
    entry_methods[d.entry] = d.method
    entry_users[d.entry] = d.user

    #if not d.sample.startswith("sim"):
        #continue
    if "LNCap" not in d.sample_name:
        continue

    fk = fusion_key(d)
    if d.entry == "truth":
        truth_groups.add(fk)
        entry_methods["truth"] = "truth"
        entry_users["truth"] = "truth"

    fusions.add(fk)
    entries.add(d.entry)
    table[fk][d.entry] = 1

headers = ["entry", "fusion", "method", "user", "value"]
print "\t".join(headers)

for entry in sorted(entries):
    for fk in sorted(fusions):
        is_truth = fk in truth_groups
        fks = "_".join(fk)

        row = [entry, fks, entry_methods[entry], entry_users[entry]]
        called = table[fk].get(entry, 0)
        if called:
            if is_truth:
                row.append(2)
            else:
                row.append(1)
        else:
            row.append(0)

        print "\t".join(str(x) for x in row)
