# scripts/config.py
# Configuration for the voice classification pipeline (Wiley + spaCy).

import os
from dotenv import load_dotenv

load_dotenv()

# ---------- API KEYS ----------
WILEY_TDM_TOKEN = os.getenv("WILEY_TDM_TOKEN")

# ---------- BASE PATHS ----------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JOURNALS_DIR = os.path.join(BASE_DIR, "journals")

# ---------- TARGET JOURNALS ----------
TARGET_JOURNALS = {
    "Cancer": "0008-543X",
    "Clinical_Genetics": "0009-9163",
    "Developmental_Dynamics": "1058-8388",
    "Ecology": "0012-9658",
    "Molecular_Ecology": "0962-1083",
    "Journal_of_Neuroscience_Research": "0360-4012",
    "Molecular_Microbiology": "0950-382X",
}

# ---------- WILEY DOI PREFIXES ----------
WILEY_DOI_PREFIXES = ("10.1002/", "10.1111/")

def is_wiley_doi(doi):
    return doi.startswith(WILEY_DOI_PREFIXES)

# ---------- TARGET YEARS ----------
TARGET_YEARS = [2005, 2010, 2015, 2020, 2025]
PAPERS_PER_YEAR = 40

JOURNAL_YEARS = {
    "Cancer":                            [2005, 2010, 2015, 2020, 2025],
    "Clinical_Genetics":                 [2005, 2010, 2015, 2020, 2025],
    "Developmental_Dynamics":            [2005, 2010, 2015, 2020, 2025],
    "Ecology":                           [2005, 2010, 2015, 2020, 2025],
    "Molecular_Ecology":                 [2005, 2010, 2015, 2020, 2025],
    "Journal_of_Neuroscience_Research":  [2005, 2010, 2015, 2020, 2025],
    "Molecular_Microbiology":            [2005, 2010, 2015, 2020, 2025],
}

# ---------- SUBFOLDER NAMES ----------
RAW_PAPERS_SUBDIR = "raw_papers"
RAW_TEXT_SUBDIR = "raw_text"
SECTIONS_SUBDIR = "sections"
CLEANED_SUBDIR = "cleaned"
SENTENCES_SUBDIR = "sentences"
CLASSIFICATIONS_SUBDIR = "classifications"
SCORES_SUBDIR = "scores"

WHOLE_PAPERS_SUBDIR = "whole_papers"
SENTENCES_WHOLE_SUBDIR = "sentences_whole"
CLASSIFICATIONS_WHOLE_SUBDIR = "classifications_whole"
SCORES_WHOLE_SUBDIR = "scores_whole"

# ---------- PIPELINE SETTINGS ----------
MIN_SENTENCE_WORDS = 5
TARGET_SECTIONS = ["introduction", "methods", "results", "discussion"]


def journal_path(journal, subdir=None):
    base = os.path.join(JOURNALS_DIR, journal)
    if subdir:
        return os.path.join(base, subdir)
    return base


def ensure_journal_folders(journal):
    for sub in [
        RAW_PAPERS_SUBDIR, RAW_TEXT_SUBDIR, SECTIONS_SUBDIR,
        CLEANED_SUBDIR, SENTENCES_SUBDIR, CLASSIFICATIONS_SUBDIR, SCORES_SUBDIR,
        WHOLE_PAPERS_SUBDIR, SENTENCES_WHOLE_SUBDIR,
        CLASSIFICATIONS_WHOLE_SUBDIR, SCORES_WHOLE_SUBDIR,
    ]:
        os.makedirs(journal_path(journal, sub), exist_ok=True)


for j in TARGET_JOURNALS:
    ensure_journal_folders(j)
