"""
Extract 2019 job postings mentioning Machine Learning from Common Crawl archives
for German domains (Indeed, Xing, Stepstone).
"""

import requests, json, re, os, hashlib, pandas as pd
from bs4 import BeautifulSoup
from io import BytesIO
from tqdm import tqdm
from warcio.archiveiterator import ArchiveIterator
from datetime import datetime
from urllib.parse import urljoin
from requests.utils import quote

# ------------------------------------
# 1. SETTINGS
# ------------------------------------
# German job portals and common ATS hosts likely present in Common Crawl (2019)
# Note: We query the CC index with pattern `url={domain}*`, so include host and a stable path segment
DOMAINS = [
    # Major general job boards
    # "de.indeed.com/jobs",              # Indeed Germany
    # "www.stepstone.de/jobs",           # StepStone
    # "www.xing.com/jobs",               # XING Jobs (public listings)
    # "www.monster.de/stellenangebote",  # Monster Germany ("stellenangebote" and "jobs")
    # "www.monster.de/jobs",
    # "www.stellenanzeigen.de/job",  # stellenanzeigen.de
    "www.kimeta.de/stellenangebote",   # Kimeta aggregator
    "www.meinestadt.de/deutschland/jobs", # meinestadt.de jobs
    "jobs.zeit.de/",                   # Die ZEIT job board
    "stellenmarkt.sueddeutsche.de/jobs", # Süddeutsche Zeitung Stellenmarkt
    "stellenmarkt.faz.net/",           # FAZ Stellenmarkt

    # IT/Tech-focused boards
    "jobs.heise.de/",                  # Heise Jobs (IT)
    "www.jobware.de/Jobs",             # Jobware (often IT/engineering)
    "www.jobvector.de/stellenangebote",# jobvector (Tech/Science)
    "www.academics.de/jobs",           # academics.de (Research/Data roles)
    "www.get-in-it.de/jobs",           # get-in-IT (junior/graduate IT)
    "www.get-in-engineering.de/jobs",  # get-in-Engineering
    "www.berlinstartupjobs.com/engineering",      # Berlin Startup Jobs (Engineering)
    "www.berlinstartupjobs.com/de/engineering",   # German version

    # Finance/analytics-oriented
    "www.efinancialcareers.de/jobs",   # eFinancialCareers DE

    # 2019 global tech boards that often include DE roles
    "stackoverflow.com/jobs",          # Stack Overflow Jobs (active in 2019)

    # Common ATS/Job boards used by many German companies (broad coverage)
    "boards.greenhouse.io/",           # Greenhouse-hosted career pages
    "jobs.lever.co/",                  # Lever-hosted career pages
    "jobs.smartrecruiters.com/",       # SmartRecruiters-hosted pages
    "join.com/companies/",             # JOIN company job pages

    # Public agency
    "www.arbeitsagentur.de/jobsuche",  # Bundesagentur für Arbeit (public job search)
]
KEYWORDS = [
     "künstliche intelligenz", "ki", "machine learning", "ml ", " ml-", " ml/",
    "deep learning", "datenwissenschaft", "data scientist", "data science",
    "nlp", "natural language", "computer vision", "cv ", "cv-",
    "modellierung", "pytorch", "tensorflow", "mlops", "ml-ops",
    "genai", "large language", "llm", "reinforcement learning",
    "dateningenieur", "data engineer", "ai engineer", "ai/ ml", "ai/ml",
    "wissenschaftlicher mitarbeiter ki", "ml engineer", "ml-engineer",
]
GERMAN_LOCATIONS = ["Deutschland", "Germany", "Berlin", "München", "Hamburg", "Stuttgart",
                    "Frankfurt", "Köln", "Düsseldorf", "Leipzig", "Dresden", "Bonn", "Nürnberg"]
# All 2019 Common Crawl indexes
INDEXES_2019 = [
    "CC-MAIN-2019-04", "CC-MAIN-2019-09", "CC-MAIN-2019-13", "CC-MAIN-2019-18",
    "CC-MAIN-2019-22", "CC-MAIN-2019-26", "CC-MAIN-2019-30", "CC-MAIN-2019-35",
    "CC-MAIN-2019-39", "CC-MAIN-2019-43", "CC-MAIN-2019-47", "CC-MAIN-2019-51"
]
TARGET_RECORDS = 200

