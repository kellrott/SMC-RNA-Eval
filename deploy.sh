#!/bin/bash

# Usage Example:
# $ ./deploy.sh isoform 7367548 sim6 n1-standard-4

CONTEST_ID=$1
ENTRY_ID=$2
TUMOR_ID=$3
MACHINE_TYPE=$4
SBG=$5
TUMOR_LOWER=`echo $TUMOR_ID | tr "[[:upper:]]" "[[:lower:]]"`
RUN_SUFFIX=$CONTEST_ID-$ENTRY_ID-$TUMOR_LOWER
DISK_SIZE=300
TIMEOUT=126000 #35 hours in seconds
SNAPSHOT=smc-rna-base
ZONE=us-west1-b

PROJECT=isb-cgc-04-0029

gcloud compute disks create smc-rna-eval-disk-$RUN_SUFFIX \
--source-snapshot $SNAPSHOT --size $DISK_SIZE --project $PROJECT --zone $ZONE

gcloud compute instances create smc-rna-eval-$RUN_SUFFIX \
--disk name=smc-rna-eval-disk-$RUN_SUFFIX,auto-delete=yes,boot=yes \
--scopes storage-rw --machine-type $MACHINE_TYPE --project $PROJECT --zone $ZONE

sleep 60

gcloud compute --project $PROJECT ssh smc-rna-eval-$RUN_SUFFIX --zone $ZONE "nohup sudo sudo -i -u ubuntu bash /home/ubuntu/SMC-RNA-Eval/eval-entry-tumor.sh $CONTEST_ID $ENTRY_ID $TUMOR_ID $TIMEOUT $SBG > /opt/eval.out 2> /opt/eval.err &"
