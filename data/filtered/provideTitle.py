import re
import pandas as pd

# Pattern to detect variations of gender-inclusive job markers
TITLE_PATTERN = re.compile(
    r"^.*?\([^)]*(?:m|w|d|f|x|M|W|D|F|X)[^)]*\)",  # capture until closing parenthesis
    flags=re.IGNORECASE
)

def extract_clean_job_title(text: str) -> str:
    """
    Extract the main job title containing the gender marker (m/w/d, f/m/x, etc.)
    from a longer text line. 
    """
    if not isinstance(text, str) or not text.strip():
        return ""

    # Pick only the first line if multiple are present
    first_line = text.strip().split("|")[0].strip()

    # Try to extract up to (m/w/d) or variants
    match = TITLE_PATTERN.search(first_line)
    if match:
        title = match.group(0)
        # Remove trailing connectors or location/company names
        title = re.sub(r"\b(at|bei|in|for|mit)\b.*", "", title, flags=re.IGNORECASE).strip()
        return title

    # Fallback — try to take up to 6 words before company/location hints
    fallback = re.split(r"\b(at|bei|in|mit|for)\b", first_line)[0]
    return fallback.strip()

# Example integration
df = pd.read_csv("/Users/shivangsinha/Downloads/Drive A/Thesis/Master_Thesis/data/filtered/jobs_2019_ai_ml_dedup_final.csv")

df["extracted_title"] = df["job_text"].apply(extract_clean_job_title)

df.to_csv("/Users/shivangsinha/Downloads/Drive A/Thesis/Master_Thesis/data/filtered/jobs_2019_with_titles.csv", index=False, encoding="utf-8-sig", quoting=1)
