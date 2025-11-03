"""
Finds and fills missing city/state information using job descriptions from another CSV file
"""
import pandas as pd
import unicodedata
import re
import requests
import time

# File paths
PRIMARY_CSV = "/Users/shivangsinha/Downloads/Drive A/Thesis/Master_Thesis/datasetConcat2019-25/jobs_ai_ml_with_city_state.csv"
SECONDARY_CSV = "/Users/shivangsinha/Downloads/Drive A/Thesis/Master_Thesis/datasets/filtered_jobs_2019.csv"
OUTPUT_CSV = "/Users/shivangsinha/Downloads/Drive A/Thesis/Master_Thesis/datasetConcat2019-25/jobs_ai_ml_with_city_state_filled.csv"

# ---------- HELPERS ----------
def normalize(s: str) -> str:
    if not isinstance(s, str): 
        return ""
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    return s.strip().lower()

def wb(pat: str) -> re.Pattern:
    """Regex builder with safe boundaries. Short aliases (≤3 chars) must be standalone."""
    esc = re.escape(pat)
    if len(pat) <= 3:
        pattern = rf"(?<![A-Za-z0-9]){esc}(?![A-Za-z0-9])"
    else:
        pattern = rf"(?<!\w){esc}(?!\w)"
    return re.compile(pattern)

# ---------- states (Bundesländer) with aliases ----------
STATE_ALIASES = {
    "Baden-Württemberg": ["baden-wuerttemberg","baden wurttemberg","baden-wurttemberg"],
    "Bayern": ["bayern","bavaria"],
    "Berlin": ["berlin"],
    "Brandenburg": ["brandenburg"],
    "Bremen": ["bremen"],
    "Hamburg": ["hamburg"],
    "Hessen": ["hessen","hesse","hesse state"],
    "Mecklenburg-Vorpommern": ["mecklenburg-vorpommern","mecklenburg vorpommern"],
    "Niedersachsen": ["niedersachsen","lower saxony","lowersaxony"],
    "Nordrhein-Westfalen": ["nordrhein-westfalen","nordrhein westfalen","north rhine-westphalia"],
    "Rheinland-Pfalz": ["rheinland-pfalz","rheinland pfalz","rhineland-palatinate"],
    "Saarland": ["saarland"],
    "Sachsen": ["sachsen","saxony"],
    "Sachsen-Anhalt": ["sachsen-anhalt","sachsen anhalt","saxony-anhalt"],
    "Schleswig-Holstein": ["schleswig-holstein","schleswig holstein"],
    "Thüringen": ["thueringen","thuringen","thüringen","thuringia"],
}

# compile state patterns
STATE_PATTERNS = []
for canon, aliases in STATE_ALIASES.items():
    for a in aliases + [canon]:
        STATE_PATTERNS.append((canon, wb(normalize(a))))

# ---------- city → state mapping with rich aliases ----------
CITY_TO_STATE = {
    # NRW
    "Köln": "Nordrhein-Westfalen",
    "Düsseldorf": "Nordrhein-Westfalen",
    "Dortmund": "Nordrhein-Westfalen",
    "Essen": "Nordrhein-Westfalen",
    "Duisburg": "Nordrhein-Westfalen",
    "Bonn": "Nordrhein-Westfalen",
    "Bochum": "Nordrhein-Westfalen",
    "Bielefeld": "Nordrhein-Westfalen",
    "Wuppertal": "Nordrhein-Westfalen",
    "Aachen": "Nordrhein-Westfalen",
    "Münster": "Nordrhein-Westfalen",
    "Leverkusen": "Nordrhein-Westfalen",
    "Mönchengladbach": "Nordrhein-Westfalen",
    "Hagen": "Nordrhein-Westfalen",
    # Bayern
    "München": "Bayern",
    "Nürnberg": "Bayern",
    "Augsburg": "Bayern",
    "Regensburg": "Bayern",
    "Ingolstadt": "Bayern",
    "Würzburg": "Bayern",
    "Erlangen": "Bayern",
    "Fürth": "Bayern",
    "Passau": "Bayern",
    "Landshut": "Bayern",
    "Bamberg": "Bayern",
    "Bayreuth": "Bayern",
    "Alzenau": "Bayern",
    "Aschaffenburg": "Bayern",
    "Schweinfurt": "Bayern",
    "Kempten": "Bayern",
    "Coburg": "Bayern",
    "Memmingen": "Bayern",
    # BW
    "Stuttgart": "Baden-Württemberg",
    "Karlsruhe": "Baden-Württemberg",
    "Mannheim": "Baden-Württemberg",
    "Heidelberg": "Baden-Württemberg",
    "Freiburg im Breisgau": "Baden-Württemberg",
    "Ulm": "Baden-Württemberg",
    "Heilbronn": "Baden-Württemberg",
    "Reutlingen": "Baden-Württemberg",
    "Tübingen": "Baden-Württemberg",
    "Konstanz": "Baden-Württemberg",
    "Sindelfingen": "Baden-Württemberg",
    "Böblingen": "Baden-Württemberg",
    "Esslingen": "Baden-Württemberg",
    "Pforzheim": "Baden-Württemberg",
    "Lörrach": "Baden-Württemberg",
    "Rastatt": "Baden-Württemberg",
    # HE
    "Frankfurt am Main": "Hessen",
    "Wiesbaden": "Hessen",
    "Darmstadt": "Hessen",
    "Kassel": "Hessen",
    # NI
    "Hannover": "Niedersachsen",
    "Braunschweig": "Niedersachsen",
    "Oldenburg": "Niedersachsen",
    "Osnabrück": "Niedersachsen",
    "Göttingen": "Niedersachsen",
    # HH / HB / BE
    "Hamburg": "Hamburg",
    "Bremen": "Bremen",
    "Berlin": "Berlin",
    # SN
    "Leipzig": "Sachsen",
    "Dresden": "Sachsen",
    "Chemnitz": "Sachsen",
    "Zwickau": "Sachsen",
    # ST
    "Halle (Saale)": "Sachsen-Anhalt",
    "Magdeburg": "Sachsen-Anhalt",
    # TH
    "Erfurt": "Thüringen",
    "Jena": "Thüringen",
    "Gera": "Thüringen",
    # RP
    "Mainz": "Rheinland-Pfalz",
    "Koblenz": "Rheinland-Pfalz",
    "Trier": "Rheinland-Pfalz",
    "Ingelheim": "Rheinland-Pfalz",
    "Bellheim": "Rheinland-Pfalz",
    # SH
    "Kiel": "Schleswig-Holstein",
    "Lübeck": "Schleswig-Holstein",
    "Flensburg": "Schleswig-Holstein",
    # MV
    "Rostock": "Mecklenburg-Vorpommern",
    "Schwerin": "Mecklenburg-Vorpommern",
    # SL
    "Saarbrücken": "Saarland",
    # BB
    "Potsdam": "Brandenburg",
}

