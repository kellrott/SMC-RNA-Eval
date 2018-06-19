package main

import (
    "os"
    "io"
    "sync"
    "fmt"
    "strings"
    "strconv"
    "compress/gzip"
    "github.com/biogo/biogo/io/featio/gff"
    "github.com/bmeg/golib"
)

type Loc struct {
  Chrome string
  Loc    int
  Strand string
}

type Fusion struct {
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
  if loc.Loc > feat.FeatStart && loc.Loc < feat.FeatEnd {
    return true
  }
  return false
}

type ExonCounter struct {
  counts map[string]int
}

func NewExonCounter() ExonCounter {
  return ExonCounter{map[string]int{}}
}

func (e *ExonCounter) AddFeature(feat *gff.Feature) {
  if feat.Feature == "exon" {
    exon_num := atoi(feat.FeatAttributes.Get("exon_number"))
    id := cleanQuotes(feat.FeatAttributes.Get("gene_id"))
    if x, ok := e.counts[id]; ok {
      if exon_num > x {
        e.counts[id] = exon_num
      }
    } else {
      e.counts[id] = exon_num
    }
  }
}

func main() {

  fusions := []*Fusion{}

  lines, _ := golib.ReadFileLines("fusion-analysis/combined-fusion-data.tsv")
  for line := range lines {
    if len(line) > 0 {
      row := strings.Split(string(line), "\t")
      f := Fusion{ Acc:Loc{Chrome:row[5], Loc:atoi(row[6]), Strand:row[7]},
        Don:Loc{Chrome:row[8], Loc:atoi(row[9]), Strand:row[10]},
      }
      fusions = append(fusions, &f)
    }
  }

  gtfPath := "Homo_sapiens.GRCh37.75.gtf.gz"
  freader, err := os.Open(gtfPath)
  if err != nil {
      fmt.Printf("Error: %s\n", err)
  }
  reader, _ := gzip.NewReader(freader)
  featReader := gff.NewReader(reader)

  exonCounter := NewExonCounter()

  ws := sync.WaitGroup{}
  featChan := make(chan *gff.Feature, 1000)
  go func() {
    ws.Add(1)
    for feat := range featChan {
      exonCounter.AddFeature(feat)
    }
    ws.Done()
  }()

  for {
      i, err := featReader.Read()
      if err == io.EOF {
          break
      }
      feat := i.(*gff.Feature)
      featChan <- feat
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
  close(featChan)
  freader.Close()
  ws.Wait()

  for _, k := range fusions {
    acc := fmt.Sprintf("%s_%d_%s", k.Acc.Chrome, k.Acc.Loc, k.Acc.Strand)
    don := fmt.Sprintf("%s_%d_%s", k.Don.Chrome, k.Don.Loc, k.Don.Strand)
    val := exonCounter.counts[k.AccGene]
    fmt.Printf("%s_%s\tdonor_exon_count\t%d\n", acc, don, val)
  }

}
