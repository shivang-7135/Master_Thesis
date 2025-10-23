#!/usr/bin/env python3
import argparse
import re
import sys
import pandas as pd
import csv

# ==============================================================
# (1) AI/ML Keywords
# ==============================================================

AI_ML_TERMS = [
    "machine learning", "deep learning", "data science",
    "künstliche intelligenz", "artificial intelligence",
    "ml", "ai", "ki", "maschinelles lernen", "tiefes lernen",
    "neural network", "natural language processing", "nlp",
    "generative ai", "large language model", "llm", "llms",
    "computer vision"
]
AI_ML_TERMS = sorted(set(AI_ML_TERMS), key=len, reverse=True)

def build_pattern(terms):
    escaped = [re.escape(t) for t in terms]
    return re.compile(r"(?<!\S)(?:" + "|".join(escaped) + r")(?!\S)", re.IGNORECASE)

PATTERN = build_pattern(AI_ML_TERMS)

# ==============================================================
# (2) Split job_text and keep AI/ML relevant parts
# ==============================================================

def extract_relevant_sections(text: str, pattern: re.Pattern) -> str:
    """Split by 'Weniger Mehr' and keep only sections containing AI/ML keywords."""
    if not isinstance(text, str) or not text.strip():
        return "NA"

    chunks = re.split(r"Weniger\s+Mehr", text)
    relevant = []

    for chunk in chunks:
        chunk = chunk.strip()
        if not chunk:
            continue
        if pattern.search(chunk):
            cleaned = re.sub(r"\s+", " ", chunk)
            relevant.append(cleaned)

    if not relevant:
        return "NA"

    # join relevant sections with a pipe separator (keeps CSV single-line)
    return " | ".join(relevant)

# ==============================================================
# (3) Main process
# ==============================================================

def process_csv(input_csv, output_csv):
    try:
        df = pd.read_csv(input_csv)
    except Exception as e:
        print(f"❌ Error reading input CSV: {e}", file=sys.stderr)
        sys.exit(1)

    if "job_text" not in df.columns:
        print("❌ Missing required column 'job_text'", file=sys.stderr)
        sys.exit(1)

    print(f"📦 Loaded {len(df)} rows")

    # Clean and split
    df["job_text"] = df["job_text"].astype(str).apply(lambda x: extract_relevant_sections(x, PATTERN))

    # Replace blanks with NA
    df["job_text"] = df["job_text"].apply(lambda x: x if x.strip() else "NA")

    # Deduplicate
    before = len(df)
    df = df.drop_duplicates(subset=["job_text"], keep="first")
    after = len(df)

    # Save with strict quoting and safe encoding
    try:
        df.to_csv(
            output_csv,
            index=False,
            quoting=csv.QUOTE_ALL,      # quote every cell
            escapechar="\\",             # escape internal quotes
            encoding="utf-8-sig",        # preserve German characters
            lineterminator="\n"          # ✅ correct arg for all pandas versions
        )
    except Exception as e:
        print(f"❌ Error writing output CSV: {e}", file=sys.stderr)
        sys.exit(1)

    na_count = (df["job_text"] == "NA").sum()
    print(f"✅ Cleaned & exported {after}/{before} rows → {output_csv}")
    print(f"   Relevant sections: {after - na_count}, NA: {na_count}")

# ==============================================================
# (4) CLI Entry
# ==============================================================



def main():
    ap = argparse.ArgumentParser(description="Filter job CSV by AI/ML terms in job_text with strict space-bounded matching.")
    input_csv = "/Users/shivangsinha/Downloads/Drive A/Thesis/Master_Thesis/data/jobs_with_ai_ml_tags.csv"
    output_csv = "/Users/shivangsinha/Downloads/Drive A/Thesis/Master_Thesis/data/filtered/jobs_2019_ai_ml_dedup_final.csv"
    
    process_csv(input_csv, output_csv)

if __name__ == "__main__":
    main()
