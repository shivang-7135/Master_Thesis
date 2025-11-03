"""
geo_distribution_ai_ml.py
---------------------------------------
Generates Table 2–style geographical distribution of
AI and ML jobs (based on Verma et al., 2021).

It calculates the percentage of AI and ML jobs
per German Bundesland (state), ranks them, and
exports results for all years combined and
individual years (2019 / 2025).

Input CSV must have at least these columns:
job_id, year, job_domain_keywords, city, state
"""

import pandas as pd
import re, os

# ------------------------------
# 1️⃣ Load dataset
# ------------------------------
INPUT_FILE = "/Users/shivangsinha/Downloads/Drive A/Thesis/Master_Thesis/datasetConcat2019-25/data/processed/jobs_with_skills_combined.csv"   # adjust as needed
OUTPUT_DIR = "/Users/shivangsinha/Downloads/Drive A/Thesis/Master_Thesis/datasetConcat2019-25/data/processed"
os.makedirs(OUTPUT_DIR, exist_ok=True)

df = pd.read_csv(INPUT_FILE)
print(f"📘 Loaded {len(df)} records with columns: {list(df.columns)}")

# ------------------------------
# 2️⃣ Domain detection (AI / ML / both, English + German)
# ------------------------------
def detect_domains(x):
    """Return list of domains ('AI', 'ML') found in the job_domain_keywords."""
    if not isinstance(x, str):
        return []
    x_low = x.lower()
    domains = set()

    # AI keywords (English + German)
    if any(term in x_low for term in [
        "artificial intelligence", "ai", "künstliche intelligenz", "kuenstliche intelligenz", "ki"
    ]):
        domains.add("AI")

    # ML keywords (English + German)
    if any(term in x_low for term in [
        "machine learning", "ml", "maschinelles lernen", "deep learning"
    ]):
        domains.add("ML")

    return list(domains)


# ------------------------------
# 3️⃣ Expand dataset for dual-domain postings
# ------------------------------
expanded_rows = []
for _, row in df.iterrows():
    domains = detect_domains(row.get("job_domain_keywords", ""))
    if not domains:
        continue  # skip postings without AI/ML reference
    for d in domains:
        new_row = row.copy()
        new_row["domain"] = d
        expanded_rows.append(new_row)

df = pd.DataFrame(expanded_rows)
print(f"✅ Expanded dataset → {len(df)} rows (AI/ML counted separately where both apply)")

# Drop rows without state info
df = df.dropna(subset=["state"])
print(f"✅ Retained {len(df)} rows with valid 'state' values")

# ------------------------------
# 4️⃣ Compute geographical distribution
# ------------------------------
def compute_geo_distribution(subdf, domain):
    """Return dataframe with Rank–State–Percentage for a given domain subset."""
    data = subdf[subdf["domain"] == domain]
    if data.empty:
        return pd.DataFrame(columns=["Rank","State","Percentage","Domain"])
    counts = data["state"].value_counts()
    total = counts.sum()
    pct = (counts / total * 100).round(2)
    geo_df = pd.DataFrame({
        "Rank": range(1, len(pct)+1),
        "State": pct.index,
        "Percentage": pct.values,
        "Domain": domain
    })
    return geo_df


# ------------------------------
# 5️⃣ Combined-year summary (all years)
# ------------------------------
ai_all = compute_geo_distribution(df, "AI")
ml_all = compute_geo_distribution(df, "ML")

geo_combined = pd.merge(
    ai_all[["Rank","State","Percentage"]],
    ml_all[["Rank","State","Percentage"]],
    on="Rank", how="outer", suffixes=(" (AI)", " (ML)")
)

combined_out = os.path.join(OUTPUT_DIR, "geo_distribution_ai_ml_all.csv")
geo_combined.to_csv(combined_out, index=False)
print(f"📊 Saved combined geographical distribution → {combined_out}\n")
print("📈 Top 5 overall (like Verma et al. Table 2):")
print(geo_combined.head(5))


# ------------------------------
# 6️⃣ Year-wise summaries
# ------------------------------
for year in sorted(df["year"].dropna().unique()):
    sub = df[df["year"] == year]
    ai_y = compute_geo_distribution(sub, "AI")
    ml_y = compute_geo_distribution(sub, "ML")

    geo_y = pd.merge(
        ai_y[["Rank","State","Percentage"]],
        ml_y[["Rank","State","Percentage"]],
        on="Rank", how="outer", suffixes=(" (AI)", " (ML)")
    )

    outfile = os.path.join(OUTPUT_DIR, f"geo_distribution_ai_ml_{int(year)}.csv")
    geo_y.to_csv(outfile, index=False)
    print(f"📄 Saved → {outfile}")


# ------------------------------
# 7️⃣ Detailed per-year/domain/state summary
# ------------------------------
summary = (
    df.groupby(["year","domain","state"])
      .size()
      .reset_index(name="count")
)

summary["percentage"] = (
    summary.groupby(["year","domain"])["count"]
    .transform(lambda x: round(x / x.sum() * 100, 2))
)
print(df.groupby(["year","domain"]).size())

detail_out = os.path.join(OUTPUT_DIR, "geo_distribution_detailed.csv")
summary.to_csv(detail_out, index=False)
print(f"🗺️ Saved detailed distribution → {detail_out}")

# ------------------------------
# 8️⃣ Quick overview
# ------------------------------
print("\n📊 Domain totals by year:")
print(df.groupby(["year","domain"]).size())
print("\n✅ Done! All files stored in:", OUTPUT_DIR)