# Link-following controls
MAX_LINKS_PER_LISTING = 10
VISITED_URLS = set()
SKIPPED_URLS = set()  # Cache of URLs we've determined are not relevant
JOB_LINK_PATTERNS = [
    r"job", r"jobs", r"stellen", r"stellenangebot", r"stellenangebote",
    r"karriere", r"career", r"careers", r"vacancy", r"vacancies", r"position", r"bewerb"
]

# Fast pre-screening keywords (case-insensitive substrings for quick check)
QUICK_CHECK_KEYWORDS = [
    "ki", "ai", "ml", "machine learning", "deep learning", "nlp", 
    "data scien", "pytorch", "tensorflow", "computer vision"
]

# Directory to save raw HTML pages for relevant job postings
HTML_SAVE_DIR = "datasets/job_pages_2019"

# Multi-job detection threshold
MIN_JOB_LINKS_FOR_LISTING_PAGE = 5
MIN_DESCRIPTION_LENGTH = 100

# -------------------- HELPERS --------------------
def clean_text(txt):
    if not txt: return ""
    txt = BeautifulSoup(txt, "html.parser").get_text(" ", strip=True)
    txt = re.sub(r"\s+", " ", txt).strip()
    return txt

# --- Keyword matching (boundary-aware) ---
_WORD_CHARS = "A-Za-z0-9ÄÖÜäöüß"

def _build_keyword_regexps(keywords):
    """Precompile boundary-aware regex patterns for keywords.
    Matches when keyword is surrounded by non-letter/digit (including start/end).
    Deduplicates while preserving order. Case-insensitive.
    """
    seen = set()
    regs = []  # list of tuples (keyword_trimmed, compiled_regex)
    for k in keywords:
        kw = (k or "").strip()
        if not kw:
            continue
        key = kw.lower()
        if key in seen:
            continue
        seen.add(key)
        pat = rf"(?<![{_WORD_CHARS}]){re.escape(kw)}(?![{_WORD_CHARS}])"
        regs.append((kw, re.compile(pat, flags=re.IGNORECASE)))
    return regs

KEYWORD_REGEXPS = _build_keyword_regexps(KEYWORDS)

def is_relevant(text):
    if not text:
        return False
    for _, rx in KEYWORD_REGEXPS:
        if rx.search(text):
            return True
    return False

def quick_relevance_check(text):
    """Fast pre-screen using simple substring matching before expensive regex.
    Returns True if text might contain keywords (needs full validation).
    This is much faster than regex and helps skip obviously irrelevant pages early.
    """
    if not text:
        return False
    text_lower = text.lower()
    # Quick substring check for common AI/ML terms
    return any(kw in text_lower for kw in KEYWORDS)

def get_matched_keywords(text):
    """Return a list of matched keywords (preserving order, deduplicated) using boundary-aware regexes."""
    if not text:
        return []
    hits = []
    for kw, rx in KEYWORD_REGEXPS:
        try:
            if rx.search(text):
                hits.append(kw)
        except Exception:
            # In case a malformed regex slipped through
            continue
    # de-duplicate while preserving order
    seen = set()
    out = []
    for k in hits:
        lk = k.lower()
        if lk not in seen:
            seen.add(lk)
            out.append(k)
    return out

def fetch_index_records(index, domain):
    api = f"https://index.commoncrawl.org/{index}-index?url={domain}*&output=json"
    try:
        res = requests.get(api, timeout=60)
        return [json.loads(l) for l in res.text.splitlines() if l.strip()]
    except Exception as e:
        print(f"Index fetch failed for {domain} in {index}: {e}")
        return []

