# arks_processing

This repo contains code to retrieve and mint ARKs. For both scripts you will need to put your authorization token in ```auth_token```

You can find the auth token here https://libapps.colorado.edu/api/user/

To see what metadata an ARK has, use this template https://libapps.colorado.edu/ark:/47540/[id]/detail

*Note: You can only mint for collections that have a 1:1 relationship between record and item in luna. It will not work if one record is linked to multiple items.*

*Do not mint for Charles F. Snow, Colorado Historical Maps, or Publishers Bindings.*

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

**testARKs.py**

This script takes a list of ARKs and tests them for HTTP errors. Prints results to terminal.

1. Run ```python getARKs.py```
2. Run ```python testARKs.py [output file from step 1]```

**updateARKs.py**

Takes new URLs and replaces the old resolve URLs on the server so that the ARK can resolve to the new one. Requires a csv with the arks and the new URLs. The csv must have two columns: ```Identifier ARK#1``` which contains the ark that needs to be updated, and ```lnexp_PAGEURL``` which contains the new URL that the ARK will resolve to. This one can only be run on production

1. Run ```python updateARKs.py [csv file] ```
