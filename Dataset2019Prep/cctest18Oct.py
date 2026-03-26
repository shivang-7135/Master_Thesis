"""
Extract 2019 job postings mentioning Machine Learning from Common Crawl archives
for German Indeed domains (de.indeed.com).
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
# --- MODIFIED ---
DOMAINS = ["de.indeed.com/jobs"] 
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
    if not any(k in t for k in KEYWORDS):
        return False
    if not any(loc.lower() in t for loc in GERMAN_LOCATIONS):
        return False
    return True

def fetch_index_records(index, domain):
    api = f"https://index.commoncrawl.org/{index}-index?url={domain}*&output=json"
    try:
        res = requests.get(api, timeout=60)
        return [json.loads(l) for l in res.text.splitlines() if l.strip()]
    except Exception as e:
        print(f"Index fetch failed for {domain} in {index}: {e}")
        return []

# --- NEW, INDEED-ONLY HELPER ---
def find_main_job_block(soup):
    """
    Tries to find the main content block OF AN INDEED JOB POSTING.
    The most reliable signal is the job description ID.
    If it's not found, this is a search results page (SERP) and we return None.
    """
    
    # This ID is the key. If it's not on the page, it's not a job post.
    desc_block = soup.find(id="jobDescriptionText")
    
    if not desc_block:
        # This is a SERP (like your screenshot) or other non-job page.
        return None
    
    # Try to get the whole job-view container for better title/company extraction
    parent_container = soup.find(id="jobsearch-ViewjobLayout-main")
    
    if parent_container:
        return parent_container
    
    # Fallback: just return the description block's parent
    return desc_block.parent

# --- HEAVILY MODIFIED EXTRACTION FUNCTION ---
def extract_from_warc(rec):
    cc_url = f"https://data.commoncrawl.org/{rec['filename']}"
    off, length = int(rec['offset']), int(rec['length'])
    headers = {'Range': f"bytes={off}-{off+length-1}"}
    
    try:
        r = requests.get(cc_url, headers=headers, timeout=60)
    except requests.RequestException:
        return None # Failed to fetch WARC record
        
    stream = BytesIO(r.content)
    
    for entry in ArchiveIterator(stream):
        if entry.rec_type == "response":
            html = entry.content_stream().read()
            try:
                soup = BeautifulSoup(html, "lxml")
            except:
                soup = BeautifulSoup(html, "html.parser")

            # **CRITICAL CHANGE**: Find the specific Indeed job block.
            main_job_block = find_main_job_block(soup)
            
            if main_job_block is None:
                # This is a search results page. DISCARD IT.
                return None
            
            # --- Page is a valid job posting, proceed with extraction ---
            
            # 1. Get Job Description Text
            desc_block = main_job_block.find(id="jobDescriptionText")
            if not desc_block: 
                desc_block = main_job_block # Fallback
            job_description_text = clean_text(desc_block.get_text(" ", strip=True))

            # 2. Check for relevance
            if not is_relevant(job_description_text):
                return None
            
            # 3. Extract Title (Indeed-specific)
            title = ""
            # Indeed's 2019 layout often used this class
            title_tag = main_job_block.find(class_="jobsearch-JobInfoHeader-title")
            if not title_tag:
                title_tag = main_job_block.find("h1") # Fallback
            title = clean_text(title_tag.text if title_tag else "")

            # 4. Extract Company & Location (Indeed-specific)
            company = ""
            location = ""
            
            # These selectors are quite reliable for Indeed's job header
            header_div = main_job_block.find(class_="jobsearch-JobInfoHeader-mainContent")
            if header_div:
                company_tag = header_div.find(attrs={"data-testid": "inlineHeader-companyName"})
                if company_tag: company = clean_text(company_tag.text)
                
                location_tag = header_div.find(attrs={"data-testid": "inlineHeader-companyLocation"})
                if location_tag: location = clean_text(location_tag.text)

            # 5. Fallbacks (if selectors failed on an old layout)
            if not location:
                for loc in GERMAN_LOCATIONS:
                    if loc.lower() in job_description_text.lower():
                        location = loc
                        break
            if not company:
                m = re.search(r"([A-ZÄÖÜ][A-Za-zÄÖÜäöüß&\-\.\s]{3,30}(GmbH|AG))", job_description_text)
                if m: company = m.group(1).strip()
            
            return {
                "url": rec.get("url"),
                "source": "indeed_de", # Hard-coded
                "timestamp": rec.get("timestamp"),
                "job_title": title,
                "company": company,
                "location": location,
                "job_description": job_description_text[:15000] 
            }
    return None

# -------------------- MAIN PIPELINE --------------------
jobs = []
print("Starting Common Crawl job extraction (Indeed-only)...")
for index in INDEXES_2019[::-1]:
    if len(jobs) >= TARGET_RECORDS:
        break
    # This loop will now only run for the 'de.indeed.com/jobs' domain
    for domain in DOMAINS:
        records = fetch_index_records(index, domain)
        if not records:
            continue
            
        for rec in tqdm(records, desc=f"{index}-indeed_de"):
            try:
                job = extract_from_warc(rec)
                if job:
                    jobs.append(job)
                    if len(jobs) >= TARGET_RECORDS:
                        raise StopIteration
            except StopIteration:
                break
            except Exception as e:
                # print(f"Error processing record {rec.get('url')}: {e}") # Uncomment for debugging
                continue
        
        if len(jobs) >= TARGET_RECORDS:
            break

print(f"\n✅ Collected {len(jobs)} structured German ML job postings from 2019")

# -------------------- STRUCTURE & SAVE --------------------
if jobs:
    df = pd.DataFrame(jobs)
    df["year"] = 2019
    df["posting_date"] = pd.to_datetime(df["timestamp"], format="%Y%m%d%H%M%S", errors="coerce")
    df["job_id"] = [f"2019_{i+1:04d}" for i in range(len(df))]
    df = df[["job_id","year","source","url","job_title","company","location", 
             "job_description","posting_date"]]

    df.to_csv("jobs_2019_indeed.csv", index=False)
    print("💾 Saved to jobs_2019_indeed.csv")
else:
    print("No jobs found matching the criteria.")