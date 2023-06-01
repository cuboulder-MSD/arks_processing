#python3
#this script takes URLs and replaces the ones on the server so the ARKs can resolve correctly

import requests, json, csv, sys
from jsonpatch import JsonPatch

url = "https://libapps.colorado.edu/ark:/"
auth_token = ''
headers={"Content-Type":"application/json","Authorization":"Token " + auth_token}

#csv file with the urls you want to use
infile_path= sys.argv[1]


with open(infile_path, encoding='utf-8', newline='' ) as csvfile:
	reader = csv.DictReader(csvfile)
	for row in reader:
		ark = row['Identifier ARK#1']
		itemURL = row['lnexp_PAGEURL']
		
		arkurl = ark +'/detail?format=json'
		
		req = requests.get(arkurl,headers=headers).json()
		
    #create the patch with updated url
		patchurl = JsonPatch([{"op": "replace", "path":"/resolve_url", "value": itemURL}])
    #idk what this does tbh
		applyPatch = patchurl.apply(req, in_place=True)
		
		#the patch is actually applied here
		updatedUrl = requests.put(arkurl, headers=headers, data=json.dumps(applyPatch)).json()
		print(updatedUrl)

