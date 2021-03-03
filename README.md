# arks_processing

This repo contains code to retrieve and mint ARKs. For both scripts you will need to put your authorization token in ```auth_token```

**getARKs.py**

This script pulls down all ARKs that are currently in the server, and outputs them in a csv ```arks_[current date].csv```

```python getARKs.py```

**mintARKs.py**

This script mints ARKs based on URLs for items in the CUDL.

1. Export metadata from CUDL.
2. Make sure 'Identifier ARK' is a column in the csv.
3. On the CLI run ```python mintARKs.py imputfile.csv outputfile.csv.``` Output file can be whatever you would like to call it.
4. Run the script on **test**, then on **prod** when test is running successfully.
5. Reupload csv to CUDL
