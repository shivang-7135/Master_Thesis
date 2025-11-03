import csv
import re

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
    ],
    "AI/ML": [
    "deep learning", "data science",
     "tiefes lernen", "neural network", "natural language processing", "nlp",
    "generative ai", "large language model", "llm", "llms", "computer vision","Deep Learning", "NLP"
],
    "AI_KEYWORDS": [
    "künstliche intelligenz", "ki", "machine learning", "ml ", " ml-", " ml/",
    "deep learning", "datenwissenschaft", "data scientist", "data science",
    "nlp", "natural language", "computer vision", "cv ", "cv-",
    "modellierung", "pytorch", "tensorflow", "mlops", "ml-ops",
    "genai", "large language", "llm", "reinforcement learning",
    "dateningenieur", "data engineer", "ai engineer", "ai/ ml", "ai/ml",
    "wissenschaftlicher mitarbeiter ki", "ml engineer", "ml-engineer",
]
    
}

ALL_KEYWORDS = [kw.lower() for group in RAW_KEYWORDS.values() for kw in group]

def find_exact_matches(text, keywords):
    """
    Find exact keyword matches using word boundary regex.
    This handles punctuation, newlines, and various text formats properly.
    """
    text_lower = text.lower()
    matches = []
    
    for keyword in keywords:
        keyword_lower = keyword.lower()
        
        # Create regex pattern with word boundaries
        # \b ensures we match whole words/phrases, not partial matches
        # For multi-word phrases, we need to handle spaces and punctuation
        escaped_keyword = re.escape(keyword_lower)
        
        # Replace escaped spaces with flexible whitespace pattern
        # This handles multiple spaces, tabs, newlines between words
        pattern = escaped_keyword.replace(r'\ ', r'\s+')
        
        # Add word boundaries at start and end
        # \b works for alphanumeric boundaries
        # For phrases starting/ending with non-word chars, use lookahead/lookbehind
        pattern = r'\b' + pattern + r'\b'
        
        # Search for the pattern
        if re.search(pattern, text_lower):
            matches.append(keyword)
    
    # Remove duplicates while preserving order
    seen = set()
    unique_matches = []
    for match in matches:
        if match not in seen:
            seen.add(match)
            unique_matches.append(match)
    
    return unique_matches

def filter_and_tag_jobs(input_csv_path, output_csv_path):
    with open(input_csv_path, encoding='utf-8') as infile, open(output_csv_path, 'w', encoding='utf-8', newline='') as outfile:
        reader = csv.DictReader(infile)
        fieldnames = reader.fieldnames + ["matched_keywords"]
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in reader:
            job_desc = row['job_text']
            
            # Remove special characters from description
            job_desc_cleaned = re.sub(r'[|~`´^°§¶†‡•◦▪▫]', ' ', job_desc)
            # Clean up extra spaces
            job_desc_cleaned = ' '.join(job_desc_cleaned.split())
            
            # Find matches in the cleaned description
            matched_keywords = find_exact_matches(job_desc_cleaned, ALL_KEYWORDS)
            if matched_keywords:
                # row['job_description'] = job_desc_cleaned  # Update with cleaned description
                row['matched_keywords'] = ', '.join(matched_keywords)
                writer.writerow(row)


# Usage:
filter_and_tag_jobs('/Users/shivangsinha/Downloads/Drive A/Thesis/Master_Thesis/datasetConcat2019-25/unified_jobs_dataset-2019-2025.csv', '/Users/shivangsinha/Downloads/Drive A/Thesis/Master_Thesis/datasetConcat2019-25/filtered_unified_jobs_dataset-2019-2025.csv')
