import re
import random
import string
import csv
import json
import requests
import sys
import time
import secrets
from datetime import datetime

# --- CREDENTIALS ---
USERNAME = "xkvt.dsydpq"
PASSWORD = secrets.password
PREFIX = "10.83783"
API_URL = 'https://api.test.datacite.org/dois'
DOI_RESOLVER = "https://doi.org/"

# --- RESOURCE TYPE MAPPING ---
DATACITE_TYPE_MAP = {
    "image": "Image",
    "still image": "Image",
    "photograph": "Image",
    "photographs": "Image",
    "photograph albums": "Image",
    "cartes-de-visite (card photographs)": "Image",
    "photo": "Image",
    "stillimage": "Image",
    "photographic prints": "Image",
    "cartographic image": "Image",
    "sketch maps": "Image",
    "cartographic": "Image",
    "watercolors (paintings)": "Image",
    "drawings (visual works)": "Image",
    "mixed material": "Image",
    "image/tiff": "Image",
    "image/jpeg": "Image",
    "tear sheets": "Image",

    "text": "Text",
    "book": "Text",
    "article": "Text",
    "articles": "Text",
    "manuscript": "Text",
    "manuscript language material": "Text",
    "language material": "Text",
    "tables of contents": "Text",
    "title pages": "Text",
    "notated music": "Text",
    "bibliographies": "Text",
    "clippings (information artifacts)": "Text",
    "reports": "Text",
    "letters (correspondence)": "Text",
    "notes": "Text",
    "documents": "Text",
    "application/pdf": "Text",

    "dataset": "Dataset",
    "collection": "Collection",

    "audio": "Sound",
    "sound": "Sound",

    "video": "Audiovisual",
    "moving image": "Audiovisual",
    "movingimage": "Audiovisual",

    "software": "Software",
}

# ---------------- UTILS ---------------- #

def get_mapped_type(raw_type):
    if not raw_type:
        return "Dataset"
    return DATACITE_TYPE_MAP.get(raw_type.strip().lower(), "Dataset")
    
# ---------------- DOI ---------------- # 

def generate_short_suffix(length=6):
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=length))

def sanitize_suffix(suffix):
    return re.sub(r"[^a-z0-9-]", "-", suffix.lower()) if suffix else None

# ---------------- DATE HANDLING ---------------- #

def doi_exists(doi):
    try:
        r = requests.get(
            f"{API_URL}/{doi}",
            auth=(USERNAME, PASSWORD),
            headers={"Accept": "application/vnd.api+json"},
            timeout=10,
        )
        return r.status_code == 200
    except requests.RequestException:
        return False 

def extract_publication_year(date_string):
    if not date_string:
        return None

    date_str = str(date_string).strip()
    date_str = re.sub(r"[\[\]]", "", date_str)
    date_str = re.sub(r"\b(ca\.?|circa|approx\.?)\b", "", date_str, flags=re.IGNORECASE)

    match = re.search(r"\b(1[0-9]{3}|20[0-9]{2})\b", date_str)
    return match.group(1) if match else None

def get_publication_year_from_row(row):
    date_fields = [
        "Date Published", "Date Issued", "Issued", "Publication Date", "Published Date",
        "Image Date", "Image Date#1", "Date Created", "Created",
        "Date Captured", "Date Captured#1",
        "Digital Conversion Date", "Digital Conversion Date#1",
        "Date Uploaded", "Date Uploaded#1",
    ]

    for field in date_fields:
        year = extract_publication_year(row.get(field, ""))
        if year:
            print(f"    Publication year from '{field}': {year}")
            return year

    fallback = str(datetime.now().year)
    print(f"    ⚠ No valid date found — using {fallback}")
    return fallback

# ---------------- DATACITE ---------------- #

def post_doi(record):
    return requests.post(
        API_URL,
        auth=(USERNAME, PASSWORD),
        headers={"Content-Type": "application/vnd.api+json"},
        data=json.dumps(record),
        timeout=10,
    )

# ---------------- DOI Minting ---------------- #

