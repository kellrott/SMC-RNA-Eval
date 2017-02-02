# SMC-RNA-Eval

This code is used to test submissions to the [ICGC-TCGA DREAM Somatic Mutation Calling - RNA Challenge](https://www.synapse.org/#!Synapse:syn2813589/wiki/401435) (SMC-RNA).

This code is intended to be run on Google Compute Engine (GCE) and presumes access to Google Cloud Storage (GS) buckets and Synapse storage related to the challenge.

The challenge works like this:

1. Public **training data** is generated.
2. Participants use that training data to **develop and submit** tools to the challenge. 
3. Submissions are **tested** against private tumor data and produces results.
4. Results from the tests are **evaluated statistically** and posted to a public leaderboard.

Each tool does **isoform** quantification and/or **fusion** detection.

Repos:

[alliecreason/rnaseqSim](https://github.com/alliecreason/rnaseqSim) handles #1

[Sage-Bionetworks/SMC-RNA-Challenge](https://github.com/Sage-Bionetworks/SMC-RNA-Challenge) does #2 and #4

This repo does #3


Quick start
===========

`install.sh` installs dependencies. You probably don't need it. There's probably already a VM snapshot in GCE.

`./deploy.sh isoform 7367548 sim6 n1-standard-4` would test the `isoform` quantification of submission `7367548` using the `sim6` test data on a `n1-standard-4` GCE VM. This will create a GCE instance, download data, and run the CWL workflow for the given submission and test data.

You can edit `deploy.sh` to configure variables for snapshot, zone, timeout, disk size, etc.


More detail
===========

A quick summary of each script. See each script for more details:

- `deploy.sh` is the top level and is described above. It calls `eval-entry-tumor.sh`.
- `eval-entry-tumor.sh` will:
  - download data
  - load docker images
  - prepare the CWL inputs file
  - run the CWL workflow
  - upload results
  - optionally power off the VM
- `generate-job.py` prepares the CWL inputs file for the test data.
- `cwl-gs-tool` runs the CWL workflow
