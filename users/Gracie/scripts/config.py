# config.py — reads config.yaml and exposes names for pipeline scripts.
# Replaces the old hardcoded Wiley config.

import os
import yaml

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
USER_DIR = os.path.dirname(SCRIPT_DIR)
CONFIG_PATH = os.path.join(USER_DIR, "config.yaml")
JOURNALS_DIR = os.path.join(USER_DIR, "journals")

if not os.path.exists(CONFIG_PATH):
    raise SystemExit(f"Missing config.yaml at {CONFIG_PATH}")

with open(CONFIG_PATH) as f:
    _cfg = yaml.safe_load(f)

# Journal names — normalized to underscore form for filesystem paths
_raw_journals = _cfg.get("journals", [])
TARGET_JOURNALS = {}
for entry in _raw_journals:
    name = entry.get("name", "").strip()
    if not name:
        continue
    key = name.replace(" ", "_").replace("/", "_")
    TARGET_JOURNALS[key] = entry.get("issn", "")

# Years and per-year target
TARGET_YEARS = _cfg.get("years", [2005, 2010, 2015, 2020, 2025])
PAPERS_PER_YEAR = _cfg.get("papers_per_year", 40)

# Per-journal years — default to global if not specified
JOURNAL_YEARS = {j: TARGET_YEARS for j in TARGET_JOURNALS}

# Subdirectory names (standard across all students)
RAW_PAPERS_SUBDIR = "raw_papers"
RAW_TEXT_SUBDIR = "raw_text"
SECTIONS_SUBDIR = "sections"
CLEANED_SUBDIR = "cleaned"
SENTENCES_SUBDIR = "sentences"
CLASSIFICATIONS_SUBDIR = "classifications"
SCORES_SUBDIR = "scores"

# NLP settings
_nlp_cfg = _cfg.get("nlp", {})
SPACY_MODEL = _nlp_cfg.get("spacy_model", "en_core_web_sm")
MIN_SENTENCE_WORDS = int(_nlp_cfg.get("min_sentence_words", 5))
TARGET_SECTIONS = _nlp_cfg.get(
    "target_sections", ["introduction", "methods", "results", "discussion"]
)

# Helpers used by the pipeline scripts
def journal_path(journal, subdir=None):
    base = os.path.join(JOURNALS_DIR, journal)
    if subdir:
        return os.path.join(base, subdir)
    return base


def ensure_journal_folders(journal):
    for sub in [
        RAW_PAPERS_SUBDIR, RAW_TEXT_SUBDIR, SECTIONS_SUBDIR,
        CLEANED_SUBDIR, SENTENCES_SUBDIR, CLASSIFICATIONS_SUBDIR, SCORES_SUBDIR,
    ]:
        os.makedirs(journal_path(journal, sub), exist_ok=True)


# Wiley check — kept for compatibility but always False for MDPI
WILEY_DOI_PREFIXES = ("10.1002/", "10.1111/")

def is_wiley_doi(doi):
    return doi.startswith(WILEY_DOI_PREFIXES)


# Create folders for every journal listed in config.yaml
for j in TARGET_JOURNALS:
    ensure_journal_folders(j)
