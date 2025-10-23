import requests
from bs4 import BeautifulSoup
import pandas as pd
import time

# Base domain to target
domain = "https://de.indeed.com/rc/clk"

# CDX API to get Wayback snapshots
def get_snapshots(url, start_year, end_year):
    cdx_url = f"https://web.archive.org/cdx/search/cdx?url={url}&output=json&from={start_year}&to={end_year}"
    res = requests.get(cdx_url)
    data = res.json()[1:]  # Skip header
    snapshots = [f"https://web.archive.org/web/{row[1]}/{row[2]}" for row in data]
    return snapshots

# Parse job data from a snapshot page
def parse_job_page(url):
    try:
        res = requests.get(url, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')

        title = soup.find('h1')
        company = soup.find('div', {'class': 'icl-u-lg-mr--sm'})
        location = soup.find('div', {'class': 'jobsearch-JobInfoHeader-subtitle'})
        desc = soup.find('div', {'id': 'jobDescriptionText'})

        return {
            "url": url,
            "title": title.get_text(strip=True) if title else None,
            "company": company.get_text(strip=True) if company else None,
            "location": location.get_text(strip=True) if location else None,
            "description": desc.get_text(separator=' ', strip=True) if desc else None
        }
    except Exception as e:
        print(f"Error parsing {url}: {e}")
        return None

# Collect all job postings from snapshots
def collect_jobs(start_year=2021, end_year=2022, limit=10):
    snapshots = get_snapshots(domain, start_year, end_year)
    print(f"Found {len(snapshots)} snapshots")

    data = []
    for i, snap in enumerate(snapshots[:limit]):
        print(f"Scraping {i+1}/{limit}: {snap}")
        job_data = parse_job_page(snap)
        if job_data:
            data.append(job_data)
        time.sleep(2)  # polite delay

    df = pd.DataFrame(data)
    df.to_csv(f"indeed_jobs_{start_year}_{end_year}.csv", index=False)
    print(f"✅ Saved {len(df)} job records to indeed_jobs_{start_year}_{end_year}.csv")

collect_jobs(2016, 2024, limit=15)
