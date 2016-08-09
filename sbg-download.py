#!/usr/bin/env python

import os
import json
import argparse
import requests


BASE_URL = "https://cgc-api.sbgenomics.com/v2/"

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--token")
    parser.add_argument("task_id")
    parser.add_argument("outdir")
    
    args = parser.parse_args()

    if not os.path.exists(args.outdir):
        os.mkdir(args.outdir)
    
    task = requests.get(BASE_URL + "tasks/" + args.task_id, headers={"X-SBG-Auth-Token" : args.token} ).json()
    with open(os.path.join(args.outdir, "task.json"), "w") as handle:
        handle.write( json.dumps(task, indent=4) )
    
    cwl = requests.get(BASE_URL + "apps/" + task['app'] + "/raw", headers={"X-SBG-Auth-Token" : args.token}).json()
    with open(os.path.join(args.outdir, "submission.cwl"), "w") as handle:
        handle.write( json.dumps(cwl, indent=4) )
    
    for k, v, in task['inputs'].items():
        if isinstance(v,dict) and 'File' == v.get('class', None):
            file_info = requests.get("https://cgc-api.sbgenomics.com/v2/files/%s" % (v['path']), headers={"X-SBG-Auth-Token" : args.token}).json()            
            file_download = requests.get("https://cgc-api.sbgenomics.com/v2/files/%s/download_info" % (v['path']), headers={"X-SBG-Auth-Token" : args.token}).json()
            print "Downloading %s from %s" % (file_info['name'], file_download['url'])
            r = requests.get(file_download['url'], headers={"X-SBG-Auth-Token" : args.token}, stream=True)
            with open(os.path.join(args.outdir, file_info['name']), 'wb') as f:
                for chunk in r.iter_content(chunk_size=1024): 
                    if chunk:
                        f.write(chunk)
                