def fetch_index_record_for_url(url, prefer_index=None):
    """Lookup an exact URL across 2019 CC indexes; prefer one index first if given."""
    indexes = INDEXES_2019.copy()
    if prefer_index in indexes:
        indexes.remove(prefer_index)
        indexes = [prefer_index] + indexes
    q = quote(url, safe='')
    for idx in indexes:
        try:
            api = f"https://index.commoncrawl.org/{idx}-index?url={q}&output=json"
            res = requests.get(api, timeout=30)
            lines = [json.loads(l) for l in res.text.splitlines() if l.strip()]
            if lines:
                rec = lines[0]
                rec['index'] = idx
                return rec
        except Exception:
            continue
    return None

def fetch_html_soup_from_rec(rec):
    """Fetch BeautifulSoup, raw text, and html string for a given CC index record via byte-range request."""
    try:
        cc_url = f"https://data.commoncrawl.org/{rec['filename']}"
        off, length = int(rec['offset']), int(rec['length'])
        headers = {'Range': f"bytes={off}-{off+length-1}"}
        r = requests.get(cc_url, headers=headers, timeout=60)
        stream = BytesIO(r.content)
        for entry in ArchiveIterator(stream):
            if entry.rec_type == "response":
                html = entry.content_stream().read()
                # Fast pre-check: decode a sample and do quick keyword check
                try:
                    html_str = html.decode("utf-8", errors="ignore")
                except Exception:
                    html_str = str(html)
                
                # Quick relevance check before expensive BeautifulSoup parsing
                if not quick_relevance_check(html_str):
                    return None, None, None
                
                soup = BeautifulSoup(html, "html.parser")
                text = soup.get_text(" ", strip=True)
                
                return soup, text, html_str
    except Exception:
        return None, None, None
    return None, None, None

def sanitize_filename(name: str) -> str:
    name = name.strip()
    # Replace forbidden characters and collapse spaces
    name = re.sub(r"[\\/:*?\"<>|]", "_", name)
    name = re.sub(r"\s+", " ", name)
    name = name.strip().rstrip(".")
    # Limit length to avoid OS issues
    return name[:120] if len(name) > 120 else name

def save_html_for_job(title: str, html_str: str, url: str):
    try:
        if not html_str:
            return
        os.makedirs(HTML_SAVE_DIR, exist_ok=True)
        base = sanitize_filename(title) if title else ""
        if not base:
            # fallback to hash of URL
            short = hashlib.md5((url or "").encode("utf-8")).hexdigest()[:10]
            base = f"job_{short}"
        filename = f"{base}.html"
        path = os.path.join(HTML_SAVE_DIR, filename)
        # If exists, append short hash to ensure uniqueness
        if os.path.exists(path):
            short = hashlib.md5((url or title).encode("utf-8")).hexdigest()[:8]
            path = os.path.join(HTML_SAVE_DIR, f"{base}_{short}.html")
        with open(path, "w", encoding="utf-8") as f:
            f.write(html_str)
    except Exception:
        # Non-fatal
        pass

def extract_from_warc(rec):
    soup, text, html_str = fetch_html_soup_from_rec(rec)
    if soup is None or not text:
        return None
    
    # Check if this is a multi-job listing page
    if is_multi_job_listing_page(soup, rec.get("url", "")):
        # Return special marker to trigger link-following workflow
        return "MULTI_JOB_PAGE"
    
    # Now do the precise boundary-aware keyword matching
    matched_list = get_matched_keywords(text)
    relevant_flag = bool(matched_list)
    
    if not relevant_flag:
        # Add to skipped URLs to avoid re-processing
        url = rec.get("url")
        if url:
            SKIPPED_URLS.add(url)
        return None
    
    # structure extraction
    title = soup.find(["h1","h2"])
    title = clean_text(title.text if title else "")
    # heuristic company/location extraction
    body = clean_text(text)
    
    # Validate that job has meaningful description
    if not has_valid_description(body):
        return None
    
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
        "source": ("indeed_de" if "indeed" in rec.get("url","")
                   else "stepstone_de" if "stepstone" in rec.get("url","")
                   else "xing_jobs"),
        "timestamp": rec.get("timestamp"),
        "job_title": title,
        "company": company,
        "location": location,
        "job_description": body[:15000],
        "is_relevant": bool(relevant_flag),
        "matched_keywords": ", ".join(matched_list),
        "_html": html_str
    }