def mint_doi(input_csv):
    
    output_csv = "doi_minting_results.csv"
    stats = {"success": 0, "exists": 0, "skipped": 0, "failed": 0}
    
    with open(input_csv, "r", encoding="utf-8-sig") as f_in, \
         open(output_csv, "w", newline="", encoding="utf-8") as f_out:
                 
        reader = csv.DictReader(f_in)
        # remove completely empty rows
        rows = [
            row for row in reader
            if any((value or "").strip() for value in row.values())
        ]
        
        total_rows = len(rows)

        writer = csv.DictWriter(
            f_out,
            fieldnames=[
                "Original Identifier",
                "Work Title",
                "DOI",
                "Status",
                "Reason",
                "URL",
            ],
        )

        writer.writeheader()

        print("\n--- STARTING DOI MINTING ---\n")
        
        for i, row in enumerate(rows, start=1):
            
            print(f"\n[{i}/{total_rows}]")
            
# ---------------- Metadata ---------------- #

            title = (
                row.get("Title#1")
                or row.get("title#1")
                or row.get("Title")
                or row.get("Work Title#1")
                or row.get("Work Title")
                or row.get("Project-Roll-Frame")
                or row.get("County Set Name#1")
                or row.get("County Set Name")
                or ""
            ).strip()

            url = (row.get("lnexp_PAGEURL") or row.get("URL") or "").strip()

            ark_and_doi_id = (
                row.get("Identifier ARK#1")
                or row.get("Identifier ARK")
                or row.get("Persistent Identifier#1")
                or row.get("Persistent Identifier")
                or ""
            ).strip()

            # --- Skipt ARK and DOI records --- #
            if ark_and_doi_id:
                print(f"SKIP: Identifier exists ({ark_and_doi_id})")
                stats["skipped"] += 1

                writer.writerow({
                    "Original Identifier": ark_and_doi_id,
                    "Work Title": title,
                    "DOI": "",
                    "Status": "Skipped",
                    "Reason": "ARK or DOI already exists",
                    "URL": url
                })
                continue

            if not url:
                print("    ⚠ Missing URL")
                stats["skipped"] += 1
                continue

            publication_year = get_publication_year_from_row(row)

            raw_type = (
                row.get("Resource Type#1")
                or row.get("Resource Type")
                or row.get("Type")
                or row.get("Type of Resource#1")
                or row.get("Type#1")
                or row.get("Type of Resource")
                or row.get("Work Type")
                or row.get("Work Type#1")
                or row.get("Work Type#2")
                or row.get("formatMediaType#1")
                or row.get("formatMediaType#2")
                or row.get("formatMediaType")
                or row.get("IANA Media Type#1")
                or row.get("Format Media Type#1")
                or ""
            ).strip()

            mapped_type = get_mapped_type(raw_type)

            # Print resource type to command line
            print(f"    Resource type — raw: '{raw_type or '∅'}' → mapped: {mapped_type}")

            doi_string = f"{PREFIX}/{generate_short_suffix()}"
            doi_url = f"{DOI_RESOLVER}{doi_string}"

            while doi_exists(doi_string):
                print(f"    DOI exists → regenerating")
                stats["exists"] += 1
                doi_string = f"{PREFIX}/{generate_short_suffix()}"

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
                        "publicationYear": publication_year,
                        "types": {"resourceTypeGeneral": mapped_type},
                        "event": "publish",
                    },
                }
            }

            sucess = False
            
            for _ in range(5):
                response = post_doi(record)

                if response.status_code == 201:
                    success = True
                    stats["success"] += 1
                    print(f"    ✔ Created {doi_url}")
                    break

                elif response.status_code == 422:
                    doi_string = f"{PREFIX}/{generate_short_suffix()}"
                    record["data"]["attributes"]["doi"] = doi_string
                    print("    Retry with new DOI")

                else:
                    stats["failed"] += 1
                    print(f"    ✖ API error {response.status_code}")
                    break

            writer.writerow({
                "Original Identifier": "",
                "Work Title": title,
                "DOI": doi_url if success else "",
                "Status": "Created" if success else "Skipped",
                "Reason": "" if success else "Mint failed",
                "URL": url
            })
            time.sleep(0.5)

    print("\n--- RUN COMPLETE ---")
    for k, v in stats.items():
        print(f"{k.capitalize()}: {v}")
    print(f"Results written to: {output_csv}")


# ---------------- ENTRY ---------------- #

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python script.py input.csv")
        sys.exit(1)

    mint_doi(sys.argv[1])
