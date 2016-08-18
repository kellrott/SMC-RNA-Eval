#!/usr/bin/env python
# coding: utf-8
# Evaluating Submissions to the SMC-RNA DREAM Challenge on the Seven Bridges CGC
# This will go over how to use the API to go from a Task ID to having the submitted application and reference files cached in a new project, then rerunning it with evaluation data. The evaluation data and new project are mocks which can be replaced for the actual evaluation.
from __future__ import print_function
from os import environ
from datetime import datetime
import sevenbridges as sbg
import argparse
from dream_helpers import *
import time
import pprint
pp = pprint.PrettyPrinter(indent=4)

def check_task_status(task_object):
    if task_object.status == "COMPLETED":
        print("\n'{}' is completed.".format(task_object.name))
    else:
        print("WARNING: '{}' incomplete. Current status: {}".format(task_object.name, task_object.status))

def replace_file_dicts_with_objects(api, project, task_inputs):
    for k, v in task_inputs.iteritems():
        if isinstance(v, dict) and v["class"] == "File":
            task_inputs[k] = get_file_by_name(api, project, v["name"])
    return task_inputs

def empty_tumor_ports_by_id(task_inputs):
    for k, v in task_inputs.iteritems():
        if "TUMOR_FASTQ" in k:
            task_inputs[k] = "ID indicates TUMOR_FASTQ"
    return task_inputs

def empty_tumor_ports_by_label(app_object, task_inputs):
    for port in app_object.raw['inputs']:
        if "label" in port and "TUMOR_FASTQ".lower() in port['label'].lower():
            task_inputs[port['id'].split("#")[-1]] = "Label indicates TUMOR_FASTQ"
    return task_inputs

def get_task_input_object(api, task_id):
    task_object = api.tasks.get(task_id)
    
    # Get required objects
    app_object = api.apps.get(task_object.app)
    project = api.projects.get(task_object.project)
    
    # Check if task is successfully completed
    check_task_status(task_object)
    
    # Remove keys where value is None/NoneType
    task_inputs = dict((str(k), v) for k, v in task_object.inputs.iteritems() if v)

    # Replace the values that represent files (currently dicts) with File object
    task_inputs = replace_file_dicts_with_objects(api, project, task_inputs)

    # Empty values where TUMOR_FASTQ is in ID or label
    task_inputs = empty_tumor_ports_by_id(task_inputs)
    task_inputs = empty_tumor_ports_by_label(app_object, task_inputs)

    # print("Task_inputs: ")
    # pp.pprint(task_inputs)
    return task_inputs

def copy_files_to_evaluation_project(api, task_object, evaluation_project, task_inputs):
    """
    Copy files
     - note that identical files in multiple projects have UNIQUE IDs
     - cannot check to see if the file exists already by ID
     - so we create a new filename that should be unique to the submitter and check on that
    """
    
    # Initialize new files and new_task_inputs
    new_files = []
    new_task_inputs = task_inputs.copy() # let's not change the original object
    
    # 1. Iterate over the keys and values in task_inputs
    # 2. Check if it's a file
    # 3. Create new_filename
    # 4. If file by new_filename not in eval project, copy
    # 5. Replace values in new_task_inputs with the new, copied files
    # 6. If files were copied, get new_files and new_input_object
    for k, obj in task_inputs.iteritems():
        if obj.__class__.__name__ == "File":
            submitters_username = task_object.created_by
            new_filename = "_".join([submitters_username, obj.name]) # e.g gauravdream_rsem_index.tar.gz
            # new_filename = "_".join(["test", obj.name]) # debugging only
            # Check if the file with that filename already exists in evaluation project (check_file)
            # - if it does,     replace the value in the input object with that file
            # - if it does not, copy to new project and set value in input object
            check_file = get_file_by_name(api, project=evaluation_project, filename=new_filename)
            if check_file:
                print("\nWARNING: '{}' already in '{}' project.".format(new_filename, evaluation_project))
                new_task_inputs[k] = check_file # replace file object with object in new project
            else:
                new_file = obj.copy(project=evaluation_project, name=new_filename)
                new_task_inputs[k] = new_file # replace old file object with new one
                print("\n'{}' copied to '{}' project \n\twith new filename: '{}'".format(obj.name, evaluation_project, new_filename))
                print("New file ID: {}".format(new_file.id))
                new_files.append(new_file)
    # If there are new_files, return them and the new task inputs object, else warn and return old inputs object
    if new_files:
        return new_files, new_task_inputs
    else:
        print("No files copied.")
        return None, new_task_inputs

