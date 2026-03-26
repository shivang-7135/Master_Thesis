"""
add_city_state_from_text.py
Extracts German city & state from location/title/text with umlaut/alias support.
"""
import re
import unicodedata
import pandas as pd
import requests
import time

# ---------- IO ----------
INFILE  = "/Users/shivangsinha/Downloads/Drive A/Thesis/Master_Thesis/data/finaldataset/jobs_with_ai_ml_tags.csv"   # or your current file
OUTFILE = "/Users/shivangsinha/Downloads/Drive A/Thesis/Master_Thesis/data/finaldataset/jobs_ai_ml_with_city_state.csv"

df = pd.read_csv(INFILE)

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
    # add one-to-one aliases for all canonical keys not listed above
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

# ---------- NOMINATIM FALLBACK ----------
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

# ---------- EXTRACTION FUNCTION ----------
def extract_city_state(row):
    loc = str(row.get("location", "") or "")
    text = str(row.get("job_text", "") or "")
    title = str(row.get("job_title", "") or "")
    all_text = f"{loc} {title} {text}"

    norm_text = normalize(all_text)

    # # 1️⃣ Skip Germany-only locations
    # if re.fullmatch(r"(germany|deutschland)", normalize(loc)):
    #     return pd.Series({"city": "", "state": "Germany"})

    # 2️⃣ Try local dictionary (fast)
    for city, state, pat in CITY_PATTERNS:
        if pat.search(norm_text):
            return pd.Series({"city": city, "state": state})

    # 3️⃣ API fallback (for non-empty, non-Germany locations)
    if loc.strip() and len(loc.strip()) > 2:
        city, state = geocode_location(loc)
        if city or state:
            time.sleep(1)  # rate limit for Nominatim
            return pd.Series({"city": city, "state": state})

    return pd.Series({"city": "", "state": ""})

# ---------- APPLY ----------
df[["city", "state"]] = df.apply(extract_city_state, axis=1)
df.to_csv(OUTFILE, index=False)

print(f"✅ Saved enriched file: {OUTFILE}")
print(df[["location","city","state"]].head(10))
