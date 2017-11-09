Download fusion output data
-------------------------------

If data is in gs://smc-rna-eval/output/fusion, run `gsutil cp -r gs://smc-rna-eval/output/fusion downloaded-data`


Install Python dependencies
----------------------------

`pip install -r requirements.txt`


Run the code
-------------

`python find-adjacent.py`


Gotchas
--------

- the code is built to expect a specific file path format:
  `downloaded-data/fusion/{entry_ID}/{tumor_ID}/*.bedpe`
