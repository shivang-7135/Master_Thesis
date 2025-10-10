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
DOMAINS = ["de.indeed.com/jobs", "www.stepstone.de/jobs", "www.xing.com/jobs"]
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
TARGET_RECORDS = 1000

# -------------------- HELPERS --------------------
def clean_text(txt):
    if not txt: return ""
    txt = BeautifulSoup(txt, "html.parser").get_text(" ", strip=True)
    txt = re.sub(r"\s+", " ", txt).strip()
    return txt

def is_relevant(text):
    t = " " + text.lower() + " "
    return any(k in t for k in KEYWORDS) and any(loc.lower() in t for loc in GERMAN_LOCATIONS)

def fetch_index_records(index, domain):
    api = f"https://index.commoncrawl.org/{index}-index?url={domain}*&output=json"
    try:
        res = requests.get(api, timeout=60)
        return [json.loads(l) for l in res.text.splitlines() if l.strip()]
    except Exception as e:
        print(f"Index fetch failed for {domain} in {index}: {e}")
        return []

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
            text = soup.get_text(" ", strip=True)
            if not is_relevant(text):
                return None
            # structure extraction
            title = soup.find(["h1","h2"])
            title = clean_text(title.text if title else "")
            # heuristic company/location extraction
            body = clean_text(text)
            company = ""
            location = ""
            for loc in GERMAN_LOCATIONS:
                if loc.lower() in body.lower():
                    location = loc
                    break
            # capture first uppercase sequence before 'GmbH' or 'AG'
            m = re.search(r"([A-ZÄÖÜ][A-Za-zÄÖÜäöüß&\-\.\s]{3,30}(GmbH|AG))", body)
            if m: company = m.group(1)
            return {
                "url": rec.get("url"),
                "source": ("indeed_de" if "indeed" in rec["url"]
                           else "stepstone_de" if "stepstone" in rec["url"]
                           else "xing_jobs"),
                "timestamp": rec.get("timestamp"),
                "job_title": title,
                "company": company,
                "location": location,
                "job_description": body[:15000]
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

df.to_csv("jobs_2019.csv", index=False)
print("💾 Saved to jobs_2019.csv")