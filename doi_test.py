import re
import random
import string
import csv
import json
import requests
import sys
import time
import secrets
import uuid  # to generate new unique DOI suffixes


# --- CREDENTIALS ---
USERNAME = "xkvt.dsydpq"
PASSWORD = secrets.password
PREFIX = "10.83783"
API_URL = 'https://api.test.datacite.org/dois'

# --- RESOURCE TYPE MAPPING ---
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
    if not raw_type:
        return "Dataset"
    return DATACITE_TYPE_MAP.get(raw_type.strip().lower(), "Dataset")

def extract_ark_suffix(ark_string):
    if not ark_string:
        return None
    return ark_string.strip().rstrip('/').split('/')[-1]

def doi_exists(doi):
    """Return True if DOI already exists in DataCite"""
    try:
        r = requests.get(
            f"{API_URL}/{doi}",
            auth=(USERNAME, PASSWORD),
            headers={"Accept": "application/vnd.api+json"},
            timeout=10
        )
        return r.status_code == 200
    except requests.RequestException:
        return False

def is_external_doi(doi):
    """Return True if DOI does not belong to our repository"""
    return not doi.startswith(PREFIX)

def generate_short_suffix(length=6):
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

def sanitize_suffix(suffix):
    if not suffix:
        return None
    suffix = suffix.lower()
    suffix = re.sub(r'[^a-z0-9-]', '-', suffix)
    return suffix

def clean_publication_year(date_string):
    """
    Remove brackets/parentheses and extract a valid 4-digit year
    Examples:
      '1954 [1955]' -> '1954'
      '[1982]' -> '1982'
      'ca. 1970 (revised)' -> '1970'
    """
    if not date_string:
        return "2026"

    # Remove bracketed or parenthetical content
    cleaned = re.sub(r'[\[\(].*?[\]\)]', '', date_string)

    # Find first 4-digit year
    match = re.search(r'\b(1[0-9]{3}|20[0-9]{2})\b', cleaned)
    if match:
        return match.group(0)

    return "2026"

def post_doi(record):
    return requests.post(
        API_URL,
        auth=(USERNAME, PASSWORD),
        headers={"Content-Type": "application/vnd.api+json"},
        data=json.dumps(record),
        timeout=10
    )

