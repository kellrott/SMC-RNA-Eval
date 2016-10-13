#!/bin/bash

CONTEST_ID=$1
ENTRY_ID=$2
TUMOR_ID=$3
TUMOR_LOWER=`echo $TUMOR_ID | tr "[[:upper:]]" "[[:lower:]]"`
DISK_SIZE=300
TIMEOUT=126000 #35 hours in seconds
MACHINE_TYPE=n1-standard-4
SNAPSHOT=smc-rna-base
ZONE=us-west1-b

PROJECT=isb-cgc-03-0004

gcloud compute disks create smc-rna-eval-disk-$CONTEST_ID-$ENTRY_ID-$TUMOR_LOWER \
--source-snapshot $SNAPSHOT --size $DISK_SIZE --project $PROJECT --zone $ZONE

gcloud compute instances create smc-rna-eval-$CONTEST_ID-$ENTRY_ID-$TUMOR_LOWER \
--disk name=smc-rna-eval-disk-$CONTEST_ID-$ENTRY_ID-$TUMOR_LOWER,auto-delete=yes,boot=yes \
--scopes storage-rw --machine-type $MACHINE_TYPE --project $PROJECT --zone $ZONE

sleep 60

gcloud compute --project $PROJECT ssh smc-rna-eval-$CONTEST_ID-$ENTRY_ID-$TUMOR_LOWER "nohup sudo sudo -i -u ubuntu bash /home/ubuntu/SMC-RNA-Eval/eval_entry_tumor.sh $ENTRY_ID $TUMOR_ID $TIMEOUT > /tmp/eval.out 2> /tmp/eval.err &" 
