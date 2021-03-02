import requests, json, csv, sys, uuid
from datetime import datetime

def getARK():

    arks = []
    url = "https://libapps.colorado.edu/ark:/?page_size=500"

    auth_token = ''
    headers={"Content-Type":"application/json","Authorization":"Token " + auth_token}

    req = requests.get(url,headers=headers)

    rjson = req.json()
    while rjson:
        for x in rjson['results']:
            ark = "https://ark.colorado.edu/ark:/"+x['ark']
            title = x['metadata']['mods']['titleInfo'][0]['title']
            luna_url = x['resolve_url']
            arks.append({'ark':ark,'title':title,'luna_url':luna_url})

        if rjson.get("next") not in ["Null", None]:
            next_page = requests.get(rjson["next"], headers=headers)
            rjson= next_page.json()
        else:
            rjson = None
    return arks




def main():
    outfile = 'arks_' + datetime.today().strftime('%Y-%m-%d') + '.csv'


    with open(outfile, "w") as outfile:
        fieldnames = ['ark', 'title', 'luna_url']
        writer = csv.DictWriter(outfile, fieldnames = fieldnames)
        arks = getARK()
        writer.writeheader()
        for row in arks:
            writer.writerow(row)


# make this a safe-ish cli script
if __name__ == '__main__':
    main()
