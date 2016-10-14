#!/bin/bash

CONTEST_ID=$1
ENTRY_ID=$2
TUMOR_ID=$3
TIMEOUT=$4
BUCKET=gs://dream-smc-rna
RUN_SUFFIX=$CONTEST_ID-$ENTRY_ID-$TUMOR_LOWER

if [ $CONTEST_ID == 'fusion' ]; then
    export CONTEST_SIGN='FusionDetection'
else
    export CONTEST_SIGN='IsoformQuantification'
fi

gsutil cp -r $BUCKET/entries/$CONTEST_SIGN/$ENTRY_ID cache/smc-rna-eval/entries/
for a in cache/smc-rna-eval/entries/$ENTRY_ID/*.tar; do echo $a; docker load -i $a; done

