"""
add_ai_ml_keywords_and_classify.py
---------------------------------
Annotates existing AI/ML job postings with keyword families (ML / AI),
supports dotted & unicode separators, accent-insensitive matching,
and produces keyword frequency summaries — without filtering rows out.
"""

import re
import unicodedata
import pandas as pd
import os

# -------------------------------
# 1️⃣ Load dataset
# -------------------------------
INPUT_PATH = "/Users/shivangsinha/Downloads/Drive A/Thesis/Master_Thesis/unified_jobs_dataset.csv"
OUTPUT_DIR = "data"
os.makedirs(OUTPUT_DIR, exist_ok=True)

df = pd.read_csv(INPUT_PATH)
print(f"📂 Loaded dataset: {len(df)} rows, {len(df.columns)} columns")

# Detect the main text column automatically
TEXT_COL = next((c for c in ["job_text", "job_description", "description", "text", "content"]
                 if c in df.columns), None)
if TEXT_COL is None:
    raise ValueError("❌ No suitable text column found. Expected job_text/job_description/description/text/content")
print(f"🧠 Using text column: {TEXT_COL}")

# -------------------------------
# 2️⃣ Define canonical keyword families
# -------------------------------
RAW_KEYWORDS = {
    "machine learning": [
        "ml", "machine learning", "maschinelles lernen",
        "lernende systeme", "selbstlernende systeme",
        "überwachtes lernen", "unüberwachtes lernen", "verstärkendes lernen",
        "datengetriebene modelle", "predictive analytics", "modelltraining"
    ],
    "artificial intelligence": [
        "ai", "ki",
        "künstliche intelligenz", "kunstliche intelligenz", "kuenstliche intelligenz",
        "artificial intelligence", "artifical intelligence",
        "intelligente systeme", "intelligente algorithmen",
        "intelligente automatisierung", "maschinelle intelligenz"
    ]
}

# -------------------------------
# 3️⃣ Normalization utilities
# -------------------------------
NBSP = "\u00A0"
UNICODE_DASH_CLASS = r"\u2010-\u2015\u2212"  # – — ‒ ― −
SEP = rf"(?:[\s_\-\/\.\u00B7\u00AD[{UNICODE_DASH_CLASS}]]+)"  # accepted separators

def strip_accents(s: str) -> str:
    return ''.join(ch for ch in unicodedata.normalize('NFKD', s)
                   if not unicodedata.combining(ch))

def normalize_text(t: str) -> str:
    if not isinstance(t, str):
        return ""
    t = t.replace(NBSP, " ")
    t = strip_accents(t).lower()
    return t

# -------------------------------
# 4️⃣ Build tolerant regex patterns
# -------------------------------
patterns = []
for canonical, variants in RAW_KEYWORDS.items():
    for v in variants:
        v_norm = strip_accents(v.lower())
        if v_norm in {"ai", "ml", "ki"}:
            # allow dotted/slashed forms: A.I., M-L, etc.
            letters = list(v_norm)
            dotted = rf"{letters[0]}(?:[.\-/\s\u00B7\u00AD[{UNICODE_DASH_CLASS}]])?{letters[1]}"
            pat = re.compile(rf"{dotted}", re.IGNORECASE)
        else:
            esc = re.escape(v_norm)
            esc = esc.replace(r"\ ", SEP)
            pat = re.compile(rf"{esc}", re.IGNORECASE)
        patterns.append((canonical, pat))

# -------------------------------
# 5️⃣ Keyword detection
# -------------------------------
def detect_ai_ml_terms(text: str) -> str:
    t = normalize_text(text)
    if not t:
        return ""
    hits = set()
    for canonical, pat in patterns:
        if pat.search(t):
            hits.add(canonical)
    ordered = [k for k in RAW_KEYWORDS.keys() if k in hits]
    return ", ".join(ordered)

# Apply detection
print("🔍 Detecting AI/ML keyword families...")
df["job_domain_keywords"] = df[TEXT_COL].apply(detect_ai_ml_terms)

# -------------------------------
# 6️⃣ Generate keyword summaries
# -------------------------------
def keyword_counts(series):
    return (
        series.str.split(", ")
        .explode()
        .replace("", pd.NA)
        .dropna()
        .value_counts()
        .rename_axis("keyword")
        .reset_index(name="count")
    )

summary = keyword_counts(df["job_domain_keywords"])
summary.to_csv(f"{OUTPUT_DIR}/ai_ml_keyword_distribution.csv", index=False)

print("\n📊 Keyword summary:")
print(summary)

# -------------------------------
# 7️⃣ Save annotated dataset
# -------------------------------
df.to_csv(f"{OUTPUT_DIR}/jobs_with_ai_ml_tags.csv", index=False)
print(f"\n💾 Saved enriched dataset → {OUTPUT_DIR}/jobs_with_ai_ml_tags.csv")
print("✅ Done — no rows removed (dataset already AI/ML-specific).")
