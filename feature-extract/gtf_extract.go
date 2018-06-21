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

type TranscriptCounter struct {
  transcripts map[string]map[string]int
}

func NewTranscriptCounter() TranscriptCounter {
  return TranscriptCounter{map[string]map[string]int{}}
}

func (e *TranscriptCounter) AddFeature(feat *gff.Feature) {
  if feat.Feature == "exon" {
    trans_id := cleanQuotes(feat.FeatAttributes.Get("transcript_id"))
    gene_id := cleanQuotes(feat.FeatAttributes.Get("gene_id"))
    featLen := feat.FeatEnd - feat.FeatStart
    if x, ok := e.transcripts[gene_id]; ok {
      x[trans_id] = x[trans_id] + featLen
    } else {
      e.transcripts[gene_id] = map[string]int{trans_id:featLen}
    }
  }
}

func mapItemMax(m map[string]int) int {
  v := make([]int, 0, len(m))
  for  _, value := range m {
     v = append(v, value)
  }
  o := v[0]
  for _, i := range v {
    if i > o {
      o = i
    }
  }
  return o
}

func mapItemMin(m map[string]int) int {
  v := make([]int, 0, len(m))
  for  _, value := range m {
     v = append(v, value)
  }
  o := v[0]
  for _, i := range v {
    if i < o {
      o = i
    }
  }
  return o
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
  transCounter := NewTranscriptCounter()

  ws := sync.WaitGroup{}
  featChan := make(chan *gff.Feature, 1000)
  go func() {
    ws.Add(1)
    for feat := range featChan {
      exonCounter.AddFeature(feat)
      transCounter.AddFeature(feat)
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

  fmt.Printf("Gene\tExonCount\tTranscriptCount\tMaxTranscriptLength\tMinTranscriptLength\n")
  for k, _ := range exonCounter.counts {
    fmt.Printf("%s\t%d\t%d\t%d\t%d\n", k,
      exonCounter.counts[k],
      len(transCounter.transcripts[k]),
      mapItemMax(transCounter.transcripts[k]),
      mapItemMin(transCounter.transcripts[k]))
  }

}
