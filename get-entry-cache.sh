#!/bin/bash

if [ ! -e entries ]; then
  mkdir entries
fi

if [ $1 == "isoform"]; then
  gsutil cp -r gs://smc-rna-cache/IsoformQuantification/$2 entries/
fi

if [ $1 == "fusion"]; then
  gsutil cp -r gs://smc-rna-cache/FusionDetection/$2 entries/
fi