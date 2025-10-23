# """
# skill_extraction_table1_bilingual.py
# Replicates Table 1 (Verma et al. 2021) skill-classification framework
# and adds German-language equivalents.
# """

# import re
# import unicodedata
# import pandas as pd

# # ---------- 1️⃣  Load dataset ----------
# df = pd.read_csv("/Users/shivangsinha/Downloads/Drive A/Thesis/Master_Thesis/jobs_2019_ai_ml_with_city_state.csv")
"""
generate_verma_skill_tables_by_year.py
→ Detects skills (Table 1 + German)
→ Computes Verma-style skill-category percentages
→ Separates results for 2019 and 2025
"""

import re, unicodedata, pandas as pd
from collections import Counter

# ---------- 1️⃣ Load unified dataset ----------
df = pd.read_csv("/Users/shivangsinha/Downloads/Drive A/Thesis/Master_Thesis/jobs_2019_ai_ml_with_city_state.csv")  # must contain columns: job_text, year

# ---------- 2️⃣ Helpers ----------
def norm(s: str) -> str:
    if not isinstance(s, str): return ""
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    return s.lower()

def compile_pat(keyword: str) -> re.Pattern:
    esc = re.escape(keyword)
    esc = esc.replace(r"\ ", r"[\s\-_]+")
    return re.compile(rf"(?<!\w){esc}(?!\w)", re.IGNORECASE)

# ---------- 3️⃣ Table 1 skills (condensed bilingual set) ----------
SKILL_DICT = {
    "Decision making": ["decision making","analysis","analytical","strategic thinking",
                        "analyse","entscheidungsfindung"],
    "Data mining": ["data mining","classification","prediction","forecasting","machine learning",
                    "maschinelles lernen","datenanalyse"],
    "Programming": ["python","java","c++","r","scala","matlab","bash","javascript",
                    "programmierung","softwareentwicklung"],
    "Statistics": ["statistics","regression","spss","sas","stata","statistik","wahrscheinlichkeit"],
    "Big data": ["big data","spark","hadoop","hive","nosql","mapreduce","datenmenge"],
    "Attitude": ["can do","positive attitude","eigeninitiative","positiv"],
    "Time management": ["time management","deadline","zeitmanagement","fristgerecht"],
    "Motivation": ["motivated","ambition","willingness to learn","motiviert","lernwillig"],
    "Independence": ["independent","autonomous","selbstständig","autonom"],
    "Detail-oriented": ["attention to detail","accuracy","precision","detailorientiert","genauigkeit"],
    "Communication General": ["communication","kommunikation","communicative","kommunikativ"],
    "Verbal": ["verbal","oral","mündlich"],
    "Written": ["writing","written","schriftlich","textbearbeitung"],
    "Presentation": ["presentation","present","report","präsentation","vortrag"],
    "Interpersonal Team": ["team management","collaboration","teamwork","teamarbeit","zusammenarbeit"],
    "Interpersonal Personal": ["personal skills","soft skills","persönlichkeitskompetenz"],
    "Networking": ["networking","netzwerken"],
    "Problem solving": ["problem solving","troubleshoot","critical thinker",
                        "problemlösung","kritisches denken"],
    "Creativity": ["creative","out of box","innovative","kreativ"],
    "Process design": ["process design","continuous improvement","prozessdesign","prozessverbesserung"],
}

PATTERNS = [(cat, kw, compile_pat(kw)) for cat, kws in SKILL_DICT.items() for kw in kws]

# ---------- 4️⃣ Detect skills ----------
def detect_categories(text: str):
    t = norm(text)
    cats = {cat for cat, kw, pat in PATTERNS if pat.search(t)}
    return ", ".join(sorted(cats))

df["skill_category"] = df["job_description"].astype(str).apply(detect_categories)

# ---------- 5️⃣ Identify AI vs ML subset (strict word match) ----------

AI_KW = [
    "artificial intelligence",
    "künstliche intelligenz",
    "kunstliche intelligenz",
    "kuenstliche intelligenz",
    "ki","ai"
]

ML_KW = [
    "machine learning",
    "maschinelles lernen",
    "ml"
]

# Special handling for "ai" and "ml" as independent tokens only
AI_SHORT_PATTERN = re.compile(r"(?<![A-Za-z0-9])ai(?![A-Za-z0-9])", re.IGNORECASE)
ML_SHORT_PATTERN = re.compile(r"(?<![A-Za-z0-9])ml(?![A-Za-z0-9])", re.IGNORECASE)

def has_kw(text: str, kwlist, short_pattern=None):
    t = norm(text)
    for k in kwlist:
        if re.search(rf"(?<![A-Za-z0-9]){re.escape(k)}(?![A-Za-z0-9])", t):
            return True
    if short_pattern and short_pattern.search(t):
        return True
    return False

df["is_ai"] = df["job_description"].apply(lambda t: has_kw(t, AI_KW, short_pattern=AI_SHORT_PATTERN))
df["is_ml"] = df["job_description"].apply(lambda t: has_kw(t, ML_KW, short_pattern=ML_SHORT_PATTERN))

# ---------- 6️⃣ Percentage calculator ----------
def category_percentages(subdf):
    total = len(subdf)
    counter = Counter()
    for cats in subdf["skill_category"].dropna():
        for c in [x.strip() for x in cats.split(",") if x.strip()]:
            counter[c] += 1
    rows = [(c, round(counter[c]/total*100,2)) for c in counter if total>0]
    return pd.DataFrame(rows, columns=["Skill category","Percentage count (%)"]).sort_values(
        "Percentage count (%)", ascending=False)

# ---------- 7️⃣ Compute results for each year ----------
results = []
for yr in [2019, 2025]:
    ai_df = df[(df["year"]==yr) & (df["is_ai"])]
    ml_df = df[(df["year"]==yr) & (df["is_ml"])]

    ai_table = category_percentages(ai_df)
    ml_table = category_percentages(ml_df)

    ai_table.to_csv(f"table4_ai_{yr}.csv", index=False)
    ml_table.to_csv(f"table5_ml_{yr}.csv", index=False)

    results.append((yr,"AI",ai_table))
    results.append((yr,"ML",ml_table))

    print(f"\n📅 Year {yr}: AI jobs = {len(ai_df)}, ML jobs = {len(ml_df)}")
    print("Top 10 AI categories:")
    print(ai_table.head(10))
    print("\nTop 10 ML categories:")
    print(ml_table.head(10))

# ---------- 8️⃣ Combined summary (optional) ----------
all_tables = []
for yr, typ, tbl in results:
    tbl2 = tbl.copy()
    tbl2["Year"]=yr
    tbl2["Type"]=typ
    all_tables.append(tbl2)
pd.concat(all_tables).to_csv("verma_skill_tables_2019_2025.csv", index=False)

print("\n✅ Generated Verma-style Tables 4 & 5 for 2019 and 2025.")