def mint_ark(input_csv, max_422_retries=5):
    output_csv = "doi_mapping_results.csv"
    stats = {"success": 0, "exists": 0, "skipped": 0, "failed": 0}

    try:
        with open(input_csv, mode='r', encoding='utf-8-sig') as f_in, \
             open(output_csv, mode='w', newline='', encoding='utf-8') as f_out:

            reader = csv.DictReader(f_in)
            fieldnames = ["Original ARK", "Work Title", "Mapped DOI", "Status", "Reason", "URL"]
            writer = csv.DictWriter(f_out, fieldnames=fieldnames)
            writer.writeheader()

            print("--- STARTING PROCESS ---")
            print(f"Input File: {input_csv}")
            print(f"Detected Headers: {reader.fieldnames}")
            print("------------------------\n")

            for i, row in enumerate(reader, 1):
                # --- Extract ARK identifiers ---
                ark_id = (
                    row.get('Identifier ARK#1')
                    or row.get('Identifier ARK')
                    or row.get('Persistent Identifier#1')
                    or row.get('Persistent Identifier')
                    or ''
                ).strip()

                ark_suffix = extract_ark_suffix(ark_id)
                sanitized_suffix = sanitize_suffix(ark_suffix) or generate_short_suffix()

                # --- Extract metadata ---
                title = (
                    row.get('Title#1')
                    or row.get('Title')
                    or row.get('Work Title#1')
                    or row.get('Work Title')
                    or ''
                ).strip() or f"Record for {ark_id}"

                url = (row.get('lnexp_PAGEURL') or row.get('URL') or '').strip()

                raw_date = (row.get('Work Date#1') or row.get('date') or '')
                publication_year = clean_publication_year(raw_date)

                raw_type = (
                    row.get('Resource Type#1')
                    or row.get('Resource Type')
                    or row.get('Type')
                    or ''
                ).strip()
                resource_type_general = get_mapped_type(raw_type)

                # --- Skip if URL is missing ---
                if not url:
                    print(f"[{i}] SKIP: Missing URL for {ark_id}")
                    stats["skipped"] += 1
                    writer.writerow({
                        "Original ARK": ark_id,
                        "Work Title": title,
                        "Mapped DOI": "",
                        "Status": "Skipped",
                        "Reason": "Missing URL",
                        "URL": ""
                    })
                    continue

                # --- Generate initial DOI string ---
                doi_string = f"{PREFIX}/{sanitized_suffix}"

                # --- Check if DOI exists ---
                if doi_exists(doi_string):
                    if is_external_doi(doi_string):
                        print(f"[{i}] External DOI exists: {doi_string}. Generating new DOI...")
                        doi_string = f"{PREFIX}/{generate_short_suffix()}"
                    else:
                        print(f"[{i}] SKIP: DOI already exists in repository {doi_string}")
                        stats["exists"] += 1
                        writer.writerow({
                            "Original ARK": ark_id,
                            "Work Title": title,
                            "Mapped DOI": doi_string,
                            "Status": "Skipped",
                            "Reason": "DOI already exists in repository",
                            "URL": url
                        })
                        continue

                # --- Build DOI record ---
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
                            "types": {"resourceTypeGeneral": resource_type_general},
                            "event": "publish"
                        }
                    }
                }

                print(f"[{i}] PROCESSING: {doi_string} ({publication_year})")

                mapped_doi = ""
                status = ""
                reason = ""
                success = False

                try:
                    for attempt in range(max_422_retries):
                        response = post_doi(record)

                        if response.status_code == 201:
                            mapped_doi = record['data']['attributes']['doi']
                            status = "Created"
                            reason = "" if attempt == 0 else f"Created after {attempt} retries"
                            stats["success"] += 1
                            success = True
                            print(f"    Success: DOI minted ({mapped_doi})")
                            break

                        elif response.status_code == 422:
                            new_suffix = generate_short_suffix()
                            new_doi = f"{PREFIX}/{new_suffix}"
                            record['data']['attributes']['doi'] = new_doi
                            print(f"    422 Error: retrying with new DOI {new_doi} (attempt {attempt+1})")
                            reason = "422 Error - retrying with new DOI"

                        else:
                            status = "Skipped"
                            reason = f"API Error {response.status_code}: {response.text}"
                            stats["failed"] += 1
                            print(f"    Skipped: {reason}")
                            break

                    if not success:
                        status = "Skipped"
                        if reason == "":
                            reason = f"Failed after {max_422_retries} retries"
                        stats["failed"] += 1

                    writer.writerow({
                        "Original ARK": ark_id,
                        "Work Title": title,
                        "Mapped DOI": mapped_doi,
                        "Status": status,
                        "Reason": reason,
                        "URL": url
                    })

                except Exception as e:
                    print(f"    Connection Error: {e}")
                    stats["failed"] += 1
                    writer.writerow({
                        "Original ARK": ark_id,
                        "Work Title": title,
                        "Mapped DOI": "",
                        "Status": "Skipped",
                        "Reason": f"Connection Error: {e}",
                        "URL": url
                    })

                time.sleep(0.5)

        # --- SUMMARY ---
        print("\n" + "=" * 30)
        print("RUN SUMMARY")
        print("=" * 30)
        print(f"Successfully Created: {stats['success']}")
        print(f"Already Exists:       {stats['exists']}")
        print(f"Skipped (No URL):     {stats['skipped']}")
        print(f"Skipped (API/Connection Errors): {stats['failed']}")
        print("=" * 30)
        print(f"Mapping saved to: {output_csv}\n")

    except FileNotFoundError:
        print(f"Fatal Error: File not found: {input_csv}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python script_name.py <your_file.csv>")
    else:
        mint_ark(sys.argv[1])
