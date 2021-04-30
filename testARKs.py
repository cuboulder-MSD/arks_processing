import sys, csv, requests, time

infile_path = sys.argv[1]
with open(infile_path, encoding='utf-8', newline='' ) as csvfile:
         reader = csv.DictReader(csvfile)
         for row in reader:
             ark = row['ark']
             url = row['luna_url']
             # print(ark)
             if len(ark) > 0:
                 auth_token = ''
                 headers={"Content-Type":"application/json","Authorization":"Token " + auth_token}
                 req = requests.get(ark,headers=headers)
                 time.sleep(.01)
                 if not req:
                     print(ark,',', req.status_code)

             
