#!/usr/bin/env python

# Given an entry's CWL workflow, CWL inputs file, and a Google Storage output bucket,
# generate a TES task to run the entry's methods.

from __future__ import print_function
import os
import argparse
import json
import uuid

parser = argparse.ArgumentParser()

parser.add_argument("contest", choices=["isoform", "fusion"])

parser.add_argument("entry", help="entry ID, e.g 7150823")

parser.add_argument("tumor", help="tumor ID, e.g. sim46")

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
for a in *.tar; do
    echo $a;
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
        #path = strip_gs(url)
        # TODO hack here
        path = url.replace("gs://smc-rna-eval/", "")
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
    contest_name = "IsoformQuantification" if args.contest == "isoform" else "FusionDetection"
    name = contest_name + "/" + args.entry + "/" + args.tumor
    
    with open(args.job_file) as handle:
   	job = json.loads(handle.read())
        
    # Working directory for CWL execution.
    cwl_base_dir = os.path.join("/opt/cwl/work", uuid.uuid4().hex[5:], name)
    # Directory to download data to.
    #data_dir = os.path.join("/opt/cwl/data", args.name)
    # Include CWL job file in TES input contents.
    cwl_inputs_host_path = os.path.join(cwl_base_dir, "inputs.json")
    # A little hacky, the CWL file path on the worker is based on the file path
    # given to this script.
    #
    # This is because CWL workflows don't have a consistent name.
    # TODO hack here
    cwl_workflow_host_path = os.path.join(cwl_base_dir, "entries", contest_name, args.entry, os.path.basename(args.cwl_file))

    # TES task
    tes = {
        "name": name,
        "inputs": [{
            "url": "gs://smc-rna-eval/entries/" + contest_name + "/" + args.entry,
            "path": cwl_base_dir,
            "type": "DIRECTORY",
        }],
        "outputs": [{
            "url": args.out_bucket + name,
            "path": os.path.join(cwl_base_dir, "work"),
            "type": "DIRECTORY",
        }],
        "executors": [{
            "image_name": "TODO",
            "cmd": ["/bin/bash", "-c", docker_load_script],
            # TODO hack here
            "workdir": os.path.join(cwl_base_dir, "entries", contest_name, args.entry),
            "stdout": os.path.join(cwl_base_dir, "work", "docker_load_stdout"),
            "stderr": os.path.join(cwl_base_dir, "work", "docker_load_stderr"),
        }, {
            "image_name": "TODO",
            "cmd": build_cmd(args.sbg, cwl_workflow_host_path, cwl_inputs_host_path),
            "workdir": os.path.join(cwl_base_dir, "work"),
            "stdout": os.path.join(cwl_base_dir, "work", "job.out"),
            "stderr": os.path.join(cwl_base_dir, "work", "job.err"),
            "environ": {
                "TMPDIR": cwl_base_dir,
            },
        }],
        "resources": {
            "cpu_cores": 16,
            "preemptible": True,
            "ram_gb": 100,
        },
    }

    # Map the CWL inputs into TES inputs.
    # Also, modify the "job" to strip the "gs://" prefix and map paths into cwl_base_dir.
    walk_cwl_input_files(job, collect_inputs(cwl_base_dir, tes["inputs"]))
    tes["inputs"].append({
        "contents": json.dumps(job),
        "path": cwl_inputs_host_path,
    })

    print(json.dumps(tes, indent=4, sort_keys=True))
