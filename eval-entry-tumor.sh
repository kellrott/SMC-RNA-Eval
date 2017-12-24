#!/bin/bash

CONTEST_ID=$1
ENTRY_ID=$2
TUMOR_ID=$3
TIMEOUT=$4
SBG=$5
BUCKET=gs://smc-rna-eval
RUN_SUFFIX=$CONTEST_ID-$ENTRY_ID-$TUMOR_LOWER
ENTRY_PATH=cache/smc-rna-eval/entries/
INPUT_JOB=test.$TUMOR_ID.json

if [ $CONTEST_ID == 'fusion' ]; then
    export CONTEST_SIGN='FusionDetection'
else
    export CONTEST_SIGN='IsoformQuantification'
fi

mkdir -p $ENTRY_PATH
gsutil cp -r $BUCKET/entries/$CONTEST_SIGN/$ENTRY_ID $ENTRY_PATH
for a in cache/smc-rna-eval/entries/$ENTRY_ID/*.tar; do echo $a; docker load -i $a; done
CWL_PATH=$(ls $ENTRY_PATH/$ENTRY_ID/*.cwl)

./SMC-RNA-Eval/generate_job.py --data real --syn-table SMC-RNA-Eval/syn.table $CONTEST_SIGN $CWL_PATH $TUMOR_ID > $INPUT_JOB

# For SBG entries only
if [ $SBG ]; then
        print "SBG entry"
	./SMC-RNA-Eval/sbg_job.py $CONTEST_ID $ENTRY_ID $INPUT_JOB $ENTRY_PATH/$ENTRY_ID/task.json > tmp_file
	mv tmp_file $INPUT_JOB
	./SMC-RNA-Eval/cwl-gs-tool --sbg $CWL_PATH $INPUT_JOB $BUCKET/real_output/$CONTEST_ID/$ENTRY_ID/$TUMOR_ID
else	
	./SMC-RNA-Eval/cwl-gs-tool $CWL_PATH#main $INPUT_JOB $BUCKET/real_output/$CONTEST_ID/$ENTRY_ID/$TUMOR_ID
fi

# Copy outputs to bucket
gsutil cp /opt/eval.* $BUCKET/real_output/$CONTEST_ID/$ENTRY_ID/$TUMOR_ID

# Shutdown
if [ "$4" != "" ]; then
  sudo poweroff
fi

# graph agent event assembler
