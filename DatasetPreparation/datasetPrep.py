import pandas as pd
import re
from bs4 import BeautifulSoup

# ---------------------------
# 1. Load the datasets
# ---------------------------
# Replace with your file paths
df_2025 = pd.read_csv("/Users/shivangsinha/Downloads/Drive A/Thesis/Master_Thesis/datasets/dataset_indeed_2025-07-07.csv")
df_2019 = pd.read_csv("/Users/shivangsinha/Downloads/Drive A/Thesis/Master_Thesis/datasets/jobs_2019.csv")

# ---------------------------
# 2. Preprocess 2019 dataset
# ---------------------------
def clean_text(text):
    if pd.isna(text):
        return ""
    # Remove HTML tags if any
    text = BeautifulSoup(str(text), "html.parser").get_text(separator=" ")
    # Normalize whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text
# ---------------------------
# 3. Preprocess 2019 dataset
# ---------------------------
df_2019["job_id"] = df_2019["job_id"].fillna("")
df_2019["year"] = 2019

# Clean and combine text
df_2019["job_title"] = df_2019["job_title"].fillna("")
df_2019["company"] = df_2019["company"].fillna("")
df_2019["location"] = df_2019["location"].fillna("")
df_2019["job_text"] = (
    df_2019["job_title"].astype(str) + " " + df_2019["job_description"].astype(str)
).apply(clean_text)

# Ensure skills_required exists
if "skills_required" not in df_2019.columns:
    df_2019["skills_required"] = ""
df_2019["skills_required"] = df_2019["skills_required"].fillna("")

# Posting date handling
if "posting_date" in df_2019.columns:
    df_2019["posting_date"] = pd.to_datetime(df_2019["posting_date"]).dt.date
elif "archive_timestamp" in df_2019.columns:
    df_2019["posting_date"] = pd.to_datetime(df_2019["archive_timestamp"],format="%Y-%m-%d",  errors="coerce").dt.date
else:
    df_2019["posting_date"] = pd.NaT

df_2019 = df_2019[["job_id", "year", "job_title", "company", "location", "job_text", "skills_required", "posting_date"]]

# ---------------------------
# 4. Preprocess 2025 dataset
# ---------------------------
df_2025["job_id"] = [f"2025_{i+1:04d}" for i in range(len(df_2025))]
df_2025["year"] = 2025

df_2025["job_title"] = df_2025.get("positionName", "").fillna("")
df_2025["company"] = df_2025.get("company", "").fillna("")
df_2025["location"] = df_2025.get("location", "").fillna("")

# Clean job text (title + description)
df_2025["job_text"] = (
    df_2025["job_title"].astype(str) + " " + df_2025["description"].astype(str)
).apply(clean_text)
# No skills_required in 2025
df_2025["skills_required"] = ""

# Normalize posting date
# if "postedAt" in df_2025.columns:
#     df_2025["posting_date"] = pd.to_datetime(df_2025["postedAt"],format="%Y-%m-%d",  errors="coerce").dt.date
if "postingDateParsed" in df_2025.columns:
    # Convert ISO timestamp to date
    df_2025["posting_date"] = pd.to_datetime(df_2025["postingDateParsed"]).dt.date
else:
    df_2025["posting_date"] = pd.NaT


df_2025 = df_2025[["job_id", "year", "job_title", "company", "location", "job_text", "skills_required", "posting_date"]]

# ---------------------------
# 5. Concatenate unified dataset
# ---------------------------
df_all = pd.concat([df_2019, df_2025], ignore_index=True)

# ---------------------------
# 6. Save output
# ---------------------------
df_all.to_csv("unified_jobs_dataset.csv", index=False)

print("✅ Preprocessing complete. Unified dataset saved as unified_jobs_dataset.csv")
print(df_all.sample(5))