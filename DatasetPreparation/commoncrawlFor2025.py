"""
Extract 2019 job postings mentioning Machine Learning from Common Crawl archives
for German domains (Indeed, Xing, Stepstone).
"""

import requests, json, re, pandas as pd
from bs4 import BeautifulSoup
from io import BytesIO
from tqdm import tqdm
from warcio.archiveiterator import ArchiveIterator
from datetime import datetime

# ------------------------------------
# 1. SETTINGS
# ------------------------------------
DOMAINS = ["de.indeed.com/viewjob"]
KEYWORDS = [
    "machine learning", "deep learning", "data science",
    "künstliche intelligenz", "artificial intelligence"
]
GERMAN_LOCATIONS = ["Deutschland", "Germany", "Berlin", "München", "Hamburg", "Stuttgart",
                    "Frankfurt", "Köln", "Düsseldorf", "Leipzig", "Dresden", "Bonn", "Nürnberg"]
# All 2019 Common Crawl indexes
INDEXES_2019 = [
    "CC-MAIN-2019-04", "CC-MAIN-2019-09", "CC-MAIN-2019-13", "CC-MAIN-2019-18",
    "CC-MAIN-2019-22", "CC-MAIN-2019-26", "CC-MAIN-2019-30", "CC-MAIN-2019-35",
    "CC-MAIN-2019-39", "CC-MAIN-2019-43", "CC-MAIN-2019-47", "CC-MAIN-2019-51"
]
TARGET_RECORDS = 1600

# -------------------- HELPERS --------------------
def clean_text(txt):
    if not txt: return ""
    txt = BeautifulSoup(txt, "html.parser").get_text(" ", strip=True)
    txt = re.sub(r"\s+", " ", txt).strip()
    return txt

def is_relevant(text):
    t = " " + text.lower() + " "
    return any(k in t for k in KEYWORDS)

def fetch_index_records(index, domain):
    api = f"https://index.commoncrawl.org/{index}-index?url={domain}*&output=json"
    try:
        res = requests.get(api, timeout=60)
        return [json.loads(l) for l in res.text.splitlines() if l.strip()]
    except Exception as e:
        print(f"Index fetch failed for {domain} in {index}: {e}")
        return []
JOB_TITLE_KEYWORDS = [
    "Engineer", "Developer", "Manager", "Scientist", "Analyst",
    "Consultant", "Director", "Lead", "Specialist", "Administrator",
    "Designer", "Architect", "Intern", "Assistant"
]

def is_job_title(cand):
    # Title should be reasonably short
    if not (5 <= len(cand) <= 60):
        return False
    # Check for job keywords
    if any(keyword.lower() in cand.lower() for keyword in JOB_TITLE_KEYWORDS):
        return True
    return False

def extract_from_warc(rec):
    cc_url = f"https://data.commoncrawl.org/{rec['filename']}"
    off, length = int(rec['offset']), int(rec['length'])
    headers = {'Range': f"bytes={off}-{off+length-1}"}
    r = requests.get(cc_url, headers=headers, timeout=60)
    stream = BytesIO(r.content)
    for entry in ArchiveIterator(stream):
        if entry.rec_type == "response":
            html = entry.content_stream().read()
            soup = BeautifulSoup(html, "html.parser")

            # Extract job title
            title_tag = soup.find(class_="jobsearch-JobInfoHeader-title")
            title = clean_text(title_tag.get_text(strip=True)) if title_tag else ""

            # Extract job description/body
            body_tag = soup.find(class_="jobsearch-JobComponent")
            text = clean_text(body_tag.get_text(" ", strip=True)) if body_tag else ""

            if not is_relevant(text):
                return None

            # Now apply further cleaning and extraction logic as before
            if not is_relevant(text):
                return None
            # Extract company details
            # Extract company name using data-testid
            company_tag = soup.find(attrs={"data-testid": "inlineHeader-companyName"})
            company = clean_text(company_tag.get_text(strip=True)) if company_tag else ""
            # Heuristic company extraction improvement
            # company_match = re.search(r"([A-ZÄÖÜ][A-Za-zÄÖÜäöüß&\-\.\s]{2,100}(GmbH|AG))", text)
            # company = company_match.group(0) if company_match else ""

# Extract company location
            location_tag = soup.find(attrs={"data-testid": "jobsearch-JobInfoHeader-companyLocation"})
            location = clean_text(location_tag.get_text(strip=True)) if location_tag else ""

            # Location filtering
            # location = ""
            # for loc in GERMAN_LOCATIONS:
            #     if re.search(r"\b" + re.escape(loc) + r"\b", text[:1000], re.IGNORECASE):
            #         location = loc
            #         break

            # Job description block extraction
            job_description = clean_text(text)

            return {
                "url": rec.get("url"),
                "source": ("indeed_de" if "indeed" in rec["url"]
                        else "stepstone_de" if "stepstone" in rec["url"]
                        else "xing_jobs"),
                "timestamp": rec.get("timestamp"),
                "job_title": title,
                "company": company,
                "location": location,
                "job_description": job_description[:15000]
            }
    return None

# -------------------- MAIN PIPELINE --------------------
jobs = []
for index in INDEXES_2019[::-1]:
    for domain in DOMAINS:
        records = fetch_index_records(index, domain)
        for rec in tqdm(records, desc=f"{index}-{domain}"):
            try:
                job = extract_from_warc(rec)
                if job:
                    jobs.append(job)
                    if len(jobs) >= TARGET_RECORDS:
                        raise StopIteration
            except StopIteration:
                break
            except Exception:
                continue
        if len(jobs) >= TARGET_RECORDS:
            break
    if len(jobs) >= TARGET_RECORDS:
        break

print(f"\n✅ Collected {len(jobs)} structured German ML job postings from 2019")

# -------------------- STRUCTURE & SAVE --------------------
df = pd.DataFrame(jobs)
df["year"] = 2019
df["posting_date"] = pd.to_datetime(df["timestamp"], errors="coerce")
df["job_id"] = [f"2019_{i+1:04d}" for i in range(len(df))]
df = df[["job_id","year","source","url","job_title","company","location", 
         "job_description","posting_date"]]

df.to_csv("jobs_2019-2.csv", index=False)
print("💾 Saved to jobs_2019-2.csv")