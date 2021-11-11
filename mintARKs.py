import requests, json, csv, sys, uuid
from datetime import datetime

def chooseURL():
    urls = {"prod": "https://libapps.colorado.edu/ark:/", "test": "https://test-libapps.colorado.edu/ark:/"}
    user_response = input("Do you want to run on prod or test? [prod/test]:").lower()
    if user_response not in urls:
        raise RuntimeError("%s is not a valid env" % user_response)

    url = urls[user_response]
    return url




def getARK(url, luna_url, title, rights, type, filename, user):
    auth_token = ''


    data={"resolve_url": luna_url ,"metadata":{"mods": {"titleInfo":[{"title": title}],"typeOfResource": type, "identifier": filename, "accessCondition": rights}},"generated_by": user,"status": "active"}
    # print(data)

    headers={"Content-Type":"application/json","Authorization":"Token " + auth_token}

    req= requests.post(url,json.dumps(data),headers=headers)

    rjson = req.json()

    print(req.json())

    ark = rjson['results'][0]['ark']

    return ark
    # print(ark)


def main():
    # Grab our infile_path and outfile_path from the cli
    infile_path = sys.argv[1]
    outfile_path = sys.argv[2]

    #if utf-8 doesnt work, try iso-8859-1
    with open(infile_path, encoding='utf-8', newline='' ) as csvfile, open(outfile_path, "w",  encoding='utf-8') as outfile:
         reader = csv.DictReader(csvfile)
         fields = reader.fieldnames
         # fields.append('Identifier ARK')
         writer = csv.DictWriter(outfile, fieldnames=fields)
         writer.writeheader()
         user = input("enter your last name:").lower()
         batchRef = input('enter a collection reference (e.g. snow, nsidc, zss, bent-hyde):') + '_' + str(uuid.uuid4())

         url = chooseURL()

         for row in reader:
             # print(row)
             if len(row['Identifier ARK#1']) == 0:
                 # print(row['Title#1'])
                 luna_url = row['lnexp_PAGEURL']
                 title = row['Title#1']
                 rights = row['Access Condition#1']
                 type = row['Resource Type#1']
                 filename = row['Identifier#1']
                 ark = getARK(url, luna_url, title, rights, type, filename, user)
                 row['Identifier ARK#1'] = 'https://ark.colorado.edu/ark:/' + ark
                 writer.writerow(row)
             else:
                 writer.writerow(row)


# make this a safe-ish cli script
if __name__ == '__main__':
    main()
