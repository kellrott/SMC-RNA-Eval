#!/bin/bash

CONTEST_ID=$1
ENTRY_ID=$2
TUMOR_ID=$3
SBG=$4
WORKDIR=$HOME/SMC-RNA/$ENTRY_ID/$TUMOR_ID

if [ ! -e $WORKDIR ]; then
    mkdir -p $WORKDIR
fi

bash /home/ubuntu/SMC-RNA-Eval/eval-entry-tumor.sh $CONTEST_ID $ENTRY_ID $TUMOR_ID $SBG > $WORKDIR/eval.out 2> $WORKDIR/eval.err &