def copy_app_to_evaluation_project(api, task_object, evaluation_project):
    """
    Copy the tool to your project
    - we will take the app and rename it
    - this will cache the app and prevent the user from potentially making changes after submission
    - to do this, we grab the raw CWL, modify the label to rename it, and set a new id  with that label
    - the label is the submitter's username, the original label, and then the version/revision number (sep="-")
    - this will make sure that each submission is uniquely versioned
    - we will also do error checking for duplicate apps
    """    
    # Get submission info
    submission_app = api.apps.get(task_object.app) # get app_object using task_object
    submission_username = task_object.created_by
    
    # Grab RAW CWL & modify label and id
    evaluation_app = submission_app.raw
    evaluation_app['label'] = "_".join([submission_username, evaluation_app['label'], str(submission_app.revision)])
    # evaluation_app['label'] = "dream_testing_this_code" # debugging only
    evaluation_app_id = "/".join([evaluation_project, evaluation_app['label']])

    # Try to install the new app -- if it fails, return the app object in the new project
    try:
        installed_app = api.apps.install_app(raw=evaluation_app, id=evaluation_app_id)
        print("\n'{}' app from '{}' installed in '{}' project.".format(evaluation_app['label'], submission_username, evaluation_project))
        return installed_app
    except:
        print("\n'{}' app already exists in the '{}' project. Returning app in evaluation project.".format(evaluation_app['label'], evaluation_project))
        return get_app_by_name(api, project=evaluation_project, app_name=evaluation_app['label'])

def insert_evaluation_fastqs_into_object(evaluation_fastqs, task_inputs):
    """
    Insert evaluation fastqs in input_object
    """
    new_task_inputs = task_inputs.copy()
    fastqs = list(evaluation_fastqs)
    while fastqs:
        for k, val in new_task_inputs.iteritems():
            if type(val) == str and "TUMOR_FASTQ" in val: 
                new_task_inputs[k] = fastqs[-1]
                fastqs.pop()
    return new_task_inputs

def create_task(evaluation_fastqs, project, task_inputs, app_object, debug, run_opt):

    # Create individualized task names with sample ID and current time
    sample_id = evaluation_fastqs[0].metadata['sample_id']
    current_time = datetime.now().strftime("%m-%d-%Y %H:%M:%S")
    task_name = "{}_{} - {}".format(app_object.name, sample_id, current_time)

    # print the final input object (by names)
    print("\nFinal inputs (by name): ")
    names_dict = task_inputs.copy()
    for k, v in names_dict.iteritems():
        if v.__class__.__name__ == "File":
            names_dict[k] = v.name
    pp.pprint(names_dict)

    # Create the task
    if not debug:
        new_task = api.tasks.create(name=task_name, 
                         project=project,
                         app=app_object, 
                         inputs=task_inputs,
                         run=run_opt) # IMPORTANT! set run=True if you want to run, not just draft the tasks
        if run_opt == False:
            print("\nTask is drafted: {}".format(task_name))
            return new_task

        else:
            print("\nTask created: {}".format(task_name))
            return new_task

if __name__ == "__main__":
    # parser
    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--task-id", type=str, help="Alphanumeric Task ID from SBG-CGC")
    parser.add_argument("-p", "--project", type=str, help="Evaluation Project")
    parser.add_argument("-v", "--verbose", action='store_true', default=False)
    parser.add_argument("-d", "--debug", action='store_true', default=False)
    parser.add_argument("-r", "--draft-only", dest='run_opt', action='store_false', default=True)
    parser.set_defaults(run_opt=True)

    args = parser.parse_args()

    # get args
    task_id = args.task_id
    eval_project = args.project
    verbose = args.verbose
    debug = args.debug
    run_opt = args.run_opt

    # get api
    api = sbg.Api(config=sbg.Config(url=environ['API_URL'], token=environ['AUTH_TOKEN']))

    # get task object
    validation_task = api.tasks.get(task_id) # task_object

    # get input object
    input_object = get_task_input_object(api, task_id)

    # copy files to evaluation project and transform new input object (has new project file ids)
    new_files, new_input_object = copy_files_to_evaluation_project(api, validation_task, eval_project, input_object)

    # Print: new filenames
    if verbose and new_files: 
        print("\nNew filenames in {}:".format(eval_project))
        print(*[f.name for f in new_files], sep="\n")  
    if verbose:
        print("\nNew input object:")
        pp.pprint(new_input_object)

    # grab the new app (if already exists, get app object in evaluation project)
    new_app = copy_app_to_evaluation_project(api, validation_task, evaluation_project=eval_project)

    # grab evaluation fastqs here by metadata 
    eval_fastq_metadata = {"sample_id":"evalabc123"} # just a dummy sample_id
    eval_fastqs = split_fastqs_tuple(fastqs=get_files_by_metadata(api, eval_project, eval_fastq_metadata))[0]
    if verbose:
        print(*[fq.name for fq in eval_fastqs], sep="\n")
        pp.pprint(new_input_object)

    # insert the evaluation fastqs into the input_object (modify cmd to loop and create multiple tasks)
    # IMPORTANT: this step will loop infinitely if the app used it outside the scope of the DREAM Challenge
    #               - no fastqs in input ports
    #               - no TUMOR_FASTQ in labels
    #               - modifying next to be useful for non-paired-end fastq tasks.
    new_input_object = insert_evaluation_fastqs_into_object(eval_fastqs, new_input_object)

    # THE MAIN EVENT -- run the task (or print task info if debugging)
    if not debug:
        print("Preparing task execution.")
        new_task = create_task(evaluation_fastqs=eval_fastqs, 
                                project=eval_project, 
                                task_inputs=new_input_object, 
                                app_object=new_app, 
                                debug=debug, 
                                run_opt=run_opt)
