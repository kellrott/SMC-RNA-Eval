package main

import (
    "os"
    "io"
    "sync"
    "fmt"
    "flag"
    "strings"
    "strconv"
    "compress/gzip"
    "github.com/biogo/biogo/io/featio/gff"
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

  flag.Parse()

  gtfPath := flag.Arg(0)
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
  }
  close(featChan)
  freader.Close()
  ws.Wait()

  for k, v := range exonCounter.counts {
    fmt.Printf("%s\t%d\n", k, v)
  }

}
