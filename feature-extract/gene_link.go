package main

import (
    "os"
    "io"
    "fmt"
    "flag"
    "strings"
    "strconv"
    "compress/gzip"
    "github.com/biogo/biogo/io/featio/gff"
    "github.com/biogo/biogo/seq"
    "github.com/bmeg/golib"
)

type Loc struct {
  Chrome string
  Loc    int
  Strand seq.Strand
}

type Fusion struct {
  Method string
  Acc Loc
  AccGene string
  Don Loc
  DonGene string
}
func cleanQuotes(a string) string {
  return strings.Replace(a, "\"", "", -1)
}
func atoi(a string) int {
  a = strings.Replace(a, "\"", "", -1)
  i, _ := strconv.Atoi(a)
  return i
}

func posMatch(feat *gff.Feature, loc Loc) bool {
  if feat.SeqName != loc.Chrome {
    return false
  }
  if feat.FeatStrand != loc.Strand {
    return false
  }
  if loc.Loc > feat.FeatStart && loc.Loc < feat.FeatEnd {
    return true
  }
  return false
}

func toStrand(s string) seq.Strand {
  if s == "-" {
    return seq.Minus
  }
  return seq.Plus
}

func main() {
  flag.Parse()
  fusionPath := flag.Arg(0) //"fusion-analysis/combined-fusion-data.tsv"
  gtfPath :=flag.Arg(1) // "Homo_sapiens.GRCh37.75.gtf.gz"

  fusions := []*Fusion{}
  lines, _ := golib.ReadFileLines(fusionPath)
  for line := range lines {
    if len(line) > 0 {
      row := strings.Split(string(line), "\t")
      f := Fusion{ Method:row[0], Acc:Loc{Chrome:row[5], Loc:atoi(row[6]), Strand:toStrand(row[7])},
        Don:Loc{Chrome:row[8], Loc:atoi(row[9]), Strand:toStrand(row[10])},
      }
      fusions = append(fusions, &f)
    }
  }

  freader, err := os.Open(gtfPath)
  if err != nil {
      fmt.Printf("Error: %s\n", err)
  }
  reader, _ := gzip.NewReader(freader)
  featReader := gff.NewReader(reader)

  for {
      i, err := featReader.Read()
      if err == io.EOF {
          break
      }
      feat := i.(*gff.Feature)
      if feat.Feature == "gene" {
        for _, k := range fusions {
          if posMatch(feat, k.Acc) {
            k.AccGene = cleanQuotes(feat.FeatAttributes.Get("gene_id"))
          }
          if posMatch(feat, k.Don) {
            k.DonGene = cleanQuotes(feat.FeatAttributes.Get("gene_id"))
          }
        }
      }
  }
  freader.Close()

  fmt.Printf("FusionName\tGene1Name\tGene2Name\n")
  for _, k := range fusions {
    acc := fmt.Sprintf("%s_%d_%s", k.Acc.Chrome, k.Acc.Loc, k.Acc.Strand)
    don := fmt.Sprintf("%s_%d_%s", k.Don.Chrome, k.Don.Loc, k.Don.Strand)
    fmt.Printf("%s_%s_%s\t%s\t%s\n", k.Method, acc, don, k.AccGene, k.DonGene)
  }

}
