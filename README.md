# SMC-RNA-Eval

## DREAM_Evaluation.py
Usage:
	
	python DREAM_Evaluation.py -t <task_id: str> -p <eval-project: str> -f <eval_fq_1.fq.gz: str> <eval_fq_2.fq.gz: str>


For example:

	python DREAM_Evaluation.py -t "752c1086-9d42-445f-a59e-38020a0857c9" -p "smc-rna-admin/evaluation-project" -f "eval_1.fq.gz" "eval_2.fq.gz"
	
where: 

- **"752c1086-9d42-445f-a59e-38020a0857c9"** is the task ID submitted by the DREAM Challenge participant (smc-rna-admin is invited to this project)
- **"smc-rna-admin/evaluation-project** is a project belonging to smc-rna-admin and to which participants do *not* have access. This is where the submission will be evaluated on withheld data
- **"eval\_\*.fq.gz"** are filenames for paired-end fastqs in the **"smc-rna-admin/evaluation-project**
