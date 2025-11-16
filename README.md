# Results Folder - Organization Guide

This folder contains all the outputs from the BERT-based skill extraction and analysis pipeline for German AI/ML job postings (2019 vs 2025).

## 📁 Folder Structure

### 1. **tables/** (8 files)
Contains CSV files with analytical tables separated by year (2019 and 2025):

- **Table 2: Geographical Distribution** (2 files)
  - `table2_geographical_distribution_2019.csv` - Job counts by German state for 2019
  - `table2_geographical_distribution_2025.csv` - Job counts by German state for 2025

- **Table 3: Top Categories** (2 files)
  - `table3_top_categories_2019.csv` - Skill category distribution for 2019
  - `table3_top_categories_2025.csv` - Skill category distribution for 2025

- **Table 4: Skills by Category** (2 files)
  - `table4_skills_2019.csv` - Top 5 skills per category for 2019
  - `table4_skills_2025.csv` - Top 5 skills per category for 2025

- **Table 5: Top Individual Skills** (2 files)
  - `table5_top_skills_2019.csv` - Top 30 most demanded skills for 2019
  - `table5_top_skills_2025.csv` - Top 30 most demanded skills for 2025

### 2. **distributions/** (8 files)
Contains distribution CSV files for AI and ML jobs by location:

**AI Job Distributions:**
- `state_distribution_AI_2019.csv` - AI job skill counts by state (2019)
- `state_distribution_AI_2025.csv` - AI job skill counts by state (2025)
- `city_distribution_AI_2019.csv` - AI job skill counts by city (2019)
- `city_distribution_AI_2025.csv` - AI job skill counts by city (2025)

**ML Job Distributions:**
- `state_distribution_ML_2019.csv` - ML job skill counts by state (2019)
- `state_distribution_ML_2025.csv` - ML job skill counts by state (2025)
- `city_distribution_ML_2019.csv` - ML job skill counts by city (2019)
- `city_distribution_ML_2025.csv` - ML job skill counts by city (2025)

### 3. **visualizations/** (16 files)
Contains 8 comparison graphs in both PDF and PNG formats:

**Side-by-Side Comparisons (AI vs ML):**
1. `comparison_states_AI_vs_ML_2019.pdf/png` - Top 10 states comparison for 2019
2. `comparison_states_AI_vs_ML_2025.pdf/png` - Top 10 states comparison for 2025
3. `comparison_cities_AI_vs_ML_2019.pdf/png` - Top 10 cities comparison for 2019
4. `comparison_cities_AI_vs_ML_2025.pdf/png` - Top 10 cities comparison for 2025

**Temporal Comparisons (2019 vs 2025):**
5. `temporal_comparison_AI_states_2019_vs_2025.pdf/png` - AI job state evolution
6. `temporal_comparison_ML_states_2019_vs_2025.pdf/png` - ML job state evolution
7. `temporal_comparison_AI_cities_2019_vs_2025.pdf/png` - AI job city evolution
8. `temporal_comparison_ML_cities_2019_vs_2025.pdf/png` - ML job city evolution

### 4. **raw_data/** (2 files)
Contains the complete skill extraction datasets:

- `skill_extractions_full.csv` - Full skill extraction results from 1,444 job postings
  - Columns: year, city, state, skill, category, subcategory
  - Total records: 14,157 skill mentions

- `skill_extractions_with_domain.csv` - Skill extraction with AI/ML/Both classification
  - Columns: year, city, state, skill, category, subcategory, job_type
  - Job type distribution: 
    - Both AI & ML: 12,759 records
    - ML only: 844 records
    - AI only: 554 records
  - Total records: 14,157 skill mentions

## 📊 Key Statistics

### Dataset Overview
- **Total job postings analyzed**: 1,444
  - 2019: 678 jobs
  - 2025: 753 jobs (July data)
  
- **Total skill extractions**: 14,157 (after removing invalid skills per skillsTable.json)

### Geographic Distribution
**Top 5 States (2019):**
1. Nordrhein-Westfalen - 296 jobs (43.66%)
2. Baden-Württemberg - 103 jobs (15.19%)
3. Bayern - 85 jobs (12.54%)
4. Hessen - 57 jobs (8.41%)
5. Berlin - 53 jobs (7.82%)

**Top 5 States (2025):**
1. Nordrhein-Westfalen - 162 jobs (21.51%)
2. Bayern - 155 jobs (20.58%)
3. Berlin - 141 jobs (18.73%)
4. Baden-Württemberg - 134 jobs (17.80%)
5. Hessen - 55 jobs (7.30%)

### Skill Categories
**Top Categories (2019):**
1. Statistics and Data - 41.17%
2. Decision Making and Analytical - 23.56%
3. Occupational Attributes - 18.38%

**Top Categories (2025):**
1. Decision Making and Analytical - 26.48%
2. Occupational Attributes - 21.74%
3. Statistics and Data - 21.06%

## 🔧 Technical Details

### BERT Model
- **Model**: DistilBertForTokenClassification
- **Task**: Named Entity Recognition (NER) for skill extraction

### Skills Taxonomy
- **Source**: `../dataset/skillsTable.json`
- **Last updated**: November 16, 2024
- **Structure**: Hierarchical taxonomy with categories and subcategories
- **Categories include**: 
  - Statistics and Data
  - Decision Making and Analytical
  - Occupational Attributes
  - Communication
  - Employee Attributes
  - Cloud Platforms
  - Specialized ML
  - Data Engineering
  - MLOps
  - Generative AI
  - General

### Data Processing Pipeline
1. Load job postings from `jobs_ai_ml_with_city_state_filled.csv`
2. Apply BERT NER model to extract skill mentions
3. Validate extracted skills against skillsTable.json taxonomy
4. Map skills to categories and subcategories
5. Classify jobs as AI/ML/Both based on domain keywords
6. Generate aggregated statistics and visualizations

## 📝 Usage Notes

- All CSV files use standard comma separation
- Percentages in tables are rounded to 2 decimal places
- Visualizations use seaborn-v0_8-darkgrid style for consistency
- PDF files are suitable for publication (300 DPI)
- PNG files are optimized for digital viewing (300 DPI)

## 🎯 Next Steps

We can use these results for:
- Thesis analysis
- Identifying skill demand trends between 2019 and 2025
- Geographic concentration analysis of AI/ML jobs in Germany
- Category-level skill evolution tracking

---
**Generated**: November 16, 2024  
**Notebook**: `modeluse.ipynb`  
**Workspace**: Master_Thesis/BERT_analysis
