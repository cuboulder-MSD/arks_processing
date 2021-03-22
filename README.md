# arks_processing

This repo contains code to retrieve and mint ARKs. For both scripts you will need to put your authorization token in ```auth_token```

**getARKs.py**

This script pulls down all ARKs that are currently in the server, and outputs them in a csv ```arks_[current date].csv```

```python getARKs.py```

**mintARKs.py**

This script mints ARKs based on URLs for items in the CUDL.

1. Export metadata from CUDL
2. Make sure 'Identifier ARK#1' is a column in the csv
3. On the CLI run ```python mintARKs.py inputfile.csv outputfile.csv.``` Output file can be whatever you would like to call it
4. Run the script on **test**
5. Make sure that no ARKs were overwritten between the input and output file
6. Run on **prod**
7. Check that ARKs in prod spreadsheet resolve correctly
8. Reupload csv to CUDL

**deleteARKs.py**

This script takes a csv of ARKs and deletes them.

1. Export metadata from CUDL
2. Make sure 'Identifier ARK#1' is a column in the csv
3. On the CLI run ```python deleteARKs.py inputfile.csv``` 
4. Check that ARKs in spreadsheet no longer resolve 
5. Remove AKRs from spreadsheet and reupload csv to CUDL

