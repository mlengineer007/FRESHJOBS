import http.client
from dotenv import load_dotenv
import os
import csv
import json
load_dotenv()

rapidapikey = os.getenv('rapidapikey')
conn = http.client.HTTPSConnection("linkedin-data-scraper-api1.p.rapidapi.com")

headers = {
    'x-rapidapi-key':  rapidapikey ,
    'x-rapidapi-host': "linkedin-data-scraper-api1.p.rapidapi.com"
}

conn = http.client.HTTPSConnection("linkedin-data-scraper-api1.p.rapidapi.com")

headers = {
    'x-rapidapi-key': "acdfb5f277msh84114c407295bf7p170cf8jsn5dff8b03ec3d",
    'x-rapidapi-host': "linkedin-data-scraper-api1.p.rapidapi.com"
}

conn.request("GET", "/jobs/search?keywords=data%20engineer&location=United%20States&page_number=1", headers=headers)

res = conn.getresponse()
data = res.read()



response = json.loads(data.decode("utf-8"))
# Extract the jobs list
jobs = response["data"]["jobs"]

# Define the output CSV file path
output_csv = "linkedin_jobs.csv"

# Define CSV headers
headers = [
    "company",
    "company_url",
    "job_title",
    "job_url",
    "job_id",
    "location",
    "work_type",
    "salary",
    "posted_at",
    "is_easy_apply",
    "applicant_count",
    "description",
    "apply_url"
]

# Write to CSV
with open(output_csv, mode='w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=headers)
    writer.writeheader()
    for job in jobs:
        writer.writerow({key: job.get(key, "") for key in headers})

print(f"✅ {len(jobs)} job(s) written to {output_csv}")
