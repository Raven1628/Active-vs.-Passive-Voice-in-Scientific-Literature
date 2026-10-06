# scripts/colors.py
# Canonical color scheme for all figures.

JOURNAL_COLORS = {
    "Cancer":                           "#2a7eb8",   # blue
    "Clinical_Genetics":                "#e07b39",   # orange
    "Developmental_Dynamics":           "#8e44ad",   # purple
    "Ecology":                          "#27ae60",   # green
    "Journal_of_Neuroscience_Research": "#c0392b",   # red
    "Molecular_Ecology":                "#e91e8c",   # pink
    "Molecular_Microbiology":           "#00bcd4",   # cyan
}

# Overall accent colors — both black now
COLOR_ACTIVE  = "black"
COLOR_PASSIVE = "black"
COLOR_OVERALL = "black"

def journal_color(journal):
    return JOURNAL_COLORS.get(journal, "#333333")

def journal_short(journal):
    return journal.replace("_", " ")
