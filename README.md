# SMC-RNA-Eval

Google tools:
https://cloud.google.com/sdk/docs/quickstart-linux

wget https://dl.google.com/dl/cloudsdk/channels/rapid/downloads/google-cloud-sdk-128.0.0-linux-x86_64.tar.gz
tar xvzf google-cloud-sdk-128.0.0-linux-x86_64.tar.gz
. google-cloud-sdk/path.bash.inc
gcloud auth login


Other code
==========

git clone https://github.com/Sage-Bionetworks/SMC-RNA-Challenge.git

bash SMC-RNA-Challenge/install-ubuntu.sh


Docker Install
==============

sudo usermod -aG docker $USER


Get an entry
============

mkdir data

./get-entry-cache.sh isoform 7150898
cd entries/7150898/

Load Entries
`for a in *.tar; do docker load -i $a; done`

../../SMC-RNA-Challenge/script/dream_runner.py inputs sim1 isoform_1471603893_merged.cwl isoform --dir ../../data





## DREAM_Evaluation.py
Usage:

	python DREAM_Evaluation.py -t <task_id: str> -p <eval-project: str> -f <eval_fq_1.fq.gz: str> <eval_fq_2.fq.gz: str>


For example:

	python DREAM_Evaluation.py -t "752c1086-9d42-445f-a59e-38020a0857c9" -p "smc-rna-admin/evaluation-project" -f "eval_1.fq.gz" "eval_2.fq.gz"

where:

- **"752c1086-9d42-445f-a59e-38020a0857c9"** is the task ID submitted by the DREAM Challenge participant (smc-rna-admin is invited to this project)
- **"smc-rna-admin/evaluation-project** is a project belonging to smc-rna-admin and to which participants do *not* have access. This is where the submission will be evaluated on withheld data
- **"eval\_\*.fq.gz"** are filenames for paired-end fastqs in the **"smc-rna-admin/evaluation-project**



## Link fusions to genes
```
go run feature-extract/gene_link.go analysis/fusion-analysis/combined-fusion-data.tsv Homo_sapiens.GRCh37.75.gtf.gz > analysis/fusion-analysis/fusion-gene-link.tsv
```

## GTF Feature Extraction
```
go run feature-extract/gtf_extract.go Homo_sapiens.GRCh37.75.gtf.gz > gene_features.tsv
```

```
mkdir analysis
synapse get -r syn9712104 --downloadLocation analysis/
```

## Analysis matrix loading

Add GID
```
cat analysis/fusion-analysis/combined-fusion-data.tsv | awk -F '\t' '{print $1 ":" $2 ":" $6 ":" $7 ":" $8 ":" $9 ":" $10 ":" $11 "\t" $0}' > analysis/fusion-analysis/combined-fusion-data.tsv.gid
```
Load Matrix
```
load_matrix.py smc-rna analysis/fusion-analysis/combined-fusion-data.tsv.gid --row-label Fusion --columns gid entry_id sample_id sample_name method user chrom_1 start_1 strand_1 chrom_2 start_2 strand_2 score -e '{sample_id}' sample -e '{entry_id}' entry

load_matrix.py smc-rna analysis/fusion-analysis/gene_features.tsv --row-label Gene

load_matrix.py smc-rna analysis/fusion-analysis/fusion-gene-link.tsv --no-vertex -e '{Gene1Name}' gene1 -e '{Gene2Name}' gene2

load_matrix.py smc-rna analysis/entry_list/fusion/fusion_list.tsv --row-label 'Entry'

load_matrix.py smc-rna analysis/fusion-analysis/transcript_features.tsv --columns gene_id gid gc_content transcript_len --index-col 1 -e {gene_id} gene --row-label Transcript
```
