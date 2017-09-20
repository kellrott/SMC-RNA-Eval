#!/usr/bin/env python

# Given an entry's CWL workflow, CWL inputs file, and a Google Storage output bucket,
# generate a TES task to run the entry's methods.

from __future__ import print_function
import os
import argparse
import json

parser = argparse.ArgumentParser()

parser.add_argument("cwl_file",
    help="CWL workflow file.")

parser.add_argument("job_file",
    help="CWL inputs JSON file.")

parser.add_argument("out_bucket",
    help="Google Storage bucket/path where outputs will be uploaded.")

parser.add_argument("--sbg",
    action="store_true", default=False,
    help="Flags this as a Seven Bridges workflow, "
    "which will be run using rabix instead of cwltool.")

# Script that loads an entry's docker tarballs into the host's docker daemon.
docker_load_script = """
for *.tar; do
    echo a;
    docker load -i $a;
done
"""

def strip_gs(path):
    """Strip "gs://" prefix from Google Storage URLs."""
    if path.startswith("gs://"):
        path = path[5:]
    return path

def collect_inputs(basedir, collection):
    """
    Returns a callback for walk_cwl_input_files() which collects
    the storage URLs and mapped host paths for use in a TES task.

    "basedir" is the base directory of the host path to map file into.
    "collection" is a list which will be modified to collect the TES input objects.
    """
    def cb(inputs):
        url = inputs["path"]
        # Strip "gs://"
        path = strip_gs(url)
        # Map path into base working directory
        path = os.path.join(basedir, path)

        tes_input = {
            "url": url,
            "path": path,
        }
        collection.append(tes_input)

        # Modify CWL input file object to have stripped + mapped file path.
        inputs["path"] = path
        
    return cb


def walk_cwl_input_files(inputs, callback):
    """
    Recursively walk over a CWL inputs tree, invoking "callback" for each file.
    """
    if isinstance(inputs, dict):
        if "class" in inputs and inputs["class"] == "File":
            callback(inputs)
            if 'secondaryFiles' in inputs:
                for i in out['secondaryFiles']:
                    walk_cwl_input_files(i, callback)
        else:
            for k, v in inputs.items():
                walk_cwl_input_files(v, callback)
    elif isinstance(inputs, list):
        for i in inputs:
            walk_cwl_input_files(i, callback)


def build_cmd(is_sbg, cwl_path, inputs_path):
    if is_sbg:
        # This is a Seven Bridges Genomics (SBG) CWL workflow, so run it with rabix.
        return ["rabix", "-v", cwl_path, "-i", inputs_path]
    else:
        return [
            "cwltool", "--disable-pull", "--custom-net", "none", "--leave-container",
            cwl_path, inputs_path
        ]


if __name__ == "__main__":
    
    args = parser.parse_args()
    
    with open(args.job_file) as handle:
   	job = json.loads(handle.read())
        
    # Working directory for CWL execution.
    cwl_work_dir = "/opt/cwl"
    # Directory to download data to.
    data_dir = "/opt/data"
    # Include CWL job file in TES input contents.
    cwl_inputs_host_path = os.path.join(cwl_work_dir, "inputs.json")
    # A little hacky, the CWL file path on the worker is based on the file path
    # given to this script.
    #
    # This is because CWL workflows don't have a consistent name.
    cwl_workflow_host_path = os.path.join(cwl_work_dir, os.path.basename(args.cwl_file))

    # TES task
    tes = {
        "inputs": [{
            "contents": json.dumps(job),
            "path": cwl_inputs_host_path,
        }],
        "outputs": [{
            "url": args.out_bucket,
            "path": cwl_work_dir,
            "type": "DIRECTORY",
        }],
        "executors": [{
            "image_name": "TODO",
            "cmd": ["/bin/bash", "-c", docker_load_script],
            "workdir": cwl_work_dir,
            "stdout": "/tmp/docker_load_stdout",
            "stderr": "/tmp/docker_load_stderr",
        }, {
            "image_name": "TODO",
            "cmd": build_cmd(args.sbg, cwl_workflow_host_path, cwl_inputs_host_path),
            "workdir": cwl_work_dir,
            "stdout": os.path.join(cwl_work_dir, "job.out"),
            "stderr": os.path.join(cwl_work_dir, "job.err"),
            "environ": {
                "TMPDIR": cwl_work_dir,
            },
        }],
        "resources": {
            "cpu_cores": 16,
            "preemptible": True,
            "ram_gb": 100,
        },
    }

    # Map the CWL inputs into TES inputs.
    # Also, modify the "job" to strip the "gs://" prefix and map paths into cwl_work_dir.
    walk_cwl_input_files(job, collect_inputs(data_dir, tes["inputs"]))

    print(json.dumps(tes, indent=4, sort_keys=True))
