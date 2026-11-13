# config.py - OUP version. Reads config.yaml dynamically.
import os
import yaml

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
USER_DIR = os.path.dirname(SCRIPT_DIR)
CONFIG_PATH = os.path.join(USER_DIR, "config.yaml")

if not os.path.exists(CONFIG_PATH):
    raise SystemExit(f"Missing config.yaml at {CONFIG_PATH}")

with open(CONFIG_PATH) as f:
    _cfg = yaml.safe_load(f)

TARGET_JOURNALS = {}
for entry in _cfg.get("journals", []):
    name = entry.get("name", "").strip()
    if not name:
        continue
    key = name.replace(" ", "_").replace("/", "_")
    TARGET_JOURNALS[key] = entry.get("issn", "")

TARGET_YEARS = _cfg.get("years", [2005, 2010, 2015, 2020, 2025])
PAPERS_PER_YEAR = _cfg.get("papers_per_year", 40)
JOURNAL_YEARS = {j: TARGET_YEARS for j in TARGET_JOURNALS}

RAW_PAPERS_SUBDIR = "raw_papers"
RAW_TEXT_SUBDIR = "raw_text"
SECTIONS_SUBDIR = "sections"
CLEANED_SUBDIR = "cleaned"
SENTENCES_SUBDIR = "sentences"
CLASSIFICATIONS_SUBDIR = "classifications"
SCORES_SUBDIR = "scores"

# Whole-paper pipeline subdirs
WHOLE_PAPERS_SUBDIR = "whole_papers"
SEGMENTS_WHOLE_SUBDIR = "segments_whole"
SENTENCES_WHOLE_SUBDIR = "sentences_whole"
CLASSIFICATIONS_WHOLE_SUBDIR = "classifications_whole"
SCORES_WHOLE_SUBDIR = "scores_whole"

_nlp_cfg = _cfg.get("nlp", {})
SPACY_MODEL = _nlp_cfg.get("spacy_model", "en_core_web_sm")
MIN_SENTENCE_WORDS = int(_nlp_cfg.get("min_sentence_words", 5))
TARGET_SECTIONS = _nlp_cfg.get("target_sections",
    ["introduction", "methods", "results", "discussion"])

JOURNALS_DIR = os.path.join(USER_DIR, "journals")

def journal_path(journal, subdir=None):
    base = os.path.join(JOURNALS_DIR, journal)
    if subdir:
        return os.path.join(base, subdir)
    return base

def ensure_journal_folders(journal):
    for sub in [RAW_PAPERS_SUBDIR, RAW_TEXT_SUBDIR, SECTIONS_SUBDIR,
                CLEANED_SUBDIR, SENTENCES_SUBDIR,
                CLASSIFICATIONS_SUBDIR, SCORES_SUBDIR,
                WHOLE_PAPERS_SUBDIR, SEGMENTS_WHOLE_SUBDIR,
                SENTENCES_WHOLE_SUBDIR,
                CLASSIFICATIONS_WHOLE_SUBDIR, SCORES_WHOLE_SUBDIR]:
        os.makedirs(journal_path(journal, sub), exist_ok=True)

DOI_PREFIXES = ("10.3389/",)

def is_target_doi(doi):
    if not DOI_PREFIXES:
        return True
    return doi.startswith(DOI_PREFIXES)

for j in TARGET_JOURNALS:
    ensure_journal_folders(j)
