import csv
import json
import requests
import sys
import time
import secrets 

# --- CREDENTIALS ---
USERNAME = "xkvt.dsydpq"
PASSWORD = secrets.password
PREFIX = "10.83783"
API_URL = 'https://api.test.datacite.org/dois'

# --- RESOURCE TYPE MAPPING ---
# Maps strings from your CSV to official DataCite resourceTypeGeneral values.
# DataCite documentation: https://schema.datacite.org/meta/kernel-4.4/doc/DataCite-MetadataKernel_v4.4.pdf
DATACITE_TYPE_MAP = {
    "image": "Image",
    "still image": "Image",
    "photograph": "Image",
    "photo": "Image",
    "text": "Text",
    "book": "Text",
    "article": "Text",
    "dataset": "Dataset",
    "collection": "Collection",
    "audio": "Sound",
    "sound": "Sound",
    "video": "Audiovisual",
    "moving image": "Audiovisual",
    "software": "Software"
}

def get_mapped_type(raw_type):
    """Helper to return valid DataCite type or default to 'Dataset'"""
    if not raw_type:
        return "Dataset"
    return DATACITE_TYPE_MAP.get(raw_type.strip().lower(), "Dataset")

def extract_ark_suffix(ark_string):
    if not ark_string: return None
    return ark_string.strip().rstrip('/').split('/')[-1]

def mint_ark(input_csv):
    output_csv = "doi_mapping_results.csv"
    
    # Counters for the final summary
    stats = {"success": 0, "exists": 0, "failed": 0, "skipped": 0}

    try:
        with open(input_csv, mode='r', encoding='utf-8-sig') as f_in, \
             open(output_csv, mode='w', newline='', encoding='utf-8') as f_out:
            
            reader = csv.DictReader(f_in)
            fieldnames = ["Original ARK", "Work Title", "Mapped DOI", "Status", "URL"]
            writer = csv.DictWriter(f_out, fieldnames=fieldnames)
            writer.writeheader()
            
            print(f"--- STARTING PROCESS ---")
            print(f"Input File: {input_csv}")
            print(f"Detected Headers: {reader.fieldnames}")
            print(f"------------------------\n")

            for i, row in enumerate(reader, 1):
                # 1. Identity Extraction
                ark_id = row.get('Identifier ARK#1', '').strip()
                ark_suffix = extract_ark_suffix(ark_id)
                
                if not ark_suffix:
                    print(f"[{i}]   SKIP: No ARK suffix found in '{ark_id}'")
                    stats["skipped"] += 1
                    continue

                doi_string = f"{PREFIX}/{ark_suffix}".lower()
                
                # 2. Metadata Extraction
                title = (row.get('Title#1') or row.get('title#1') or row.get('Title') or row.get('County Set Name#1') or row.get('County Set Name') or row.get('Work Title#1') or row.get('Work Title') or row.get('Project-Roll-Frame') or '').strip()
                rights = (row.get('Access Condition#1') or row.get('Access Condition#2') or row.get('Access Condition') or row.get('Rights#1') or row.get('Rights') or row.get('Image Rights#1') or row.get('Image Rights') or row.get('Rights Statement#1') or row.get('Rights Statement') or row.get('Conditions of Use#1') or row.get('Conditions of Use') or row.get('rightsSummary#1') or row.get('Access restrictions#1') or '').strip()
                resource_type = (row.get('Resource Type#1') or row.get('Resource Type') or row.get('Type#1') or row.get('Type') or row.get('Type of Resource#1') or row.get('Type of Resource') or row.get('Work Type#1') or row.get('Work Type') or row.get('formatMediaType#1') or row.get('formatMediaType#2') or row.get('formatMediaType') or row.get('IANA Media Type#1') or '').strip()
                filename = (row.get('Local Identifier#1') or row.get('Local Identifier') or row.get('Identifier#1') or row.get('Identifier#2') or row.get('identifier#2') or row.get('identifier#1') or row.get('Identifier') or row.get('FileID#1') or row.get('FileID#2') or row.get('FileID') or row.get('File Name') or row.get('filename') or '').strip()
                url = (row.get('lnexp_PAGEURL') or row.get('URL') or row.get('Url') or '').strip()
                date = (row.get('Work Date#1') or row.get('date') or '2026').strip()
                
                # New: Extract Resource Type from CSV
                raw_type = (row.get('Resource Type') or row.get('Type') or row.get('type') or '').strip()
                resource_type_general = get_mapped_type(raw_type)

                if not title:
                    title = f"Record for {ark_id}"
                
                if not url:
                    print(f"[{i}] SKIP: Missing URL for {doi_string}")
                    stats["skipped"] += 1
                    continue

                # 3. Build record
                record = {
                    "data": {
                        "type": "dois",
                        "attributes": {
                            "doi": doi_string,
                            "prefix": PREFIX,
                            "url": url,
                            "creators": [{"name": "University of Colorado Boulder"}],
                            "titles": [{"title": title}],
                            "publisher": "University of Colorado Boulder",
                            "publicationYear": date if len(date) >= 4 else "2026",
                            "types": {"resourceTypeGeneral": resource_type_general},
                            "event": "publish"
                        }
                    }
                }

                # 4. API Call
                print(f"[{i}] PROCESSING: {doi_string} ({resource_type_general})")
                
                try:
                    response = requests.post(
                        API_URL,
                        auth=(USERNAME, PASSWORD),
                        headers={"Content-Type": "application/vnd.api+json"},
                        data=json.dumps(record),
                        timeout=10
                    )

                    status_label = ""
                    if response.status_code == 201:
                        status_label = "Created"
                        stats["success"] += 1
                        print(f"    Success: New DOI minted.")
                    elif response.status_code == 422:
                        status_label = "Already Exists"
                        stats["exists"] += 1
                        print(f"     Note: DOI already registered.")
                    else:
                        status_label = f"Error {response.status_code}"
                        stats["failed"] += 1
                        print(f"    Failed: {response.text}")

                    # Write to output CSV immediately
                    writer.writerow({
                        "Original ARK": ark_id,
                        "Work Title": title,
                        "Mapped DOI": doi_string,
                        "Status": status_label,
                        "URL": url
                    })

                except Exception as e:
                    print(f"     Connection Error: {e}")
                    stats["failed"] += 1

                time.sleep(0.5)

        # --- FINAL SUMMARY ---
        print(f"\n" + "="*30)
        print(f"RUN SUMMARY")
        print(f"="*30)
        print(f"Successfully Created: {stats['success']}")
        print(f" Already Exists:     {stats['exists']}")
        print(f"Skipped (No data):  {stats['skipped']}")
        print(f"Failed (API Error):  {stats['failed']}")
        print(f"="*30)
        print(f"Mapping saved to: {output_csv}\n")

    except FileNotFoundError:
        print(f"Fatal Error: The file '{input_csv}' was not found.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python script_name.py <your_file.csv>")
    else:
        mint_ark(sys.argv[1])
