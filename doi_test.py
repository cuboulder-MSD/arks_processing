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
                title = (row.get('Work Title#1') or row.get('title') or row.get('Title') or '').strip()
                url = (row.get('lnexp_PAGEURL') or row.get('URL') or row.get('Url') or '').strip()
                date = (row.get('Work Date#1') or row.get('date') or '2026').strip()

                if not title:
                    title = f"Record for {ark_id}"
                
                if not url:
                    print(f"[{i}] SKIP: Missing URL for {doi_string}")
                    stats["skipped"] += 1
                    continue

                # 3. Build Payload
                payload = {
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
                            "types": {"resourceTypeGeneral": "Image"},
                            "event": "publish"
                        }
                    }
                }

                # 4. API Call
                print(f"[{i}] PROCESSING: {doi_string}")
                
                try:
                    response = requests.post(
                        API_URL,
                        auth=(USERNAME, PASSWORD),
                        headers={"Content-Type": "application/vnd.api+json"},
                        data=json.dumps(payload),
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
