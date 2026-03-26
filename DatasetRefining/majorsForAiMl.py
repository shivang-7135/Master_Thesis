"""
generate_verma_table3_majors_by_year.py
Replicates Verma et al. Table 3 (Majors for AI & ML jobs),
computed separately for 2019 and 2025.
"""

import re, unicodedata, pandas as pd

# ---------- 1️⃣ Load dataset ----------
# Must contain columns: 'year', 'job_text', 'is_ai', 'is_ml'
df = pd.read_csv("/Users/shivangsinha/Downloads/Drive A/Thesis/Master_Thesis/jobs_2019_ai_ml_with_skill_categories.csv")

# ---------- 2️⃣ Helpers ----------
def norm(s: str) -> str:
    if not isinstance(s, str):
        return ""
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    return s.lower()

def compile_pat(k):
    esc = re.escape(k)
    esc = esc.replace(r"\ ", r"[\s\-_]+")
    # strict boundaries – no matches inside words like "email" or "xml"
    return re.compile(rf"(?<![A-Za-z0-9]){esc}(?![A-Za-z0-9])", re.IGNORECASE)

# ---------- 3️⃣ Majors dictionary (English + German) ----------
MAJORS = {
    "Machine learning": ["machine learning", "maschinelles lernen"],
    "Engineering": ["engineering", "engineer", "ingenieur", "ingenieurwesen"],
    "Business": ["business", "wirtschaft", "betriebswirtschaft", "bwl"],
    "Computer science": [
        "computer science", "informatics", "informatik", "software engineering"
    ],
    "Artificial intelligence": [
        "artificial intelligence", "künstliche intelligenz",
        "kunstliche intelligenz", "kuenstliche intelligenz", "ki"
    ],
    "Mathematics": ["mathematics", "math", "mathe", "mathematik"],
    "Data science": ["data science", "datenwissenschaft", "data analyst", "datenanalyse"],
    "Statistics": ["statistics", "statistik"]
}

MAJOR_PATTERNS = {m: [compile_pat(k) for k in kws] for m, kws in MAJORS.items()}

# ---------- 4️⃣ Detection ----------
def has_major(text, patterns):
    t = norm(text)
    for p in patterns:
        if p.search(t):
            return True
    return False

def detect_majors(text):
    return ", ".join(
        [m for m, pats in MAJOR_PATTERNS.items() if has_major(text, pats)]
    )

df["majors_detected"] = df["job_text"].astype(str).apply(detect_majors)

# ---------- 5️⃣ Subset & Computation ----------
def major_percentages(subdf):
    total = len(subdf)
    rows = []
    for m, pats in MAJOR_PATTERNS.items():
        cnt = subdf["job_text"].astype(str).apply(lambda x: has_major(x, pats)).sum()
        pct = round(cnt / total * 100, 2) if total else 0
        rows.append((m, pct))
    tbl = (
        pd.DataFrame(rows, columns=["Major", "Percentage count (%)"])
        .sort_values("Percentage count (%)", ascending=False)
        .reset_index(drop=True)
    )
    tbl.index = tbl.index + 1
    return tbl

# ---------- 6️⃣ Run for each year (2019 & 2025) ----------
results = []
for yr in [2019, 2025]:
    ai_df = df[(df["year"] == yr) & (df["is_ai"])]
    ml_df = df[(df["year"] == yr) & (df["is_ml"])]

    print(f"\n📅 Year {yr}: AI jobs = {len(ai_df)} | ML jobs = {len(ml_df)}")

    ai_table = major_percentages(ai_df)
    ml_table = major_percentages(ml_df)

    # Export separate files
    ai_table.to_csv(f"table3_ai_majors_{yr}.csv", index_label="Rank")
    ml_table.to_csv(f"table3_ml_majors_{yr}.csv", index_label="Rank")

    # Combine side-by-side (Verma-style layout)
    combined = pd.concat(
        [
            ai_table.rename(columns={"Major": "Major (AI jobs)", "Percentage count (%)": "AI (%)"}),
            ml_table.rename(columns={"Major": "Major (ML jobs)", "Percentage count (%)": "ML (%)"}),
        ],
        axis=1,
    )
    combined.to_csv(f"table3_majors_ai_ml_{yr}.csv", index_label="Rank")
    results.append((yr, combined))

    print("\nTop majors – AI jobs:")
    print(ai_table.head(7))
    print("\nTop majors – ML jobs:")
    print(ml_table.head(7))

# ---------- 7️⃣ Optional: Combine all years ----------
all_tables = []
for yr, tbl in results:
    t = tbl.copy()
    t["Year"] = yr
    all_tables.append(t)
pd.concat(all_tables).to_csv("table3_majors_ai_ml_2019_2025.csv", index=False)

print("\n✅ Generated Table 3-style major results for 2019 and 2025 successfully.")
