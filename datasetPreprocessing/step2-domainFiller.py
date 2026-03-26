"""
add_ai_ml_keywords_and_classify_fixed.py
----------------------------------------
Annotates existing AI/ML job postings with keyword families (Machine Learning / Artificial Intelligence),
tolerates cases like "machinelearning" or "Machine LearningAlgorithmen",
is accent- and separator-insensitive, and keeps all rows.
"""

import re
import unicodedata
import pandas as pd
import os

# -------------------------------
# 1️⃣ Load dataset
# -------------------------------
INPUT_PATH = "/Users/shivangsinha/Downloads/Drive A/Thesis/Master_Thesis/data/filtered/jobs_2019_with_titles.csv"
OUTPUT_DIR = "data/finaldataset"
os.makedirs(OUTPUT_DIR, exist_ok=True)

df = pd.read_csv(INPUT_PATH)
print(f"📂 Loaded dataset: {len(df)} rows, {len(df.columns)} columns")

# Detect main text column automatically
TEXT_COL = next(
    (c for c in ["job_text", "job_description", "description", "text", "content"]
     if c in df.columns),
    None
)
if TEXT_COL is None:
    raise ValueError("❌ No suitable text column found. Expected job_text/job_description/description/text/content")
print(f"🧠 Using text column: {TEXT_COL}")

# -------------------------------
# 2️⃣ Define canonical keyword families
# -------------------------------

RAW_KEYWORDS = {
    "machine learning": [
        "ml", "machine learning", "maschinelles lernen","deep learning","data science","tiefes lernen"
        "lernende systeme", "selbstlernende systeme",
        "überwachtes lernen", "unüberwachtes lernen", "verstärkendes lernen",
        "datengetriebene modelle", "predictive analytics", "modelltraining"
    ],
    "artificial intelligence": [
        "ai", "ki","neural network", "natural language processing", "nlp",
        "generative ai", "large language model", "llm", "llms","computer vision",
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
# ✅ allow *zero or more* separators, not just one (+ → *)
SEP = rf"(?:[\s_\-\/\.\u00B7\u00AD[{UNICODE_DASH_CLASS}]]*)"

def strip_accents(s: str) -> str:
    """Removes accents/diacritics."""
    return ''.join(ch for ch in unicodedata.normalize('NFKD', s)
                   if not unicodedata.combining(ch))

def normalize_text(t: str) -> str:
    """Lowercase, normalize and remove non-breaking spaces."""
    if not isinstance(t, str):
        return ""
    t = t.replace(NBSP, " ")
    t = strip_accents(t).lower()
    return t

# -------------------------------
# 4️⃣ Build tolerant regex patterns (final robust version)
# -------------------------------
patterns = []
for canonical, variants in RAW_KEYWORDS.items():
    for v in variants:
        v_norm = strip_accents(v.lower()).strip()

        # handle short forms like AI, ML, KI separately
        if v_norm in {"ai", "ml", "ki"}:
            letters = list(v_norm)
            dotted = rf"{letters[0]}(?:[.\-/\s\u00B7\u00AD[{UNICODE_DASH_CLASS}]])*{letters[1]}"
            pat = re.compile(dotted, re.IGNORECASE)
        else:
            # split into words and allow for optional or zero separators
            parts = re.split(r"\s+", v_norm)
            if len(parts) > 1:
                joined = SEP.join(map(re.escape, parts))
                # 🔑 add a fallback where parts are directly concatenated (machinelearning)
                no_sep = "".join(map(re.escape, parts))
                combined = rf"(?:{joined}|{no_sep})"
            else:
                combined = re.escape(v_norm)
            pat = re.compile(combined, re.IGNORECASE)

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
# 6️⃣ Generate keyword summary
# -------------------------------
def keyword_counts(series):
    """Creates a frequency table of keyword families."""
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
# 7️⃣ Save enriched dataset
# -------------------------------
output_path = f"{OUTPUT_DIR}/jobs_with_ai_ml_tags.csv"
df.to_csv(output_path, index=False)
print(f"\n💾 Saved enriched dataset → {output_path}")
print("✅ Done — all rows retained, detection tolerant to missing spaces and accents.")

# -------------------------------
# 8️⃣ Optional diagnostic test
# -------------------------------
print("\n🧪 Diagnostic test:")
test_cases = [
    "Machine Learning",
    "machinelearning",
    "MachineLearning",
    "machine-learning",
    "machine_learning",
    "Machine LearningAlgorithmen",
    "Künstliche Intelligenz",
    "AI-driven analytics",
    "KI Systeme"
]
for t in test_cases:
    print(f"{t} → {detect_ai_ml_terms(t)}")