# city aliases (ASCII + English + common variants)
CITY_ALIASES = {
    "Köln": ["köln","koln","koeln","cologne"],
    "Düsseldorf": ["düsseldorf","duesseldorf","dusseldorf"],
    "München": ["münchen","muenchen","munchen","munich"],
    "Nürnberg": ["nürnberg","nuernberg","nuremberg"],
    "Freiburg im Breisgau": ["freiburg im breisgau","freiburg"],
    "Frankfurt am Main": ["frankfurt am main","frankfurt"],
    "Mönchengladbach": ["mönchengladbach","moenchengladbach","monchengladbach"],
    "Göttingen": ["göttingen","goettingen","gottingen"],
    "Lübeck": ["lübeck","luebeck","lubeck"],
    "Saarbrücken": ["saarbrücken","saarbruecken","saarbrucken"],
}

# ensure every canonical has at least itself as alias
for city in list(CITY_TO_STATE.keys()):
    CITY_ALIASES.setdefault(city, [city])

# compile city patterns mapping alias_norm -> (canonical_city, canonical_state, regex)
CITY_PATTERNS = []
for canon_city, aliases in CITY_ALIASES.items():
    state = CITY_TO_STATE[canon_city]
    for a in aliases:
        CITY_PATTERNS.append((canon_city, state, wb(normalize(a))))

def geocode_location(loc: str):
    """Query OSM Nominatim for city/state when not found locally."""
    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": f"{loc}, Germany", "format": "json", "addressdetails": 1, "limit": 1}
    try:
        r = requests.get(url, params=params, headers={"User-Agent": "ThesisGeocoder/1.0"})
        if r.ok and r.json():
            addr = r.json()[0]["address"]
            city = addr.get("city") or addr.get("town") or addr.get("village") or ""
            state = addr.get("state") or ""
            return city, state
    except Exception:
        pass
    return "", ""

def extract_city_state(text):
    """Extract city and state from given text."""
    if not text:
        return "", ""

    norm_text = normalize(text)

    # Try local dictionary (fast)
    for city, state, pat in CITY_PATTERNS:
        if pat.search(norm_text):
            return city, state

    # Try state patterns
    for state, pat in STATE_PATTERNS:
        if pat.search(norm_text):
            return "", state

    return "", ""

def main():
    print("Loading CSV files...")
    # Load primary CSV with missing city/state info
    df_primary = pd.read_csv(PRIMARY_CSV)
    
    # Load secondary CSV with job descriptions
    df_secondary = pd.read_csv(SECONDARY_CSV)

    # Create a mapping from job_id to job_description
    job_desc_map = df_secondary.set_index('job_id')['job_description'].to_dict()

    # Counter for updates
    updates = 0
    
    print("Processing rows with missing city/state information...")
    # Iterate through primary dataframe rows that have missing city or state
    for idx, row in df_primary.iterrows():
        if pd.isna(row['city']) or pd.isna(row['state']) or row['city'] == '' or row['state'] == '':
            # Try to find corresponding job in secondary CSV
            job_id = row['job_id']
            if job_id in job_desc_map:
                # Get job description from secondary CSV
                job_desc = job_desc_map[job_id]
                
                # Try to extract city and state from job description
                extracted_city, extracted_state = extract_city_state(job_desc)
                
                # Update if we found something
                if extracted_city or extracted_state:
                    if extracted_city:
                        df_primary.at[idx, 'city'] = extracted_city
                    if extracted_state:
                        df_primary.at[idx, 'state'] = extracted_state
                    updates += 1

                    if updates % 100 == 0:
                        print(f"Processed {updates} updates...")

    print(f"Completed processing. Made {updates} updates.")
    print(f"Saving results to {OUTPUT_CSV}")
    df_primary.to_csv(OUTPUT_CSV, index=False)
    print("Done!")

if __name__ == "__main__":
    main()
