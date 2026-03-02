import os
from pathlib import Path

# --- CONFIGURATION ---
VAULT_PATH = Path("/Volumes/ObsidianSync/Logs Vault")
INBOX_PATH = VAULT_PATH / "01 - Filer"
TARGET_YEAR = "2026"

# Kinds that follow the "[Kind] Logs" pattern
LOG_KINDS = ["3D Printing", "Creator", "Family", "House", "Overlander", "Personal", "Red Cross", "Stoic", "TimOS"]

def get_nexus_name(kind, year, month=None):
    """Naming convention fix: Removed brackets from Daily Itineraries filename."""
    if kind == "DailyItinerary":
        # Physically named without brackets to resolve your naming issue
        return f"{year}-{month} - Daily Itineraries.md" if month else f"{year} - Daily Itineraries.md"
    
    prefix = f"{year}-{month}" if month else f"{year}"
    return f"{prefix} - {kind} Logs.md"

def generate_nexus_content(kind, year, month=None):
    """Generates content for Yearly or Monthly Nexuses."""
    type_tag = "[Nexus, Log Entry]"
    date_str = f"{year}-{month}-01" if month else f"{year}-01-01"
    
    # Logic for display titles
    display_kind = "Daily Itineraries" if kind == "DailyItinerary" else f"{kind} Logs"
    title = f"{year}-{month} {display_kind}" if month else f"{year} {display_kind}"
    
    # Linking Logic
    links = ""
    if not month:
        links = "## Monthly Indices\n" + "\n".join([f"* [[{get_nexus_name(kind, year, str(m).zfill(2)).replace('.md', '')}]]" for m in range(1, 13)])
    else:
        links = f"## Parent\n* [[{get_nexus_name(kind, year).replace('.md', '')}|{year} Yearly Nexus]]"

    return f"---\ndate_created: {date_str}\ndomain: Personal\ntype: {type_tag}\nkind: {kind}\n---\n# {title}\n\n{links}"

def generate_log_content(kind, year, month):
    """Matches the log template 'part_of' logic."""
    nexus_target = get_nexus_name(kind, year, month).replace('.md', '')
    return f"""---
date_created: {year}-{month}-01
domain: Personal
type: Log Entry
kind: {kind}
part_of: "[[{nexus_target}]]"
SpecialBecause:
---
# {year}-{month} {kind} Log
"""

def create_files():
    print(f"--- Generating {TARGET_YEAR} Files (v2.1) ---")
    INBOX_PATH.mkdir(parents=True, exist_ok=True)
    
    all_types = LOG_KINDS + ["DailyItinerary"]
    
    for kind in all_types:
        # 1. Create Yearly Nexus
        y_name = get_nexus_name(kind, TARGET_YEAR)
        (INBOX_PATH / y_name).write_text(generate_nexus_content(kind, TARGET_YEAR), encoding='utf-8')

        for m in range(1, 13):
            m_str = str(m).zfill(2)
            
            # 2. Create Monthly Nexus
            m_nexus_name = get_nexus_name(kind, TARGET_YEAR, m_str)
            (INBOX_PATH / m_nexus_name).write_text(generate_nexus_content(kind, TARGET_YEAR, m_str), encoding='utf-8')
            
            # 3. Create Monthly Log (Skipped for DailyItinerary)
            if kind != "DailyItinerary":
                log_name = f"{TARGET_YEAR}-{m_str} {kind} Log.md"
                (INBOX_PATH / log_name).write_text(generate_log_content(kind, TARGET_YEAR, m_str), encoding='utf-8')

    print(f"Generation complete. Files created in {INBOX_PATH}")

if __name__ == "__main__":
    create_files()