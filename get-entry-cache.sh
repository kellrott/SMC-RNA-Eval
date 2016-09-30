#!/bin/bash

if [ ! -e entries ]; then
  mkdir entries
fi

gsutil cp -r gs://smc-rna-cache/$1/$2 entries/