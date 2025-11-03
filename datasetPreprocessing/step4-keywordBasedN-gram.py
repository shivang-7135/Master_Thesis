"""
skill_extraction_combined.py
----------------------------
Verma et al.–style keyword-based skill extraction using n-gram analysis.
Handles combined dataset for multiple years (e.g., 2019 + 2025)
and supports AI vs ML domain comparison.
"""

import re, string, os, nltk, pandas as pd
from nltk.corpus import stopwords
from nltk.util import ngrams
from collections import Counter

nltk.download('punkt')
nltk.download('stopwords')

STOPWORDS = set(stopwords.words('english')) | set(stopwords.words('german'))

# ---------------------------------
# 1️⃣ TEXT CLEANING + N-GRAM HELPERS
# ---------------------------------
def clean_text(text):
    text = str(text).lower()
    text = re.sub(rf"[{re.escape(string.punctuation)}]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

def tokenize(text):
    return [w for w in nltk.word_tokenize(clean_text(text))
            if w not in STOPWORDS and len(w) > 1]

def make_ngrams(tokens):
    unigrams = tokens
    bigrams  = [" ".join(b) for b in ngrams(tokens, 2)]
    trigrams = [" ".join(t) for t in ngrams(tokens, 3)]
    return unigrams + bigrams + trigrams

# ---------------------------------
# 2️ SKILL DICTIONARY (based on Verma et al.)
# ---------------------------------
skill_dict = {
    # ---------------- COMMUNICATION ----------------
    "Communication_Written": [
        "copywriting","editing","blogging","content creation","story ideation",
        "textverfassung","korrekturlesen","bloggen","inhalts­erstellung","geschichtsideen"
    ],
    "Communication_Verbal": [
        "verbal","oral","cold calling",
        "mündlich","telefonakquise","telefonverkauf","kundenanruf"
    ],
    "Communication_Presentation": [
        "presentation","present","report",
        "präsentation","vortrag","bericht","reporting"
    ],
    "Communication_Generic": [
        "responsible","determined","competitive","witty","success oriented",
        "verantwortlich","entschlossen","wettbewerbsfähig","witzig","erfolgsorientiert"
    ],

    # ---------------- EMPLOYEE ATTRIBUTES ----------------
    "Employee_Motivation": [
        "motivated","ambition","willingness to learn","delivering result","continuous learning",
        "motiviert","ehrgeiz","lernbereitschaft","ergebnisorientiert","kontinuierliches lernen"
    ],
    "Employee_TimeManagement": [
        "time management","timely manner","prioritize time","deadline driven",
        "zeitmanagement","fristgerecht","zeitpriorisierung","termintreu"
    ],
    "Employee_DetailOriented": [
        "attention to detail","eye for detail","accuracy","precision",
        "detailgenauigkeit","präzision","sorgfalt","genauigkeit"
    ],
    "Employee_Attitude": [
        "can do","go getter","self learner","self directed","positive attitude",
        "anpackend","zielstrebig","selbstlerner","eigenverantwortlich","positive einstellung"
    ],
    "Employee_Independence": [
        "independent","without supervision","autonomous",
        "unabhängig","eigenständig","selbstständig","ohne aufsicht"
    ],
    "Employee_Adaptability": [
        "adaptable","flexible","multitasking",
        "anpassungsfähig","flexibel","multitasking","vielseitig"
    ],
    "Employee_Confidence": [
        "confident","decisive",
        "selbstbewusst","entscheidungsfreudig"
    ],
    "Employee_Other": [
        "funny","smiling","high energy","reliable","proactive",
        "lustig","lächelnd","energiegeladen","zuverlässig","proaktiv"
    ],

    # ---------------- OCCUPATIONAL ATTRIBUTES ----------------
    "Occupational_EnterpriseSystem": [
        "erp","crm","scm","sap","peoplesoft","oracle","integration","saas",
        "unternehmenssoftware","crm system","sap system","oracle datenbank","integration","saas lösung"
    ],
    "Occupational_Visualization": [
        "visualization","tableau","lumira","crystal reports","d3","d3.js",
        "datenvisualisierung","tableau","powerbi","berichte","diagramme"
    ],
    "Occupational_Programming": [
        "mathematical programming","scala","python","c#","c++","vb","excel macros",
        "perl","c","java","visual basic","vb.net","vba","cobol","fortran","s","splus","bash","javascript","asp.net","jquery","jboss",
        "programmierung","python","java","scala","c plus plus","javascript","programmieren","bash","skripting"
    ],
    "Occupational_ProjectManagement": [
        "project management","pert","cpm","change management","project budget",
        "project documentation","pmp","microsoft project","gantt chart",
        "projektmanagement","projektplanung","änderungsmanagement","projektbudget","projekt­dokumentation","pmp zertifizierung","projektplan","gantt diagramm"
    ],
    "Occupational_Modeling": [
        "neural networks","linear programming","integer programming","goal programming",
        "queuing","genetic algorithms","expert systems",
        "neuronale netze","lineare programmierung","ganzzahlprogrammierung",
        "zielprogrammierung","warteschlangen","genetische algorithmen","experten­systeme"
    ],
    "Occupational_Scraping": [
        "scraping","web scraping","crawling","web crawling",
        "datenextraktion","web scraping","daten crawling","web crawler"
    ],
    "Occupational_Hardware": [
        "hardware","architecture","devices","printer","storage","desktop","pc","server","workstation","mainframe","legacy","system architecture",
        "hardware","architektur","geräte","drucker","speicher","server","arbeitsstation","hauptrechner","systemarchitektur"
    ],
    "Occupational_Networks": [
        "internet","lan","wan","networking","cloud computing","client server",
        "distributed computing","network security","ubiquitous computing","tcp/ip",
        "netzwerk","netzwerke","lan","wan","cloud computing","client server","verteiltes rechnen","netzwerksicherheit","tcp ip"
    ],

    # ---------------- STATISTICS / DATA ----------------
    "Statistics": [
        "statistics","spss","sas","excel","stata","matlab","probability","hypothesis testing",
        "regression","pandas","scipy","scikits learn","splunk","h2o","r","statistical programming",
        "statistik","wahrscheinlichkeit","hypothesentest","regression","datenanalyse","r","matlab","python pandas","statistische programmierung"
    ],
    "DataMining": [
        "classification","text mining","web mining","stream mining","knowledge discovery",
        "anomaly detection","associations","outlier","classify","association","estimation",
        "prediction","forecasting","machine learning","decision trees",
        "datenanalyse","text mining","web mining","strom daten","wissensentdeckung",
        "anomalieerkennung","assoziationen","ausreißer","vorhersage","prognose","maschinelles lernen","entscheidungsbäume"
    ],
    "StructuredData": [
        "sql","relational database","oracle","sql server","db2","microsoft access","data model",
        "data management","entity relationship","data warehouse","dbms","transactional database",
        "cassandra","mongodb","mysql","postgresql",
        "sql","relationale datenbank","oracle datenbank","mysql","postgresql","datenmanagement","datenmodell","data warehouse","dbms"
    ],
    "BigData": [
        "big data","unstructured data","data variety","data velocity","data volume",
        "hadoop","hive","pig","spark","mapreduce","presto","mahout","nosql","oozie","zookeeper","flume",
        "big data","unstrukturierte daten","datenvielfalt","datenvolumen","hadoop","spark","mapreduce","nosql","datenströme","datenplattform"
    ],

    # ---------------- DECISION MAKING & ANALYTICAL ----------------
    "DecisionMaking": [
        "reporting","analysis","modeling","design","problem solving","implementation",
        "testing","analytical","strategic thinking",
        "analyse","modellierung","design","problemlösung","implementierung","testen","analytisch","strategisches denken"
    ],
    "MSOffice": [
        "ms office","powerpoint","word","communication","documentation",
        "microsoft office","powerpoint","word","excel","office suite","kommunikation","dokumentation"
    ],
    "Interpersonal": [
        "interpersonal","team management","collaboration","cooperation","networking","client relationship",
        "zwischenmenschlich","teamführung","zusammenarbeit","kooperation","netzwerkpflege","kundenbeziehung"
    ],
    "ProblemSolving": [
        "problem solving","troubleshoot","conflict resolution","solve issue","critical thinker",
        "problemlösung","störungsbehebung","konfliktlösung","kritisches denken"
    ],
    "Creativity": [
        "creative","out of box","storyteller",
        "kreativ","innovativ","geschichtenerzähler","ideenreich"
    ],
    "ProcessDesign": [
        "design process","improve process","continuous improvement","operations management",
        "prozessdesign","prozessverbesserung","kontinuierliche verbesserung","betriebsführung"
    ],
    "Administrative": [
        "issue management","posting schedule","product launch","social calendar",
        "administrativ","terminplanung","produktstart","social media kalender"
    ],
    "Analytical": [
        "insight","identify trend","summarize finding","analyze trend","synthesize information",
        "draw conclusion","propose solution","google analytics","arcgis","gis","qgis",
        "data analytics","business analytics",
        "analytisch","trend erkennen","schlussfolgerung ziehen","lösung vorschlagen","datenanalyse","geschäftsanalyse","google analytics","gis","qgis"
    ],
    "Research": [
        "data gathering","data collection","data reporting","monitor trend","monitor performance",
        "recherche","datenerhebung","datenanalyse","leistung überwachen","trendanalyse"
    ],
    "Numeracy": [
        "numeracy","financial management","bookkeeping","accountancy",
        "mathematik","finanzverwaltung","buchhaltung","rechnungswesen"
    ],
    "ForeignLanguage": [
        "foreign language","spanish","french","german","italian","chinese",
        "fremdsprache","spanisch","französisch","deutsch","italienisch","chinesisch","englisch"
    ]
}


# ---------------------------------
# 3️ MATCH SKILLS FUNCTION
# ---------------------------------
def match_skills(text, skill_dict):
    tokens = tokenize(text)
    ngrams_all = make_ngrams(tokens)
    found = []
    for cat, keywords in skill_dict.items():
        for kw in keywords:
            if kw in ngrams_all:
                found.append((cat, kw))
    return found

# ---------------------------------
# 4️ PROCESS COMBINED DATASET
# ---------------------------------
def extract_skills_combined(input_file):
    df = pd.read_csv(input_file)
    if "year" not in df.columns:
        raise ValueError("❌ Dataset must contain a 'year' column (e.g., 2019 or 2025).")

    if "job_text" not in df.columns:
        raise ValueError("❌ Dataset must contain a 'job_text' column.")

    print(f"📘 Loaded combined dataset: {len(df)} records across years {df['year'].unique().tolist()}")

    results = []
    for i, row in df.iterrows():
        text = str(row.get("job_text", ""))
        matches = match_skills(text, skill_dict)
        skills = sorted(set([k for _, k in matches]))
        cats   = sorted(set([c for c, _ in matches]))
        df.loc[i, "skills_found"] = ", ".join(skills)
        df.loc[i, "skill_categories"] = ", ".join(cats)
        results.extend([(row["year"], row.get("job_domain_keywords", ""), c, k) for c, k in matches])

    # Save enriched dataset
    os.makedirs("/Users/shivangsinha/Downloads/Drive A/Thesis/Master_Thesis/datasetConcat2019-25/data/processed", exist_ok=True)
    df.to_csv("/Users/shivangsinha/Downloads/Drive A/Thesis/Master_Thesis/datasetConcat2019-25/data/processed/jobs_with_skills_combined.csv", index=False)
    print("✅ Added 'skills_found' and 'skill_categories' columns.")

    # Create skill frequency tables per year & domain (AI/ML)
    recs = pd.DataFrame(results, columns=["year","domain_raw","category","skill"])
    recs["domain"] = recs["domain_raw"].apply(
        lambda x: "AI" if re.search(r"artificial", str(x), re.I)
        else ("ML" if re.search(r"machine", str(x), re.I) else "Other")
    )

    summary = (
        recs.groupby(["year","domain","category","skill"])
            .size()
            .reset_index(name="count")
    )
    summary["percentage"] = (
        summary.groupby(["year","domain"])["count"]
        .apply(lambda x: round(x / x.sum() * 100, 2))
        .reset_index(drop=True)
    )

    summary.to_csv("/Users/shivangsinha/Downloads/Drive A/Thesis/Master_Thesis/datasetConcat2019-25/data/processed/skill_summary_by_year_domain.csv", index=False)
    print("📊 Saved skill_summary_by_year_domain.csv")

    return df, summary


df, summary = extract_skills_combined("/Users/shivangsinha/Downloads/Drive A/Thesis/Master_Thesis/datasetConcat2019-25/jobs_ai_ml_with_city_state_filled.csv")


trend = summary.groupby(["year","skill"])["count"].sum().unstack(fill_value=0)
trend["growth_%"] = ((trend.loc[2025] - trend.loc[2019]) / trend.loc[2019] * 100).round(2)
print(trend.sort_values("growth_%", ascending=False).head(10))

ai_ml_comp = (
    summary.groupby(["year","domain","category"])["count"]
    .sum()
    .reset_index()
    .pivot(index=["category"], columns=["domain","year"], values="count")
    .fillna(0)
)
print(ai_ml_comp)