def extract_candidate_hrefs(soup, base_url):
    """Extract likely job detail links from a page and resolve to absolute URLs."""
    candidates = []
    for a in soup.find_all('a', href=True):
        href = a['href']
        text = (a.get_text(" ", strip=True) or "")
        abs_url = urljoin(base_url, href)
        path = abs_url.lower()
        # Use job-like path substrings OR boundary-aware keyword matches in anchor text
        if any(p in path for p in JOB_LINK_PATTERNS) or any(rx.search(text) for _, rx in KEYWORD_REGEXPS):
            candidates.append(abs_url)
    # deduplicate preserve order
    seen = set()
    unique = []
    for u in candidates:
        if u not in seen:
            seen.add(u)
            unique.append(u)
    return unique

def is_multi_job_listing_page(soup, base_url):
    """Detect if page contains multiple job listings (listing/search results page)."""
    job_links = extract_candidate_hrefs(soup, base_url)
    # If page has many job-like links, it's likely a listing page not a single job detail
    return len(job_links) >= MIN_JOB_LINKS_FOR_LISTING_PAGE

def has_valid_description(description):
    """Check if job description is meaningful (not empty, has minimum content)."""
    if not description:
        return False
    clean = description.strip()
    return len(clean) >= MIN_DESCRIPTION_LENGTH

def crawl_links_from_rec(rec, limit=MAX_LINKS_PER_LISTING):
    """Follow a limited number of candidate links from a listing page and extract jobs."""
    jobs_found = []
    soup, _, _ = fetch_html_soup_from_rec(rec)
    if soup is None:
        return jobs_found
    base_url = rec.get("url", "")
    links = extract_candidate_hrefs(soup, base_url)
    count = 0
    for url in links:
        if count >= limit:
            break
        # Skip if already visited or previously determined irrelevant
        if url in VISITED_URLS or url in SKIPPED_URLS:
            continue
        VISITED_URLS.add(url)
        child_rec = fetch_index_record_for_url(url, prefer_index=rec.get('index'))
        if not child_rec:
            continue
        job = extract_from_warc(child_rec)
        # Skip if multi-job page marker or None
        if job == "MULTI_JOB_PAGE":
            # Recursively follow links (but don't count toward limit to avoid infinite depth)
            continue
        if job:
            # Validate description before saving
            if not has_valid_description(job.get("job_description", "")):
                continue
            # Save HTML only for confirmed jobs to be stored
            try:
                save_html_for_job(job.get("job_title", ""), job.get("_html"), job.get("url"))
            except Exception:
                pass
            jobs_found.append(job)
            count += 1
    return jobs_found

# -------------------- MAIN PIPELINE --------------------
jobs = []
for index in INDEXES_2019[::-1]:
    for domain in DOMAINS:
        records = fetch_index_records(index, domain)
        for rec in tqdm(records, desc=f"{index}-{domain}"):
            try:
                rec['index'] = index
                job = extract_from_warc(rec)
                
                # Handle multi-job listing pages
                if job == "MULTI_JOB_PAGE":
                    # Extract all job links and process individually
                    linked_jobs = crawl_links_from_rec(rec)
                    if linked_jobs:
                        jobs.extend(linked_jobs)
                elif job:
                    # Single job page - validate description before saving
                    if not has_valid_description(job.get("job_description", "")):
                        continue
                    # Save HTML only when the job is confirmed to be stored
                    try:
                        save_html_for_job(job.get("job_title", ""), job.get("_html"), job.get("url"))
                    except Exception:
                        pass
                    jobs.append(job)
                else:
                    # Not relevant or no content - try link-following as fallback
                    linked_jobs = crawl_links_from_rec(rec)
                    if linked_jobs:
                        jobs.extend(linked_jobs)
                
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
         "job_description","posting_date","is_relevant","matched_keywords"]]

df.to_csv("jobs_20192.csv", index=False)
print("💾 Saved to jobs_20192.csv")