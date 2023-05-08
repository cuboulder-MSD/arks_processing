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


def get_value(reader, row, fieldnames):
    for fieldname in fieldnames:
        if fieldname in reader.fieldnames and row.get(fieldname):
            return row[fieldname]
    return ''
    
def get_title(reader, row):
    return get_value(reader, row, ['Title#1', 'Title', 'County Set Name#1', 'County Set Name', 'Work Title#1', 'Work Title'])

def get_rights(reader, row):
    return get_value(reader, row, ['Access Condition#1', 'Access Condition', 'Rights#1', 'Rights', 'Image Rights#1', 'Image Rights', 'Rights Statement#1', 'Rights Statement', 'Conditions of Use#1', 'Conditions of Use'])
    
def get_type(reader, row):
    return get_value(reader, row, ['Resource Type#1', 'Resource Type', 'Type#1', 'Type', 'Type of Resource#1', 'Type of Resource', 'Work Type#1', 'Work Type', 'formatMediaType#1', 'formatMediaType#2', 'formatMediaType', 'IANA Media Type#1'])
    
def get_filename(reader, row):
    return get_value(reader, row, ['Identifier#1', 'Identifier#2', 'Identifier', 'FileID#1', 'FileID#2', 'FileID', 'File Name'])
    
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
             # check if Identifier ARK#1 column exists, if not, check for Identifier ARK column
             if 'Identifier ARK#1' in row and not row['Identifier ARK#1']:
                 identifier_ark = 'Identifier ARK#1'
             elif 'Identifier ARK' in row and not row['Identifier ARK']:
                 identifier_ark = 'Identifier ARK'
             else:
                 identifier_ark = None
                    
             if identifier_ark:
                 # generate ARK
                 luna_url = row['lnexp_PAGEURL']
                 title = get_title(reader, row)
                 rights = get_rights(reader, row)
                 type = get_type(reader, row)
                 filename = get_filename(reader, row)
                 ark = getARK(url, luna_url, title, rights, type, filename, user)
                 row[identifier_ark] = 'https://ark.colorado.edu/ark:/' + ark
                 writer.writerow(row)
             else:
                 writer.writerow(row)


# make this a safe-ish cli script
if __name__ == '__main__':
    main()
