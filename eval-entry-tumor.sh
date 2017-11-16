#!/bin/bash

CONTEST_ID=$1
ENTRY_ID=$2
TUMOR_ID=$3
#SBG=$4
BUCKET=gs://smc-rna-eval
RUN_SUFFIX=$CONTEST_ID-$ENTRY_ID-$TUMOR_LOWER
ENTRY_PATH=$HOME/SMC-RNA/entries/
INPUT_JOB=test.$TUMOR_ID.json
WORKDIR=$HOME/SMC-RNA/$ENTRY_ID/$TUMOR_ID

if [ $CONTEST_ID == 'fusion' ]; then
    export CONTEST_SIGN='FusionDetection'
else
    export CONTEST_SIGN='IsoformQuantification'
fi

if [ ! -e $ENTRY_PATH ]; then
    mkdir -p $ENTRY_PATH
fi

if [ ! -e $ENTRY_PATH/$ENTRY_ID ]; then
    gsutil cp -r $BUCKET/entries/$CONTEST_SIGN/$ENTRY_ID $ENTRY_PATH
    for a in $ENTRY_PATH/$ENTRY_ID/*.tar; do echo $a; docker load -i $a; done
    CWL_PATH=$(ls $ENTRY_PATH/$ENTRY_ID/*.cwl)
fi

$HOME/SMC-RNA-Eval/generate_job.py --data real --syn-table $HOME/SMC-RNA-Eval/syn.table $CONTEST_SIGN $CWL_PATH $TUMOR_ID > $WORKDIR/$INPUT_JOB

# For SBG entries only
if [ $SBG ]; then
	$HOME/SMC-RNA-Eval/sbg_job.py $CONTEST_ID $ENTRY_ID $INPUT_JOB $ENTRY_PATH/$ENTRY_ID/task.json > tmp_file
	mv tmp_file $INPUT_JOB
	$HOME/SMC-RNA-Eval/cwl-gs-tool --sbg $CWL_PATH $INPUT_JOB $BUCKET/output/$CONTEST_ID/$ENTRY_ID/$TUMOR_ID
else	
	$HOME/SMC-RNA-Eval/cwl-gs-tool --work-base $WORKDIR  $CWL_PATH#main $WORKDIR/$INPUT_JOB $BUCKET/real_output/$CONTEST_ID/$ENTRY_ID/$TUMOR_ID
fi

# Copy outputs to bucket
gsutil cp $WORKDIR/eval.* $BUCKET/real_output/$CONTEST_ID/$ENTRY_ID/$TUMOR_ID

# Clean up files
#rm -rf $WORKDIR
