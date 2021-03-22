import requests, json, csv, sys, uuid
from datetime import datetime


def deleteARK(ark):
    auth_token = ''


    ark = ark.replace('https://ark.colorado.edu',' https://libapps.colorado.edu')

    url = ark + '/detail'
    # print(url)
    headers={"Content-Type":"application/json","Authorization":"Token " + auth_token}

    req = requests.delete(url,headers=headers)


    print(url + ' has been deleted')




def main():
    # Grab our infile_path from the cli
    infile_path = sys.argv[1]



    with open(infile_path, newline='' ) as csvfile:
         reader = csv.DictReader(csvfile)


         for row in reader:

             ark = row['Identifier ARK#1']
             # print(ark)
             deleteARK(ark)


# make this a safe-ish cli script
if __name__ == '__main__':
    main()
